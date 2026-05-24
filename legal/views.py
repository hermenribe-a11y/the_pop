from django.views.generic import TemplateView

class PrivacidadeView(TemplateView):
    template_name = 'legal/privacidade.html'

class TermosView(TemplateView):
    template_name = 'legal/termos.html'

class ContatoView(TemplateView):
    template_name = 'legal/contato.html'

class sobre_nosView(TemplateView):
    template_name = 'legal/sobre_nos.html'
