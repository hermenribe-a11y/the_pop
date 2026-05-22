
from django.db import models

class PaginaDinamica(models.Model):
    CATEGORIAS = [
        ('sobre', 'Sobre Nós'),
        ('links', 'Links Rápidos'),
        ('termos', 'Termos de Uso'),
        ('privacidade', 'Privacidade'),
        ('contato', 'Contato'),
    ]
    categoria = models.CharField(max_length=20, choices=CATEGORIAS, unique=True)
    titulo = models.CharField(max_length=200)
    conteudo = models.TextField(help_text="HTML permitido")
    ativo = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.titulo

    class Meta:
        verbose_name = 'Página Dinâmica'
        verbose_name_plural = 'Páginas Dinâmicas'

class RedeSocial(models.Model):
    nome = models.CharField(max_length=100)
    url = models.URLField(help_text="Link para a rede social")
    icone = models.CharField(max_length=50, help_text="Classe do ícone (ex: fab fa-facebook, fab fa-instagram, fab fa-twitter)")
    ordem = models.IntegerField(default=0)
    ativo = models.BooleanField(default=True)

    def __str__(self):
        return self.nome

    class Meta:
        verbose_name = 'Rede Social'
        verbose_name_plural = 'Redes Sociais'
        ordering = ['ordem']
