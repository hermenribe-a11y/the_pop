from django.contrib import admin
from django.utils import timezone
from .models import Categoria, Author, Artigo

@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'cor_badge')
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = ('user', 'bio', 'site')

@admin.register(Artigo)
class ArtigoAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'categoria', 'status', 'destaque', 'visualizacoes', 'data_publicacao')
    list_filter = ('status', 'destaque', 'categoria', 'data_publicacao')
    search_fields = ('titulo', 'resumo', 'conteudo')
    prepopulated_fields = {'slug': ('titulo',)}
    list_editable = ('status', 'destaque')
    date_hierarchy = 'data_publicacao'
    readonly_fields = ('visualizacoes', 'criado_em', 'atualizado_em', 'tempo_leitura')
    actions = ['publicar_selecionados']

    def publicar_selecionados(self, request, queryset):
        updated = queryset.update(status='published', data_publicacao=timezone.now())
        self.message_user(request, f'{updated} artigo(s) publicado(s) com sucesso.')
    publicar_selecionados.short_description = "Publicar artigos selecionados"
