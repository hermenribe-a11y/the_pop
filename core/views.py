
from django.shortcuts import render, get_object_or_404
from .models import PaginaDinamica, RedeSocial
from news.models import Artigo

def pagina_dinamica(request, categoria):
    pagina = get_object_or_404(PaginaDinamica, categoria=categoria, ativo=True)
    return render(request, 'core/pagina_dinamica.html', {'pagina': pagina})

def index(request):
    artigos_destaque = Artigo.objects.filter(status='published').order_by('-data_publicacao')[:3]
    artigos_recentes = Artigo.objects.filter(status='published').order_by('-data_publicacao')[3:9]
    return render(request, 'core/index.html', {
        'artigos_destaque': artigos_destaque,
        'artigos_recentes': artigos_recentes,
    })
