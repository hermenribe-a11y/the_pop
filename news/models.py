from django.db import models
from django.contrib.auth.models import User
from slugify import slugify

class Categoria(models.Model):
    name = models.CharField(max_length=80, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    cor_badge = models.CharField(
        max_length=7, default='#e63946',
        help_text='Cor em hexadecimal para o badge da categoria'
    )
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Categorias"
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Author(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(blank=True)
    avatar = models.ImageField(upload_to='autores/', blank=True)
    site = models.URLField(blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.get_full_name() or self.user.username


class Artigo(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Rascunho'),
        ('published', 'Publicado'),
    ]

    titulo = models.CharField(max_length=255)
    slug = models.SlugField(max_length=300, unique=True)
    categoria = models.ForeignKey(
        Categoria, on_delete=models.SET_NULL, null=True,
        related_name='artigos'
    )
    autor = models.ForeignKey(
        Author, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='artigos'
    )
    resumo = models.TextField(
        max_length=500,
        help_text='Breve resumo para aparecer nos cards'
    )
    conteudo = models.TextField()
    imagem = models.ImageField(upload_to='artigos/', blank=True)
    imagem_credito = models.CharField(
        max_length=200, blank=True,
        help_text='Crédito da imagem'
    )
    status = models.CharField(
        max_length=15, choices=STATUS_CHOICES, default='draft'
    )
    destaque = models.BooleanField(
        default=False,
        help_text='Marcar para aparecer no destaque da homepage'
    )
    visualizacoes = models.PositiveIntegerField(default=0, editable=False)
    tempo_leitura = models.PositiveIntegerField(
        default=0, editable=False,
        help_text='Tempo estimado em minutos'
    )
    data_publicacao = models.DateTimeField(null=True, blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Artigos"
        ordering = ['-data_publicacao', '-criado_em']

    def __str__(self):
        return self.titulo

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.titulo)
        word_count = len(self.conteudo.split())
        self.tempo_leitura = max(1, round(word_count / 200))
        super().save(*args, **kwargs)
