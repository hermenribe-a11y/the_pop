from django.views.generic import ListView, DetailView
from django.db.models import Q
from .models import Categoria, Artigo

class HomeView(ListView):
    model = Artigo
    template_name = 'news/home.html'
    context_object_name = 'ultimas_noticias'

    def get_queryset(self):
        return Artigo.objects.filter(status='published').order_by('-data_publicacao')[:10]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['artigos_destaque'] = Artigo.objects.filter(
            status='published', destaque=True
        ).order_by('-data_publicacao')[:3]
        return context

class ArticleDetailView(DetailView):
    model = Artigo
    template_name = 'news/article_detail.html'
    context_object_name = 'artigo'

    def get_object(self, queryset=None):
        artigo = super().get_object(queryset)
        artigo.visualizacoes += 1
        artigo.save(update_fields=['visualizacoes'])
        return artigo

class CategoryListView(ListView):
    model = Artigo
    template_name = 'news/category.html'
    context_object_name = 'artigos'

    def get_queryset(self):
        self.categoria = Categoria.objects.get(slug=self.kwargs['slug'])
        return Artigo.objects.filter(
            categoria=self.categoria, status='published'
        ).order_by('-data_publicacao')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categoria'] = self.categoria
        return context

class SearchView(ListView):
    model = Artigo
    template_name = 'news/search.html'
    context_object_name = 'artigos'
    paginate_by = 10

    def get_queryset(self):
        query = self.request.GET.get('q', '')
        if query:
            return Artigo.objects.filter(
                Q(titulo__icontains=query) |
                Q(resumo__icontains=query) |
                Q(conteudo__icontains=query),
                status='published'
            ).order_by('-data_publicacao')
        return Artigo.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['query'] = self.request.GET.get('q', '')
        return context
