from django.db import models
from django.contrib.auth.models import User






class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    telephone = models.CharField(max_length=30)

    def __str__(self):
        """Representação em string do modelo"""
        return self.telephone


class Workspace (models.Model):
    name = models.CharField(max_length=100)
    holder = models.ForeignKey(Profile, on_delete=models.CASCADE)
    created_at = models.DateField()
    def __str__(self):
        """Representação em string do modelo"""
        return self.name



class WorkspaceMember (models.Model):
    TYPES = {
        "T": "TITULAR",
        "M": "MEMBRO",
    }
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE)
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE)
    role = models.CharField(max_length=1, choices=TYPES)
    created_at = models.DataField()
    def __str__(self):
        """Representação em string do modelo"""
        return self.workspace, self.profile, self.role, self.date


class Invitation (models.Model):
    nome = models.CharField(max_length=100)
    holder = models.ForeignKey(Profile, on_delete=models.CASCADE)
    def __str__(self):
        """Representação em string do modelo"""
