from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, DeleteView, UpdateView
from django.db.models import ProtectedError

from users.models import Workspace
from .forms import TransactionForm, AccountForm, CategoryForm
from .models import Transaction, Account, Category
from users.utils import get_active_workspace


# # TEMPORÁRIO: trocar pelo get_active_workspace do users/utils.py
# def get_active_workspace(request):
#     workspaces = Workspace.objects.filter(workspacemember__profile__user=request.user)
#     workspace_id = request.session.get("active_workspace_id")
#     workspace = workspaces.filter(pk=workspace_id).first() if workspace_id else None
#     if workspace is None:
#         workspace = workspaces.first()
#         if workspace:
#             request.session["active_workspace_id"] = workspace.pk
#     return workspace


#Mixin para verificar se o usuário está autenticado e se possui um workspace ativo
class WorkspaceMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            self.workspace = get_active_workspace(request)
            if self.workspace is None:
                messages.warning(request, "Você ainda não participa de nenhum espaço financeiro.")
                return redirect("users:workspace_list")
                # return redirect("admin:index")
        return super().dispatch(request, *args, **kwargs)


#ListView exibe a lista de transações do workspace ativo
class TransactionListView(WorkspaceMixin, ListView):
    model = Transaction
    template_name = "finances/transaction_list.html"
    context_object_name = "transactions"
    paginate_by = 20

    def get_queryset(self):
        return Transaction.objects.filter(account__workspace=self.workspace).select_related("account", "category").order_by("-date")



#CreateView cria uma nova transação
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



#UpdateView atualiza uma contas existente
class AccountListView(WorkspaceMixin, ListView):
    model = Account
    template_name = "finances/account_list.html"
    context_object_name = "accounts"

    def get_queryset(self):
        return Account.objects.filter(workspace=self.workspace)
    


#CreateView cria uma nova conta
class AccountCreateView(WorkspaceMixin, SuccessMessageMixin, CreateView):
    model = Account
    form_class = AccountForm
    template_name = "finances/account_form.html"
    success_url = reverse_lazy("finances:account_list")
    success_message = "Conta “%(name)s” criada com sucesso."


    def form_valid(self, form):
        form.instance.workspace = self.workspace
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "Não foi possível salvar a conta. Corrija os campos destacados.")
        return super().form_invalid(form)



#UpdateView atualiza uma conta existente
class AccountUpdateView(WorkspaceMixin, SuccessMessageMixin, UpdateView):
    model = Account
    form_class = AccountForm
    template_name = "finances/account_form.html"
    success_url = reverse_lazy("finances:account_list")
    success_message = "Conta “%(name)s” atualizada com sucesso."

    def get_queryset(self):
        return Account.objects.filter(workspace=self.workspace)

    def form_invalid(self, form):
        messages.error(self.request, "Não foi possível salvar a conta. Corrija os campos destacados.")
        return super().form_invalid(form)



#DeleteView exclui uma conta existente
class AccountDeleteView(WorkspaceMixin, DeleteView):
    model = Account
    template_name = "finances/account_confirm_delete.html"
    success_url = reverse_lazy("finances:account_list")

    def get_queryset(self):
        return Account.objects.filter(workspace=self.workspace)

    def form_valid(self, form):
        messages.success(self.request, f"Conta “{self.object.name}” excluída.")
        return super().form_valid(form)    


#ListView exibe a lista de categorias do workspace ativo
class CategoryListView(WorkspaceMixin, ListView):
    model = Category
    template_name = "finances/category_list.html"
    context_object_name = "categories"

    def get_queryset(self):
        # "-type" coloca Receita "R" antes de Despesa "D"
        return Category.objects.filter(workspace=self.workspace).order_by("-type", "name")



#CreateView cria uma nova categoria
class CategoryCreateView(WorkspaceMixin, SuccessMessageMixin, CreateView):
    model = Category
    form_class = CategoryForm
    template_name = "finances/category_form.html"
    success_url = reverse_lazy("finances:category_list")
    success_message = "Categoria “%(name)s” criada com sucesso."

    def form_valid(self, form):
        form.instance.workspace = self.workspace
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "Não foi possível salvar a categoria. Corrija os campos destacados.")
        return super().form_invalid(form)



#UpdateView atualiza uma categoria existente
class CategoryUpdateView(WorkspaceMixin, SuccessMessageMixin, UpdateView):
    model = Category
    form_class = CategoryForm
    template_name = "finances/category_form.html"
    success_url = reverse_lazy("finances:category_list")
    success_message = "Categoria “%(name)s” atualizada com sucesso."

    def get_queryset(self):
        return Category.objects.filter(workspace=self.workspace)

    def form_invalid(self, form):
        messages.error(self.request, "Não foi possível salvar a categoria. Corrija os campos destacados.")
        return super().form_invalid(form)



#DeleteView exclui uma categoria existente
class CategoryDeleteView(WorkspaceMixin, DeleteView):
    model = Category
    template_name = "finances/category_confirm_delete.html"
    success_url = reverse_lazy("finances:category_list")

    def get_queryset(self):
        return Category.objects.filter(workspace=self.workspace)

    def form_valid(self, form):
        try:
            response = super().form_valid(form)
        except ProtectedError:
            messages.error(self.request, f"A categoria “{self.object.name}” não pode ser excluída porque há transações ou recorrências que a usam.",)
            return redirect("finances:category_list")
        messages.success(self.request, f"Categoria “{self.object.name}” excluída.")
        return response



