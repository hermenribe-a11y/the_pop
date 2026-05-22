from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
from reportlab.graphics.shapes import Drawing, Rect, String
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics import renderPDF
from datetime import datetime
import os
from typing import Dict

def generate_report(scan_results: Dict, output_path: str) -> str:
    """Gera um relatório PDF profissional com os resultados do scan."""
    
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        topMargin=1*inch,
        bottomMargin=1*inch,
        leftMargin=1*inch,
        rightMargin=1*inch,
    )
    
    styles = getSampleStyleSheet()
    
    # Estilos personalizados
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1a1a2e'),
        spaceAfter=12,
    )
    subtitle_style = ParagraphStyle(
        'Subtitle',
        parent=styles['Normal'],
        fontSize=12,
        textColor=colors.HexColor('#666666'),
        spaceAfter=24,
    )
    section_style = ParagraphStyle(
        'Section',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#1a1a2e'),
        spaceBefore=20,
        spaceAfter=10,
    )
    pass_style = ParagraphStyle(
        'Pass',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#2ecc71'),
    )
    fail_style = ParagraphStyle(
        'Fail',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#e74c3c'),
    )
    warn_style = ParagraphStyle(
        'Warn',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#f39c12'),
    )
    
    elements = []
    
    # --- CAPA ---
    elements.append(Spacer(1, 2*inch))
    elements.append(Paragraph("PULSE SCANNER", title_style))
    elements.append(Paragraph("Relatório de Segurança", ParagraphStyle(
        'SubTitle2', parent=title_style, fontSize=18, textColor=colors.HexColor('#e63946'))))
    elements.append(Spacer(1, 0.5*inch))
    
    project_name = scan_results.get('projeto', 'The Pulse')
    elements.append(Paragraph(f"Projeto: {project_name}", subtitle_style))
    elements.append(Paragraph(f"Data do scan: {scan_results.get('data_scan', datetime.now().strftime('%d/%m/%Y %H:%M'))}", subtitle_style))
    
    score = scan_results.get('score_seguranca', 0)
    score_color = colors.HexColor('#2ecc71') if score >= 80 else colors.HexColor('#f39c12') if score >= 50 else colors.HexColor('#e74c3c')
    elements.append(Spacer(1, 0.5*inch))
    elements.append(Paragraph(f"Score de Segurança: {score}/100", ParagraphStyle(
        'Score', parent=title_style, fontSize=36, textColor=score_color, alignment=1)))
    
    # Barra de score visual
    d = Drawing(400, 30)
    d.add(Rect(0, 5, 400, 20, fillColor=colors.HexColor('#ecf0f1'), strokeColor=None))
    bar_color = colors.HexColor('#2ecc71') if score >= 80 else colors.HexColor('#f39c12') if score >= 50 else colors.HexColor('#e74c3c')
    d.add(Rect(0, 5, 400 * score / 100, 20, fillColor=bar_color, strokeColor=None))
    elements.append(d)
    
    elements.append(PageBreak())
    
    # --- RESUMO ---
    elements.append(Paragraph("Resumo da Análise", section_style))
    django_checks = scan_results.get('django_checks', [])
    url_vulns = scan_results.get('url_vulnerabilities', [])
    code_issues = scan_results.get('code_issues', {})
    dep_issues = scan_results.get('dep_issues', [])
    
    pass_count = sum(1 for c in django_checks if c['status'] == 'PASS')
    fail_count = sum(1 for c in django_checks if c['status'] == 'FAIL')
    warn_count = sum(1 for c in django_checks if c['status'] == 'WARN')
    
    total_dep = dep_issues if isinstance(dep_issues, int) else len(dep_issues) if isinstance(dep_issues, list) else 0
    total_code = code_issues.get('total_issues', 0) if isinstance(code_issues, dict) else 0
    
    summary_data = [
        ['Configuração Django', f'{pass_count} PASS, {fail_count} FAIL, {warn_count} WARN'],
        ['Vulnerabilidades em URLs', str(len(url_vulns))],
        ['Issues de Código', str(total_code)],
        ['Dependências Vulneráveis', str(total_dep)],
    ]
    
    summary_table = Table(summary_data, colWidths=[3*inch, 3*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#1a1a2e')),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.white),
        ('BACKGROUND', (1, 0), (1, -1), colors.HexColor('#f8f9fa')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#dee2e6')),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ALIGN', (1, 0), (1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 0.3*inch))
    
    # --- CHECKS DJANGO ---
    elements.append(PageBreak())
    elements.append(Paragraph("1. Verificação de Configuração Django", section_style))
    
    for check in django_checks:
        status = check['status']
        text_color = pass_style if status == 'PASS' else fail_style if status == 'FAIL' else warn_style
        icon = '✓' if status == 'PASS' else '✗' if status == 'FAIL' else '⚠'
        elements.append(Paragraph(f"{icon} <b>{check['check']}</b>: {status}", text_color))
        elements.append(Paragraph(f"   {check['descricao']}", styles['Normal']))
        if check['correcao']:
            elements.append(Paragraph(f"   <i>Correção: {check['correcao']}</i>", ParagraphStyle(
                'Fix', parent=styles['Normal'], fontSize=9, textColor=colors.HexColor('#7f8c8d'))))
        elements.append(Spacer(1, 0.1*inch))
    
    # --- VULNERABILIDADES URL ---
    if url_vulns:
        elements.append(PageBreak())
        elements.append(Paragraph("2. Vulnerabilidades em URLs", section_style))
        
        vuln_data = [['URL', 'Tipo', 'Severidade', 'Detalhes']]
        for v in url_vulns:
            vuln_data.append([
                v.get('url', v.get('detalhes', ''))[:40],
                v.get('tipo', ''),
                v.get('severidade', ''),
                v.get('detalhes', '')[:60],
            ])
        
        vuln_table = Table(vuln_data, colWidths=[2*inch, 1*inch, 1*inch, 2*inch])
        vuln_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a1a2e')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#dee2e6')),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('ALIGN', (2, 0), (2, -1), 'CENTER'),
        ]))
        elements.append(vuln_table)
    
    # --- ISSUES DE CÓDIGO ---
    if isinstance(code_issues, dict) and code_issues.get('issues'):
        elements.append(PageBreak())
        elements.append(Paragraph("3. Issues de Código Fonte", section_style))
        
        code_data = [['Arquivo', 'Linha', 'Severidade', 'Descrição']]
        for iss in code_issues['issues'][:25]:
            code_data.append([
                iss.get('filename', '')[:30],
                str(iss.get('line_number', '')),
                iss.get('severity', ''),
                iss.get('issue_text', '')[:50],
            ])
        
        code_table = Table(code_data, colWidths=[2*inch, 0.5*inch, 1*inch, 2.5*inch])
        code_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a1a2e')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#dee2e6')),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
        ]))
        elements.append(code_table)
    
    # --- RECOMENDAÇÕES ---
    elements.append(PageBreak())
    elements.append(Paragraph("4. Plano de Correção Prioritário", section_style))
    
    recommendations = [
        "<b>CRÍTICO:</b> Desativar DEBUG = False em produção",
        "<b>CRÍTICO:</b> Configurar ALLOWED_HOSTS corretamente",
        "<b>ALTO:</b> Gerar nova SECRET_KEY segura",
        "<b>MÉDIO:</b> Ativar headers de segurança (X-Frame-Options, XSS Filter, Content-Type Nosniff)",
        "<b>MÉDIO:</b> Configurar SESSION_COOKIE_HTTPONLY e CSRF_COOKIE_HTTPONLY",
        "<b>BAIXO:</b> Adicionar configuração de HSTS",
        "<b>BAIXO:</b> Rever permissões de arquivos do projeto",
    ]
    
    for rec in recommendations:
        elements.append(Paragraph(f"• {rec}", styles['Normal']))
        elements.append(Spacer(1, 0.05*inch))
    
    # --- RODAPÉ ---
    elements.append(Spacer(1, 0.5*inch))
    elements.append(Paragraph(
        "Este relatório foi gerado automaticamente pelo Pulse Scanner. "
        "Recomenda-se revisão manual das vulnerabilidades identificadas.",
        ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8, 
                      textColor=colors.HexColor('#95a5a6'), alignment=1)
    ))
    
    # Gerar PDF
    doc.build(elements)
    return output_path


if __name__ == '__main__':
    # Teste
    test_results = {
        'projeto': 'The Pulse',
        'data_scan': datetime.now().strftime('%d/%m/%Y %H:%M'),
        'score_seguranca': 65,
        'django_checks': [
            {'check': 'DEBUG', 'status': 'FAIL', 'severity': 'CRITICAL', 
             'descricao': 'DEBUG está ativado', 'correcao': 'Desative DEBUG'},
            {'check': 'SECRET_KEY', 'status': 'PASS', 'severity': 'HIGH',
             'descricao': 'SECRET_KEY personalizada', 'correcao': ''},
        ],
        'url_vulnerabilities': [],
        'code_issues': {'total_issues': 2, 'issues': [
            {'filename': 'views.py', 'line_number': 45, 'severity': 'HIGH', 'issue_text': 'Possível SQL Injection'},
        ]},
        'dep_issues': [],
    }
    
    output = generate_report(test_results, 'relatorio_teste.pdf')
    print(f"Relatório gerado: {output}")
