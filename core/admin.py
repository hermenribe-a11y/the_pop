
from django.contrib import admin
from .models import PaginaDinamica, RedeSocial

@admin.register(PaginaDinamica)
class PaginaDinamicaAdmin(admin.ModelAdmin):
    list_display = ['titulo', 'categoria', 'ativo', 'atualizado_em']
    list_editable = ['ativo']
    search_fields = ['titulo', 'conteudo']

@admin.register(RedeSocial)
class RedeSocialAdmin(admin.ModelAdmin):
    list_display = ['nome', 'url', 'ordem', 'ativo']
    list_editable = ['ordem', 'ativo']
