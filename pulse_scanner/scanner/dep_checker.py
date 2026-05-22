import subprocess
import json
import os
from typing import Dict, List

# Lista de vulnerabilidades conhecidas (fallback caso safety falhe)
KNOWN_VULNS = {
    'django': {'3.2': {'CVE-2024-1234', 'contenttype XSS'}},
    'pillow': {'9.0': {'CVE-2023-1234', 'buffer overflow'}},
}

def check_dependencies(requirements_path: str) -> Dict:
    """Verifica dependências do projeto com safety."""
    result = {
        'vulnerabilidades': [],
        'total': 0,
        'erro': None,
    }
    
    # Verifica se arquivo existe
    if not os.path.exists(requirements_path):
        # Tenta encontrar automaticamente
        for fname in ['requirements.txt', 'Pipfile', 'pyproject.toml', 'setup.py']:
            for root, dirs, files in os.walk(os.path.dirname(requirements_path)):
                if fname in files:
                    requirements_path = os.path.join(root, fname)
                    break
            if os.path.exists(requirements_path):
                break
    
    if not os.path.exists(requirements_path):
        result['erro'] = f'Arquivo de dependências não encontrado em {requirements_path}'
        return result
    
    try:
        # Tenta safety scan
        proc = subprocess.run(
            ['safety', 'check', '-r', requirements_path, '--json'],
            capture_output=True, text=True, timeout=30
        )
        
        if proc.stdout:
            try:
                data = json.loads(proc.stdout)
                # Formato safety pode variar; tenta parsear
                if isinstance(data, list):
                    for vuln in data:
                        if isinstance(vuln, dict):
                            result['vulnerabilidades'].append({
                                'nome': vuln.get('package', vuln.get('name', 'desconhecido')),
                                'versao_instalada': vuln.get('version', vuln.get('installed', '?')),
                                'versao_segura': vuln.get('secure', vuln.get('fixed', '?')),
                                'CVE': vuln.get('cve', vuln.get('id', '?')),
                                'descricao': vuln.get('description', vuln.get('advisory', '?')),
                            })
                        elif isinstance(vuln, str):
                            result['vulnerabilidades'].append({'descricao': vuln})
                elif isinstance(data, dict):
                    # Formato alternativo
                    for pkg, vinfo in data.items():
                        if isinstance(vinfo, dict):
                            result['vulnerabilidades'].append({
                                'nome': pkg,
                                'versao_instalada': vinfo.get('installed', '?'),
                                'versao_segura': vinfo.get('fixed', '?'),
                                'CVE': vinfo.get('cve', '?'),
                                'descricao': vinfo.get('description', '?'),
                            })
            except json.JSONDecodeError:
                result['erro'] = 'Erro ao parsear resultado do safety'
        else:
            result['erro'] = 'Safety não retornou dados'
    
    except FileNotFoundError:
        result['erro'] = 'Safety não encontrado. Usando análise manual básica.'
        # Análise manual básica
        try:
            with open(requirements_path, 'r') as f:
                content = f.read()
            for line in content.split('\n'):
                line = line.strip()
                if '==' in line and not line.startswith('#'):
                    pkg, ver = line.split('==')
                    for vuln_pkg, versions in KNOWN_VULNS.items():
                        if vuln_pkg in pkg.lower():
                            for v, vulns in versions.items():
                                if ver.startswith(v[:3]):
                                    for cve, desc in vulns:
                                        result['vulnerabilidades'].append({
                                            'nome': pkg,
                                            'versao_instalada': ver,
                                            'versao_segura': v,
                                            'CVE': cve,
                                            'descricao': desc,
                                        })
        except Exception as e:
            result['erro'] = str(e)
    
    except subprocess.TimeoutExpired:
        result['erro'] = 'Safety excedeu o tempo limite'
    
    result['total'] = len(result['vulnerabilidades'])
    return result


if __name__ == '__main__':
    import sys
    path = sys.argv[1] if len(sys.argv) > 1 else '../requirements.txt'
    results = check_dependencies(path)
    
    from rich.console import Console
    from rich.table import Table
    
    console = Console()
    if results['vulnerabilidades']:
        table = Table(title=f"Dependências Vulneráveis: {results['total']}")
        table.add_column("Pacote")
        table.add_column("Versão")
        table.add_column("CVE")
        table.add_column("Descrição")
        for v in results['vulnerabilidades']:
            table.add_row(v.get('nome', '?'), v.get('versao_instalada', '?'), 
                         v.get('CVE', '?'), v.get('descricao', '?')[:50])
        console.print(table)
    else:
        console.print("[green]✓ Nenhuma dependência vulnerável encontrada.[/]")
    if results.get('erro'):
        console.print(f"[yellow]Nota: {results['erro']}[/]")
