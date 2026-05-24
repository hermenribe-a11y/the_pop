from django.urls import path
from . import views

app_name = 'legal'

urlpatterns = [
    path('termos/', views.TermosView.as_view(), name='termos'),
    path('privacidade/', views.PrivacidadeView.as_view(), name='privacidade'),
    path('contato/', views.ContatoView.as_view(), name='contato'),
    path('sobre_nos/', views.sobre_nosView.as_view(), name='sobre_nos'),
]
