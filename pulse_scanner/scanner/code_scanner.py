import subprocess
import os
import json
from typing import Dict, List

def scan_code(source_path: str) -> Dict:
    """Analisa código fonte com bandit em busca de vulnerabilidades."""
    result = {
        'total_issues': 0,
        'por_severidade': {'HIGH': 0, 'MEDIUM': 0, 'LOW': 0},
        'issues': [],
        'erro': None
    }
    
    if not os.path.isdir(source_path):
        result['erro'] = f'Caminho não encontrado: {source_path}'
        return result
    
    try:
        # Tenta executar bandit
        proc = subprocess.run(
            ['bandit', '-r', source_path, '-f', 'json', '--quiet'],
            capture_output=True, text=True, timeout=60
        )
        
        if proc.returncode == 0 or proc.returncode == 1:  # 1 = vulnerabilidades encontradas
            try:
                data = json.loads(proc.stdout) if proc.stdout else json.loads(proc.stderr)
                for issue in data.get('results', []):
                    result['issues'].append({
                        'filename': issue.get('filename', ''),
                        'line_number': issue.get('line_number', 0),
                        'test_id': issue.get('test_id', ''),
                        'issue_text': issue.get('issue_text', ''),
                        'severity': issue.get('issue_severity', 'LOW'),
                        'confidence': issue.get('issue_confidence', 'LOW'),
                    })
                    sev = issue.get('issue_severity', 'LOW')
                    result['por_severidade'][sev] = result['por_severidade'].get(sev, 0) + 1
                
                result['total_issues'] = len(result['issues'])
            except json.JSONDecodeError:
                result['erro'] = 'Erro ao parsear saída do bandit'
        else:
            result['erro'] = f'Bandit retornou código {proc.returncode}: {proc.stderr[:200]}'
    
    except FileNotFoundError:
        # Bandit não instalado, faz análise básica manual
        result['erro'] = 'Bandit não encontrado. Executando análise básica manual...'
        result['issues'] = _manual_scan(source_path)
        result['total_issues'] = len(result['issues'])
        for iss in result['issues']:
            result['por_severidade'][iss['severity']] = result['por_severidade'].get(iss['severity'], 0) + 1
    
    except subprocess.TimeoutExpired:
        result['erro'] = 'Bandit excedeu o tempo limite (60s)'
    
    return result


def _manual_scan(source_path: str) -> List[Dict]:
    """Análise manual básica quando bandit não está disponível."""
    issues = []
    patterns = {
        'eval()': {'severity': 'HIGH', 'message': 'Uso de eval() detectado. Risco de execução de código arbitrário.'},
        'exec()': {'severity': 'HIGH', 'message': 'Uso de exec() detectado. Risco de execução de código arbitrário.'},
        'pickle.loads': {'severity': 'HIGH', 'message': 'Uso de pickle.loads(). Risco de desserialização insegura.'},
        'os.system': {'severity': 'MEDIUM', 'message': 'Uso de os.system(). Prefira subprocess com shell=False.'},
        'subprocess.call': {'severity': 'MEDIUM', 'message': 'Uso de subprocess.call(). Verifique se shell=False.'},
        'subprocess.Popen': {'severity': 'MEDIUM', 'message': 'Uso de subprocess.Popen(). Verifique se shell=False.'},
        'mark_safe': {'severity': 'MEDIUM', 'message': 'Uso de mark_safe(). Pode permitir XSS se usado com dados do utilizador.'},
        'safe': {'severity': 'LOW', 'message': 'Uso do filtro safe no template. Verifique se o conteúdo é confiável.'},
        'DEBUG = True': {'severity': 'HIGH', 'message': 'DEBUG = True encontrado. Desative em produção.'},
        'SECRET_KEY': {'severity': 'LOW', 'message': 'Arquivo contém SECRET_KEY. Certifique-se de que não está versionado.'},
    }
    
    for root, dirs, files in os.walk(source_path):
        if 'venv' in root or 'venv_scanner' in root or '__pycache__' in root:
            continue
        
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                        lines = f.readlines()
                    
                    for i, line in enumerate(lines, 1):
                        for pattern, info in patterns.items():
                            if pattern in line:
                                issues.append({
                                    'filename': os.path.relpath(filepath, source_path),
                                    'line_number': i,
                                    'test_id': pattern,
                                    'issue_text': info['message'],
                                    'severity': info['severity'],
                                    'confidence': 'MEDIUM',
                                })
                except Exception:
                    pass
    
    return issues


if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print("Uso: python code_scanner.py <caminho_do_projeto>")
        sys.exit(1)
    
    results = scan_code(sys.argv[1])
    
    from rich.console import Console
    from rich.table import Table
    
    console = Console()
    console.print(f"\n[bold]Total de issues encontradas: {results['total_issues']}[/]")
    console.print(f"Por severidade: {results['por_severidade']}")
    
    if results['issues']:
        table = Table(title="Issues de Código")
        table.add_column("Arquivo")
        table.add_column("Linha")
        table.add_column("Severidade")
        table.add_column("Descrição")
        for iss in results['issues'][:20]:
            table.add_row(iss['filename'], str(iss['line_number']), 
                         f"[red]{iss['severity']}[/]" if iss['severity'] == 'HIGH' else iss['severity'],
                         iss['issue_text'][:80])
        console.print(table)
        if len(results['issues']) > 20:
            console.print(f"[yellow]... e mais {len(results['issues'])-20} issues[/]")
