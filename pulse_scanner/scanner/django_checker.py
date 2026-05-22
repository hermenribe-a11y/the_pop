import ast
import sys
from typing import List, Dict

def check_django_settings(settings_path: str) -> List[Dict]:
    """Analisa settings.py e retorna lista de checks de segurança."""
    checks = []
    
    try:
        with open(settings_path, 'r') as f:
            source = f.read()
        tree = ast.parse(source)
    except Exception as e:
        return [{'check': 'Ler arquivo', 'status': 'FAIL', 'severity': 'CRITICAL', 
                 'descricao': f'Não foi possível ler o arquivo: {str(e)}', 'correcao': 'Verifique o caminho e permissões do arquivo.'}]
    
    # Coletar assignments
    assigns = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    if isinstance(node.value, ast.Constant):
                        assigns[target.id] = node.value.value
                    elif isinstance(node.value, ast.List):
                        assigns[target.id] = [el.s if isinstance(el, ast.Constant) else '*' for el in node.value.elts]
                    elif isinstance(node.value, ast.Dict):
                        assigns[target.id] = 'dict'
                    elif isinstance(node.value, ast.NameConstant):
                        assigns[target.id] = node.value.value
                    elif isinstance(node.value, ast.Name):
                        assigns[target.id] = node.value.id
                    elif isinstance(node.value, ast.Tuple):
                        assigns[target.id] = [el.s if isinstance(el, ast.Constant) else '*' for el in node.value.elts]
    
    # DEBUG
    debug_val = assigns.get('DEBUG', None)
    if debug_val is True:
        checks.append({'check': 'DEBUG = False', 'status': 'FAIL', 'severity': 'CRITICAL',
                       'descricao': 'DEBUG está ativado (True). Em produção, isso expõe informações sensíveis.',
                       'correcao': 'Defina DEBUG = False no settings.py de produção.'})
    else:
        checks.append({'check': 'DEBUG = False', 'status': 'PASS', 'severity': 'CRITICAL',
                       'descricao': 'DEBUG está desativado.', 'correcao': ''})
    
    # SECRET_KEY
    sk = assigns.get('SECRET_KEY', '')
    if isinstance(sk, str) and 'django-insecure-' in sk:
        checks.append({'check': 'SECRET_KEY segura', 'status': 'WARN', 'severity': 'HIGH',
                       'descricao': 'SECRET_KEY contém o prefixo padrão "django-insecure-". Pode ser vulnerável.',
                       'correcao': 'Gere uma nova SECRET_KEY com: python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"'})
    else:
        checks.append({'check': 'SECRET_KEY segura', 'status': 'PASS', 'severity': 'HIGH',
                       'descricao': 'SECRET_KEY parece personalizada.', 'correcao': ''})
    
    # ALLOWED_HOSTS
    ah = assigns.get('ALLOWED_HOSTS', [])
    if isinstance(ah, list) and '*' in ah:
        checks.append({'check': 'ALLOWED_HOSTS seguro', 'status': 'FAIL', 'severity': 'CRITICAL',
                       'descricao': 'ALLOWED_HOSTS contém "*" (aceita qualquer host). Risco de host header injection.',
                       'correcao': 'Remova "*" e adicione apenas os domínios reais: ALLOWED_HOSTS = ["seusite.com", "www.seusite.com"]'})
    else:
        checks.append({'check': 'ALLOWED_HOSTS seguro', 'status': 'PASS', 'severity': 'CRITICAL',
                       'descricao': 'ALLOWED_HOSTS não contém "*".', 'correcao': ''})
    
    # LANGUAGE_CODE e TIME_ZONE
    if assigns.get('LANGUAGE_CODE', '') in ['', 'en-us']:
        checks.append({'check': 'LANGUAGE_CODE configurado', 'status': 'WARN', 'severity': 'LOW',
                       'descricao': 'LANGUAGE_CODE não foi personalizado (padrão en-us).',
                       'correcao': 'Configure LANGUAGE_CODE = "pt-br" para português de Moçambique.'})
    else:
        checks.append({'check': 'LANGUAGE_CODE configurado', 'status': 'PASS', 'severity': 'LOW',
                       'descricao': f'LANGUAGE_CODE = {assigns.get("LANGUAGE_CODE", "")}', 'correcao': ''})
    
    if assigns.get('TIME_ZONE', '') in ['', 'UTC']:
        checks.append({'check': 'TIME_ZONE configurado', 'status': 'WARN', 'severity': 'LOW',
                       'descricao': 'TIME_ZONE não foi personalizado (padrão UTC).',
                       'correcao': 'Configure TIME_ZONE = "Africa/Maputo" para Moçambique.'})
    else:
        checks.append({'check': 'TIME_ZONE configurado', 'status': 'PASS', 'severity': 'LOW',
                       'descricao': f'TIME_ZONE = {assigns.get("TIME_ZONE", "")}', 'correcao': ''})
    
    # USE_TZ
    if assigns.get('USE_TZ', None) is True:
        checks.append({'check': 'USE_TZ ativado', 'status': 'PASS', 'severity': 'LOW',
                       'descricao': 'USE_TZ = True — fusos horários ativos.', 'correcao': ''})
    else:
        checks.append({'check': 'USE_TZ ativado', 'status': 'WARN', 'severity': 'LOW',
                       'descricao': 'USE_TZ não está ativo.', 'correcao': 'Defina USE_TZ = True para evitar problemas com datas.'})
    
    # SESSION_COOKIE_HTTPONLY
    if assigns.get('SESSION_COOKIE_HTTPONLY', None) is True:
        checks.append({'check': 'SESSION_COOKIE_HTTPONLY', 'status': 'PASS', 'severity': 'MEDIUM',
                       'descricao': 'Cookies de sessão com HttpOnly ativado.', 'correcao': ''})
    else:
        checks.append({'check': 'SESSION_COOKIE_HTTPONLY', 'status': 'WARN', 'severity': 'MEDIUM',
                       'descricao': 'SESSION_COOKIE_HTTPONLY não configurado explicitamente.',
                       'correcao': 'Adicione SESSION_COOKIE_HTTPONLY = True'})
    
    # CSRF_COOKIE_HTTPONLY
    if assigns.get('CSRF_COOKIE_HTTPONLY', None) is True:
        checks.append({'check': 'CSRF_COOKIE_HTTPONLY', 'status': 'PASS', 'severity': 'MEDIUM',
                       'descricao': 'CSRF cookie com HttpOnly ativado.', 'correcao': ''})
    else:
        checks.append({'check': 'CSRF_COOKIE_HTTPONLY', 'status': 'WARN', 'severity': 'MEDIUM',
                       'descricao': 'CSRF_COOKIE_HTTPONLY não configurado explicitamente.',
                       'correcao': 'Adicione CSRF_COOKIE_HTTPONLY = True'})
    
    # X_FRAME_OPTIONS
    xfo = assigns.get('X_FRAME_OPTIONS', '').upper() if isinstance(assigns.get('X_FRAME_OPTIONS', ''), str) else ''
    if xfo in ['DENY', 'SAMEORIGIN']:
        checks.append({'check': 'X_FRAME_OPTIONS', 'status': 'PASS', 'severity': 'MEDIUM',
                       'descricao': f'X_FRAME_OPTIONS = {xfo} — proteção contra clickjacking ativa.', 'correcao': ''})
    else:
        checks.append({'check': 'X_FRAME_OPTIONS', 'status': 'WARN', 'severity': 'MEDIUM',
                       'descricao': 'X_FRAME_OPTIONS não configurado ou inválido.',
                       'correcao': 'Adicione X_FRAME_OPTIONS = "DENY"'})
    
    # SECURE_BROWSER_XSS_FILTER
    if assigns.get('SECURE_BROWSER_XSS_FILTER', None) is True:
        checks.append({'check': 'SECURE_BROWSER_XSS_FILTER', 'status': 'PASS', 'severity': 'MEDIUM',
                       'descricao': 'XSS filter ativado.', 'correcao': ''})
    else:
        checks.append({'check': 'SECURE_BROWSER_XSS_FILTER', 'status': 'WARN', 'severity': 'MEDIUM',
                       'descricao': 'SECURE_BROWSER_XSS_FILTER não configurado.',
                       'correcao': 'Adicione SECURE_BROWSER_XSS_FILTER = True'})
    
    # SECURE_CONTENT_TYPE_NOSNIFF
    if assigns.get('SECURE_CONTENT_TYPE_NOSNIFF', None) is True:
        checks.append({'check': 'SECURE_CONTENT_TYPE_NOSNIFF', 'status': 'PASS', 'severity': 'MEDIUM',
                       'descricao': 'Proteção MIME sniffing ativa.', 'correcao': ''})
    else:
        checks.append({'check': 'SECURE_CONTENT_TYPE_NOSNIFF', 'status': 'WARN', 'severity': 'MEDIUM',
                       'descricao': 'SECURE_CONTENT_TYPE_NOSNIFF não configurado.',
                       'correcao': 'Adicione SECURE_CONTENT_TYPE_NOSNIFF = True'})
    
    # DEFAULT_AUTO_FIELD
    if assigns.get('DEFAULT_AUTO_FIELD', '') != '':
        checks.append({'check': 'DEFAULT_AUTO_FIELD', 'status': 'PASS', 'severity': 'LOW',
                       'descricao': f'DEFAULT_AUTO_FIELD = {assigns.get("DEFAULT_AUTO_FIELD")}', 'correcao': ''})
    else:
        checks.append({'check': 'DEFAULT_AUTO_FIELD', 'status': 'WARN', 'severity': 'LOW',
                       'descricao': 'DEFAULT_AUTO_FIELD não definido.',
                       'correcao': 'Adicione DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"'})
    
    return checks

if __name__ == '__main__':
    import json
    from rich.console import Console
    from rich.table import Table
    
    if len(sys.argv) < 2:
        print("Uso: python django_checker.py <caminho_para_settings.py>")
        sys.exit(1)
    
    results = check_django_settings(sys.argv[1])
    
    console = Console()
    table = Table(title="Resultados da Verificação Django")
    table.add_column("Check", style="cyan")
    table.add_column("Status", style="bold")
    table.add_column("Severidade")
    table.add_column("Descrição")
    
    for r in results:
        status_style = "green" if r['status'] == 'PASS' else "red" if r['status'] == 'FAIL' else "yellow"
        table.add_row(r['check'], f"[{status_style}]{r['status']}[/]", r['severity'], r['descricao'])
    
    console.print(table)
