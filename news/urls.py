from django.urls import path
from . import views

app_name = 'news'

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('artigo/<slug:slug>/', views.ArticleDetailView.as_view(), name='article_detail'),
    path('categoria/<slug:slug>/', views.CategoryListView.as_view(), name='category'),
    path('busca/', views.SearchView.as_view(), name='search'),
]
