from django.urls import path
from . import views

urlpatterns = [
    path('sobre/', views.pagina_dinamica, {'categoria': 'sobre'}, name='sobre'),
    path('links/', views.pagina_dinamica, {'categoria': 'links'}, name='links'),
    path('termos/', views.pagina_dinamica, {'categoria': 'termos'}, name='termos'),
    path('privacidade/', views.pagina_dinamica, {'categoria': 'privacidade'}, name='privacidade'),
    path('contato/', views.pagina_dinamica, {'categoria': 'contato'}, name='contato'),
    path('', views.index, name='index'),
]
