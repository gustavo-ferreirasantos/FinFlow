from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView

from users.models import Workspace
from .forms import TransactionForm
from .models import Transaction

# TEMPORÁRIO: trocar pelo get_active_workspace do users/utils.py
def get_active_workspace(request):
    workspaces = Workspace.objects.filter(workspacemember__profile__user=request.user)
    workspace_id = request.session.get("active_workspace_id")
    workspace = workspaces.filter(pk=workspace_id).first() if workspace_id else None
    if workspace is None:
        workspace = workspaces.first()
        if workspace:
            request.session["active_workspace_id"] = workspace.pk
    return workspace

class WorkspaceMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            self.workspace = get_active_workspace(request)
            if self.workspace is None:
                messages.warning(request, "Você ainda não participa de nenhum espaço financeiro.")
                return redirect("admin:index")
        return super().dispatch(request, *args, **kwargs)

class TransactionListView(WorkspaceMixin, ListView):
    model = Transaction
    template_name = "finances/transaction_list.html"
    context_object_name = "transactions"
    paginate_by = 20

    def get_queryset(self):
        return Transaction.objects.filter(account__workspace=self.workspace).select_related("account", "category").order_by("-date")



class TransactionCreateView(WorkspaceMixin, SuccessMessageMixin, CreateView):
    model = Transaction
    form_class = TransactionForm
    template_name = "finances/transaction_form.html"
    success_url = reverse_lazy("finances:transaction_list")
    success_message = "Transação “%(description)s” cadastrada com sucesso."

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["workspace"] = self.workspace
        return kwargs


    def form_invalid(self, form):
        messages.error(self.request, "Não foi possível salvar a transação. Corrija os campos destacados.")
        return super().form_invalid(form)

