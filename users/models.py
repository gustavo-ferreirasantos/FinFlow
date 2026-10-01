from django.db import models
import uuid
from django.contrib.auth.models import User



class Profile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    telephone = models.CharField(max_length=30, blank=True)

    class Meta:
        verbose_name = "Pefil"
        verbose_name_plural = "Perfis"
        ordering = ["user__first_name"]

    def __str__(self):
        """Representação em string do modelo"""
        return self.user.username



class Workspace (models.Model):
    name = models.CharField(max_length=100)
    holder = models.ForeignKey(Profile, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Espaço de trabalho"
        verbose_name_plural = "Espaços de trabalho"
        ordering = ["name"]

    def __str__(self):
        """Representação em string do modelo"""
        return self.name


class WorkspaceMember (models.Model):
    ROLE_CHOICES = {
        "T": "TITULAR",
        "M": "MEMBRO",
    }
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE)
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE)
    role = models.CharField(max_length=1, choices=ROLE_CHOICES)
    registered_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Membro do espaço de trabalho"
        verbose_name_plural = "Membros do espaço de trabalho"
        ordering = ["workspace"]

    def __str__(self):
        """Representação em string do modelo"""
        return f"{self.workspace} - {self.profile}"



class Invitation (models.Model):
    STATUS_CHOICES = {
        "P": "PENDENTE",
        "A": "ACEITO",
        "R": "REJEITADO",
        "E": "EXPIRADO",
    }
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE)
    email = models.EmailField()
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default="P")
    token = models.UUIDField(default=uuid.uuid4, unique=True, blank=True, null=True)
    sent_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Convite"
        verbose_name_plural = "Convites"
        ordering = ["sent_at"]

    def __str__(self):
        """Representação em string do modelo"""
        return self.email
