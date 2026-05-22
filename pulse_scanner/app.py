from flask import Flask, render_template, request, jsonify, send_file
import os, sys, json, threading, time
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from scanner.django_checker import check_django_settings
from scanner.url_scanner import scan_all
from scanner.code_scanner import scan_code
from scanner.dep_checker import check_dependencies
from scanner.report_gen import generate_report

app = Flask(__name__)
app.config['SECRET_KEY'] = 'pulse-scanner-secret-2026'

resultados = {}
scan_rodando = False

def executar_scan(alvo, paths, cookies_opt):
    global resultados, scan_rodando
    scan_rodando = True
    
    # Se nenhum path fornecido, usa paths comuns
    if not paths or paths == ['']:
        paths = ['/', '/admin/', '/login/', '/busca/?q=teste', '/api/', '/wp-admin/']
    
    res = {
        'projeto': alvo,
        'data_scan': datetime.now().strftime('%d/%m/%Y %H:%M'),
        'progresso': 0,
        'django': [],
        'url': [],
        'codigo': {'total': 0, 'issues': []},
        'deps': 0,
        'score': 0,
        'status': 'rodando'
    }
    resultados = res
    
    try:
        # 1 - Testes de URL (SQLi, XSS, CSRF)
        res['progresso'] = 20
        try:
            cookies = {}
            if cookies_opt:
                for par in cookies_opt.split(';'):
                    if '=' in par:
                        k, v = par.split('=', 1)
                        cookies[k.strip()] = v.strip()
            url_r = scan_all(alvo, paths, cookies)
            for k in url_r:
                if isinstance(url_r[k], dict) and 'vulnerabilidades' in url_r[k]:
                    res['url'].extend(url_r[k]['vulnerabilidades'])
        except Exception as e:
            res['url'].append({'tipo': 'Erro', 'detalhes': str(e), 'severidade': 'INFO'})
        res['progresso'] = 60
        
        # 2 - Se for Django, analisar settings (opcional)
        try:
            settings_path = None
            # Tenta encontrar settings.py no projeto local
            if '127.0.0.1' in alvo or 'localhost' in alvo:
                projeto_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
                settings_path = os.path.join(projeto_path, 'the_pulse', 'settings.py')
                if os.path.exists(settings_path):
                    res['django'] = check_django_settings(settings_path)
        except:
            pass
        res['progresso'] = 80
        
        # 3 - Análise de código (apenas local)
        try:
            if '127.0.0.1' in alvo or 'localhost' in alvo:
                projeto_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
                res['codigo'] = scan_code(projeto_path)
        except:
            pass
        res['progresso'] = 90
        
        # Calcular score
        score = 100
        fails = sum(1 for c in res['django'] if c.get('status') == 'FAIL')
        warns = sum(1 for c in res['django'] if c.get('status') == 'WARN')
        score -= fails * 15 + warns * 5 + len(res['url']) * 10
        if isinstance(res['codigo'], dict):
            sev = res['codigo'].get('por_severidade', {})
            score -= sev.get('HIGH', 0) * 8 + sev.get('MEDIUM', 0) * 4
        res['score'] = max(0, min(100, score))
        res['status'] = 'completo'
        res['progresso'] = 100
    except Exception as e:
        res['status'] = 'erro'
        res['erro'] = str(e)
    
    resultados = res
    scan_rodando = False

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/scan', methods=['POST'])
def scan():
    global scan_rodando
    if scan_rodando:
        return jsonify({'ok': False, 'msg': 'Scan já em andamento'})
    
    alvo = request.form.get('alvo', 'http://127.0.0.1:8000')
    paths_raw = request.form.get('paths', '/,/admin/')
    paths = [p.strip() for p in paths_raw.split(',') if p.strip()]
    cookies_opt = request.form.get('cookies', '')
    
    threading.Thread(target=executar_scan, args=(alvo, paths, cookies_opt), daemon=True).start()
    return jsonify({'ok': True, 'msg': 'Scan iniciado contra: ' + alvo})

@app.route('/status')
def status():
    return jsonify({'rodando': scan_rodando, 'resultados': resultados})

@app.route('/relatorio')
def relatorio():
    if not resultados or resultados.get('status') != 'completo':
        return jsonify({'ok': False, 'msg': 'Nenhum scan concluído'})
    os.makedirs('reports', exist_ok=True)
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    pdf = f'reports/relatorio_{ts}.pdf'
    try:
        generate_report(resultados, pdf)
        return send_file(pdf, as_attachment=True, download_name=f'pulse_scan_{ts}.pdf')
    except Exception as e:
        return jsonify({'ok': False, 'msg': f'Erro ao gerar PDF: {str(e)}'})

if __name__ == '__main__':
    print("Pulse Scanner - Pentest Web Tool")
    print("Acesse: http://127.0.0.1:5001")
    app.run(debug=False, port=5001)
