from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from .forms import InvitationForm, ProfileEditForm, UserRegisterForm, WorkspaceForm
from .models import Invitation, Profile, Workspace, WorkspaceMember



#CreateView cria um novo usuario
class RegisterView(SuccessMessageMixin, CreateView):
    form_class = UserRegisterForm
    template_name = "users/register.html"
    success_url = reverse_lazy("login")
    success_message = "Cadastro realizado com sucesso! Faça login para continuar."

    def form_invalid(self, form):
        messages.error(self.request, "Erro ao realizar cadastro. Verifique os campos destacados.")
        return super().form_invalid(form)




#DetailView exibe o perfil do usuario logado
class ProfileDetailView(LoginRequiredMixin, DetailView):
    model = Profile
    template_name = "users/profile.html"
    context_object_name = "profile"

    def get_object(self):
        profile, _ = Profile.objects.get_or_create(user=self.request.user)
        return profile




#UpdateView atualiza os dados do perfil e usuario
class ProfileUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Profile
    form_class = ProfileEditForm
    template_name = "users/profile_edit.html"
    success_url = reverse_lazy("users:profile")
    success_message = "Perfil atualizado com sucesso."

    def get_object(self):
        profile, _ = Profile.objects.get_or_create(user=self.request.user)
        return profile

    def form_invalid(self, form):
        messages.error(self.request, "Não foi possível atualizar o perfil. Corrija os erros.")
        return super().form_invalid(form)




#ListView exibe os workspaces do usuario
class WorkspaceListView(LoginRequiredMixin, ListView):
    model = Workspace
    template_name = "users/workspace_list.html"
    context_object_name = "workspaces"

    def get_queryset(self):
        profile, _ = Profile.objects.get_or_create(user=self.request.user)
        return Workspace.objects.filter(members__profile=profile).order_by("name")




#CreateView cria um novo workspace
class WorkspaceCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = Workspace
    form_class = WorkspaceForm
    template_name = "users/workspace_form.html"
    success_url = reverse_lazy("users:workspace_list")
    success_message = "Espaço “%(name)s” criado com sucesso."

    def form_valid(self, form):
        with transaction.atomic():
            profile, _ = Profile.objects.get_or_create(user=self.request.user)
            form.instance.holder = profile
            response = super().form_valid(form)
            # cria membro titular
            WorkspaceMember.objects.create(
                workspace=self.object,
                profile=profile,
                role="T"
            )
            # ativa na sessao
            self.request.session["active_workspace_id"] = str(self.object.id)
            return response

    def form_invalid(self, form):
        messages.error(self.request, "Não foi possível criar o espaço. Corrija o nome.")
        return super().form_invalid(form)




#DetailView exibe detalhes e membros do workspace
class WorkspaceDetailView(LoginRequiredMixin, DetailView):
    model = Workspace
    template_name = "users/workspace_detail.html"
    context_object_name = "workspace"

    def get_queryset(self):
        profile, _ = Profile.objects.get_or_create(user=self.request.user)
        return Workspace.objects.filter(members__profile=profile)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        workspace = self.object
        profile, _ = Profile.objects.get_or_create(user=self.request.user)
        context["members"] = workspace.members.select_related("profile__user").all()
        context["pending_invitations"] = Invitation.objects.filter(workspace=workspace, status="P").order_by("-sent_at")
        context["is_holder"] = (workspace.holder == profile)
        return context




#View troca o workspace ativo na sessao
class WorkspaceSelectView(LoginRequiredMixin, View):
    def get(self, request, pk):
        profile, _ = Profile.objects.get_or_create(user=request.user)
        workspace = get_object_or_404(Workspace, id=pk, members__profile=profile)
        request.session["active_workspace_id"] = str(workspace.id)
        messages.success(request, f"Espaço alterado para “{workspace.name}”.")
        next_url = request.META.get("HTTP_REFERER") or reverse_lazy("finances:transaction_list")
        return redirect(next_url)




#CreateView cria um novo convite para o workspace
class InviteMemberView(LoginRequiredMixin, CreateView):
    model = Invitation
    form_class = InvitationForm
    template_name = "users/invite_member.html"

    def get_workspace(self):
        profile, _ = Profile.objects.get_or_create(user=self.request.user)
        return get_object_or_404(Workspace, pk=self.kwargs.get("pk"), members__profile=profile)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["workspace"] = self.get_workspace()
        return kwargs

    def form_valid(self, form):
        workspace = self.get_workspace()
        form.instance.workspace = workspace
        response = super().form_valid(form)
        accept_url = self.request.build_absolute_uri(
            reverse_lazy("users:accept_invitation", kwargs={"token": self.object.token})
        )
        messages.success(self.request, f"Convite criado para {self.object.email}! Link: {accept_url}")
        return response

    def get_success_url(self):
        return reverse_lazy("users:workspace_detail", kwargs={"pk": self.get_workspace().pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["workspace"] = self.get_workspace()
        return context

    def form_invalid(self, form):
        messages.error(self.request, "Não foi possível enviar o convite. Verifique o e-mail.")
        return super().form_invalid(form)




#View aceita o convite atraves do token
class AcceptInvitationView(LoginRequiredMixin, View):
    def get(self, request, token):
        profile, _ = Profile.objects.get_or_create(user=request.user)
        invitation = get_object_or_404(Invitation, token=token, status="P")
        with transaction.atomic():
            WorkspaceMember.objects.get_or_create(workspace=invitation.workspace,profile=profile,defaults={"role": "M"})
            invitation.status = "A"
            invitation.save()

        request.session["active_workspace_id"] = str(invitation.workspace.id)
        messages.success(request, f"Convite aceito! Você entrou no espaço “{invitation.workspace.name}”.")
        return redirect("finances:transaction_list")


class WorkspaceUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Workspace
    form_class = WorkspaceForm
    template_name = "users/workspace_form.html"
    success_url = reverse_lazy("users:workspace_list")
    success_message = "Espaço atualizado com sucesso."

    def get_queryset(self):
        profile, _ = Profile.objects.get_or_create(user=self.request.user)
        return Workspace.objects.filter(holder=profile)


class WorkspaceDeleteView(LoginRequiredMixin, DeleteView):
    model = Workspace
    template_name = "users/workspace_confirm_delete.html"
    success_url = reverse_lazy("users:workspace_list")

    def get_queryset(self):
        profile, _ = Profile.objects.get_or_create(user=self.request.user)
        return Workspace.objects.filter(holder=profile)

    def form_valid(self, form):
        workspace = self.get_object()
        if self.request.session.get("active_workspace_id") == str(workspace.id):
            self.request.session.pop("active_workspace_id", None)
        messages.success(self.request, f"Espaço “{workspace.name}” excluído com sucesso.")
        return super().form_valid(form)
