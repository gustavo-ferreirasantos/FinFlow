from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.db import transaction

from .models import Profile, Workspace, WorkspaceMember, Invitation


class UserRegisterForm(UserCreationForm):
    telephone = forms.CharField(
        max_length=20,
        required=False,
        label="Telefone / Celular",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '(11) 99999-9999'})
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'first_name', 'last_name', 'email')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault('class', 'form-control')

    def save(self, commit=True):
        with transaction.atomic():
            # Salva a instância de User
            user = super().save(commit=True)
            telephone = self.cleaned_data.get('telephone', '')

            # Cria ou atualiza o Profile vinculado
            profile, _ = Profile.objects.get_or_create(
                user=user,
                defaults={'telephone': telephone}
            )
            if telephone and profile.telephone != telephone:
                profile.telephone = telephone
                profile.save()

            workspace_name = f"Finanças de {user.first_name or user.username}"
            workspace = Workspace.objects.create(
                name=workspace_name,
                holder=profile
            )

            # Associa o usuário ao seu espaço como Titular ('T')
            WorkspaceMember.objects.create(
                workspace=workspace,
                profile=profile,
                role='T'
            )

            return user


class ProfileEditForm(forms.ModelForm):
    first_name = forms.CharField(
        max_length=150,
        required=False,
        label="Nome",
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    last_name = forms.CharField(
        max_length=150,
        required=False,
        label="Sobrenome",
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    email = forms.EmailField(
        required=True,
        label="E-mail",
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = Profile
        fields = ('telephone',)
        widgets = {
            'telephone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '(11) 99999-9999'}),
        }
        labels = {
            'telephone': 'Telefone / Celular',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Preenche os campos extras do formulário com os valores atuais do User
        if self.instance and hasattr(self.instance, 'user') and self.instance.user:
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name
            self.fields['email'].initial = self.instance.user.email

    def save(self, commit=True):
        # Salva os campos do Profile
        profile = super().save(commit=commit)

        # Atualiza e salva a instância relacionada de User
        user = profile.user
        user.first_name = self.cleaned_data.get('first_name', '').strip()
        user.last_name = self.cleaned_data.get('last_name', '').strip()
        user.email = self.cleaned_data.get('email', '').strip()
        user.save()

        return profile


class WorkspaceForm(forms.ModelForm):
    class Meta:
        model = Workspace
        fields = ('name',)
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: Finanças da Família, Empresa XYZ, Pessoal'
            }),
        }
        labels = {
            'name': 'Nome do Espaço',
        }

    def clean_name(self):
        name = self.cleaned_data.get('name', '').strip()
        if not name:
            raise forms.ValidationError("O nome do espaço não pode ficar em branco.")
        return name


class InvitationForm(forms.ModelForm):
    class Meta:
        model = Invitation
        fields = ('email',)
        widgets = {
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'exemplo@email.com'
            }),
        }
        labels = {
            'email': 'E-mail do Convidado',
        }

    def __init__(self, *args, workspace=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.workspace = workspace

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()

        if self.workspace:
            # Verifica se já é membro ativo deste workspace
            already_member = WorkspaceMember.objects.filter(
                workspace=self.workspace,
                profile__user__email__iexact=email
            ).exists()
            if already_member:
                raise forms.ValidationError("Este usuário já é membro deste espaço financeiro.")

            # Verifica se já existe um convite pendente para este e-mail
            pending_invite = Invitation.objects.filter(
                workspace=self.workspace,
                email__iexact=email,
                status='P'
            ).exists()
            if pending_invite:
                raise forms.ValidationError("Já existe um convite pendente enviado para este e-mail.")

        return email
