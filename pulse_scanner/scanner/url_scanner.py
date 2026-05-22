import requests
from urllib.parse import urljoin, urlparse, parse_qs, urlencode, urlunparse
from typing import List, Dict, Optional
import time

PAYLOADS_SQLI = [
    "' OR '1'='1",
    "' OR '1'='1' --",
    "1; DROP TABLE users--",
    "' UNION SELECT NULL--",
    "\" OR \"1\"=\"1",
    "' OR 1=1--",
]

PAYLOADS_XSS = [
    "<script>alert('XSS')</script>",
    "<img src=x onerror=alert('XSS')>",
    "<svg onload=alert('XSS')>",
    "javascript:alert('XSS')",
    "\"><script>alert('XSS')</script>",
]

PAYLOADS_CSRF = [
    {"test": "csrf_test", "payload": "application/json", "header": "text/plain"},
]


def test_sqli(base_url: str, paths: List[str], cookies: Optional[Dict] = None) -> List[Dict]:
    """Testa SQL Injection nas URLs fornecidas."""
    results = []
    if cookies is None:
        cookies = {}
    
    for path in paths:
        url = urljoin(base_url, path)
        parsed = urlparse(url)
        
        # Se a URL tiver parâmetros, testa cada um
        if parsed.query:
            params = parse_qs(parsed.query)
            for param, values in params.items():
                for payload in PAYLOADS_SQLI:
                    test_params = params.copy()
                    test_params[param] = [payload]
                    test_url = urlunparse(parsed._replace(query=urlencode(test_params, doseq=True)))
                    
                    try:
                        resp = requests.get(test_url, cookies=cookies, timeout=5)
                        # Indicadores de SQLi: erros de banco, palavras-chave
                        indicators = ['sql', 'syntax', 'mysql', 'postgres', 'sqlite', 
                                     'unclosed quotation', 'odbc', 'error in your sql']
                        has_error = any(ind in resp.text.lower() for ind in indicators)
                        
                        if has_error:
                            results.append({
                                'url': test_url,
                                'parametro': param,
                                'payload': payload,
                                'tipo': 'SQL Injection',
                                'status_code': resp.status_code,
                                'evidencia': 'Mensagem de erro SQL encontrada na resposta' if has_error else '',
                                'severidade': 'HIGH',
                                'detalhes': f'Possível SQL Injection no parâmetro {param}'
                            })
                    except Exception as e:
                        results.append({
                            'url': test_url,
                            'parametro': param,
                            'payload': payload,
                            'tipo': 'SQL Injection',
                            'status_code': 0,
                            'evidencia': str(e),
                            'severidade': 'LOW',
                            'detalhes': f'Erro ao testar: {str(e)}'
                        })
        else:
            # Testa POST com payloads no corpo
            for payload in PAYLOADS_SQLI:
                try:
                    resp = requests.post(url, data={'q': payload, 'id': payload, 'slug': payload}, 
                                       cookies=cookies, timeout=5)
                    indicators = ['sql', 'syntax', 'mysql', 'postgres', 'sqlite', 'unclosed quotation']
                    has_error = any(ind in resp.text.lower() for ind in indicators)
                    if has_error:
                        results.append({
                            'url': url,
                            'parametro': 'POST body',
                            'payload': payload,
                            'tipo': 'SQL Injection',
                            'status_code': resp.status_code,
                            'evidencia': 'Mensagem de erro SQL encontrada',
                            'severidade': 'HIGH',
                            'detalhes': f'Possível SQL Injection via POST'
                        })
                except Exception as e:
                    pass
    
    return results


def test_xss(base_url: str, paths: List[str], cookies: Optional[Dict] = None) -> List[Dict]:
    """Testa Cross-Site Scripting nas URLs."""
    results = []
    if cookies is None:
        cookies = {}
    
    for path in paths:
        url = urljoin(base_url, path)
        parsed = urlparse(url)
        
        if parsed.query:
            params = parse_qs(parsed.query)
            for param, values in params.items():
                for payload in PAYLOADS_XSS:
                    test_params = params.copy()
                    test_params[param] = [payload]
                    test_url = urlunparse(parsed._replace(query=urlencode(test_params, doseq=True)))
                    
                    try:
                        resp = requests.get(test_url, cookies=cookies, timeout=5)
                        if payload in resp.text:
                            results.append({
                                'url': test_url,
                                'parametro': param,
                                'payload': payload,
                                'tipo': 'XSS (Refletido)',
                                'status_code': resp.status_code,
                                'severidade': 'HIGH',
                                'detalhes': f'Payload XSS refletido na resposta no parâmetro {param}'
                            })
                    except Exception as e:
                        pass
    
    return results


def test_csrf_headers(base_url: str, paths: List[str], cookies: Optional[Dict] = None) -> List[Dict]:
    """Verifica proteção CSRF nas URLs POST."""
    results = []
    if cookies is None:
        cookies = {}
    
    for path in paths:
        url = urljoin(base_url, path)
        try:
            # Tenta POST sem CSRF token
            resp = requests.post(url, data={'test': 'csrf'}, cookies=cookies, timeout=5)
            if resp.status_code == 200 and 'csrf' not in resp.text.lower():
                results.append({
                    'url': url,
                    'tipo': 'CSRF',
                    'status_code': resp.status_code,
                    'severidade': 'MEDIUM',
                    'detalhes': 'URL POST parece aceitar requisições sem token CSRF'
                })
        except Exception:
            pass
    
    return results


def scan_all(base_url: str, paths: List[str], cookies: Optional[Dict] = None) -> Dict:
    """Executa todos os testes de segurança nas URLs fornecidas."""
    results = {
        'sqli': {'testados': 0, 'vulnerabilidades': []},
        'xss': {'testados': 0, 'vulnerabilidades': []},
        'csrf': {'testados': 0, 'vulnerabilidades': []},
        'total_urls': len(paths),
        'total_vulnerabilidades': 0,
    }
    
    print(f"[SCAN] Testando {len(paths)} URLs...")
    
    try:
        results['sqli']['vulnerabilidades'] = test_sqli(base_url, paths, cookies)
        results['sqli']['testados'] = len(paths) * len(PAYLOADS_SQLI)
    except Exception as e:
        results['sqli']['erro'] = str(e)
    
    try:
        results['xss']['vulnerabilidades'] = test_xss(base_url, paths, cookies)
        results['xss']['testados'] = len(paths) * len(PAYLOADS_XSS)
    except Exception as e:
        results['xss']['erro'] = str(e)
    
    try:
        results['csrf']['vulnerabilidades'] = test_csrf_headers(base_url, paths, cookies)
        results['csrf']['testados'] = len(paths)
    except Exception as e:
        results['csrf']['erro'] = str(e)
    
    total = (len(results['sqli']['vulnerabilidades']) + 
             len(results['xss']['vulnerabilidades']) + 
             len(results['csrf']['vulnerabilidades']))
    results['total_vulnerabilidades'] = total
    
    return results


if __name__ == '__main__':
    import sys
    if len(sys.argv) < 3:
        print("Uso: python url_scanner.py <base_url> <path1,path2,...>")
        print("Ex: python url_scanner.py http://127.0.0.1:8000 /,/busca/?q=teste")
        sys.exit(1)
    
    base = sys.argv[1]
    paths = sys.argv[2].split(',')
    
    results = scan_all(base, paths)
    
    from rich.console import Console
    from rich.table import Table
    
    console = Console()
    
    for test_type in ['sqli', 'xss', 'csrf']:
        vulns = results[test_type]['vulnerabilidades']
        if vulns:
            table = Table(title=f"Vulnerabilidades {test_type.upper()} encontradas: {len(vulns)}")
            table.add_column("URL")
            table.add_column("Payload")
            table.add_column("Severidade")
            for v in vulns:
                table.add_row(v.get('url', v.get('detalhes', '')), 
                             v.get('payload', '-'), 
                             f"[red]{v['severidade']}[/]")
            console.print(table)
        else:
            console.print(f"[green]✓[/] {test_type.upper()}: Nenhuma vulnerabilidade encontrada.")
