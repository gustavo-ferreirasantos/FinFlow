from datetime import timedelta
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, ListView, DeleteView, UpdateView, DetailView, View
from django.db.models import ProtectedError, Sum

from users.models import Workspace
from .forms import (
    TransactionForm, AccountForm, CategoryForm,
    CreditCardForm, BudgetForm, FinancialGoalForm, GoalDepositForm, RecurringTransactionForm,
)
from .models import (
    Transaction, Account, Category,
    CreditCard, Invoice, Budget, FinancialGoal, RecurringTransaction,
)


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


#Mixin para verificar se o usuário está autenticado e se possui um workspace ativo
class WorkspaceMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            self.workspace = get_active_workspace(request)
            if self.workspace is None:
                messages.warning(request, "Você ainda não participa de nenhum espaço financeiro.")
                return redirect("admin:index")
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


# ---------------------------------------------------------------------------
# Pessoa 3 — Planejamento & Crédito (cartões, faturas, orçamentos, metas,
# transações recorrentes)
# ---------------------------------------------------------------------------

def _inicio_mes(data):
    return data.replace(day=1)


def _fim_mes(data):
    return (data.replace(day=1) + timedelta(days=32)).replace(day=1)


#ListView exibe os cartões de crédito do workspace ativo
class CreditCardListView(WorkspaceMixin, ListView):
    model = CreditCard
    template_name = "finances/card_list.html"
    context_object_name = "cards"

    def get_queryset(self):
        return CreditCard.objects.filter(account__workspace=self.workspace).select_related("account")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        itens = []
        for card in context["cards"]:
            faturas_abertas = card.invoices.filter(status="A").order_by("-reference_month")
            total_aberto = sum((invoice.total_value for invoice in faturas_abertas), Decimal("0"))
            itens.append({
                "card": card,
                "faturas_abertas": faturas_abertas,
                "total_aberto": total_aberto,
            })
        context["itens"] = itens
        context["total_limite"] = sum((card.limit for card in context["cards"]), Decimal("0"))
        return context


#CreateView cria um novo cartão de crédito
class CreditCardCreateView(WorkspaceMixin, SuccessMessageMixin, CreateView):
    model = CreditCard
    form_class = CreditCardForm
    template_name = "finances/card_form.html"
    success_url = reverse_lazy("finances:card_list")
    success_message = "Cartão “%(name)s” criado com sucesso."

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["workspace"] = self.workspace
        return kwargs

    def form_invalid(self, form):
        messages.error(self.request, "Não foi possível salvar o cartão. Corrija os campos destacados.")
        return super().form_invalid(form)


#DetailView exibe a fatura e os lançamentos do mês de referência
class InvoiceDetailView(WorkspaceMixin, DetailView):
    model = Invoice
    template_name = "finances/invoice_detail.html"
    context_object_name = "invoice"

    def get_queryset(self):
        return Invoice.objects.filter(credit_card__account__workspace=self.workspace).select_related(
            "credit_card", "credit_card__account"
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        invoice = self.object
        inicio = _inicio_mes(invoice.reference_month)
        fim = _fim_mes(invoice.reference_month)
        context["lancamentos"] = (
            Transaction.objects.filter(
                account=invoice.credit_card.account, date__gte=inicio, date__lt=fim
            )
            .select_related("category")
            .order_by("date")
        )
        return context


#View (POST) paga a fatura: marca como paga e registra a despesa na conta
class PayInvoiceView(WorkspaceMixin, View):
    def post(self, request, pk):
        invoice = get_object_or_404(
            Invoice, pk=pk, credit_card__account__workspace=self.workspace
        )

        if invoice.status == "P":
            messages.warning(request, "Esta fatura já está paga.")
            return redirect("finances:invoice_detail", pk=invoice.pk)

        if invoice.total_value <= 0:
            messages.warning(request, "Faturas com valor zero não podem ser pagas.")
            return redirect("finances:invoice_detail", pk=invoice.pk)

        conta = invoice.credit_card.account
        categoria, _ = Category.objects.get_or_create(
            workspace=self.workspace, name="Pagamento de Fatura", type="D"
        )
        Transaction.objects.create(
            account=conta,
            category=categoria,
            responsible=getattr(request.user, "profile", None),
            description=f"Pagamento da fatura de {invoice.credit_card.name} "
                        f"({invoice.reference_month:%m/%Y})",
            type="D",
            date=timezone.localdate(),
            value=invoice.total_value,
        )
        invoice.status = "P"
        invoice.save(update_fields=["status"])

        messages.success(
            request,
            f"Fatura de {invoice.credit_card.name} ({invoice.reference_month:%m/%Y}) paga com sucesso.",
        )
        return redirect("finances:invoice_detail", pk=invoice.pk)


#ListView exibe os orçamentos com o gasto do mês e o nível de alerta
class BudgetListView(WorkspaceMixin, ListView):
    model = Budget
    template_name = "finances/budget_list.html"
    context_object_name = "budgets"

    def get_queryset(self):
        return (
            Budget.objects.filter(workspace=self.workspace)
            .select_related("category")
            .order_by("-reference_month", "category__name")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        itens = []
        for budget in context["budgets"]:
            inicio = _inicio_mes(budget.reference_month)
            fim = _fim_mes(budget.reference_month)
            gasto = (
                Transaction.objects.filter(
                    category=budget.category, type="D", date__gte=inicio, date__lt=fim
                ).aggregate(total=Sum("value"))["total"]
                or Decimal("0")
            )
            limite = budget.limit_value or Decimal("0")
            percentual = round(float(gasto / limite * 100), 1) if limite > 0 else 0.0
            if percentual > 100:
                nivel, classe = "Estourado", "alerta-vermelho"
            elif percentual >= 80:
                nivel, classe = "Atenção", "alerta-amarelo"
            else:
                nivel, classe = "Normal", "alerta-verde"
            itens.append({
                "budget": budget,
                "gasto": gasto,
                "percentual": percentual,
                "percentual_barra": min(percentual, 100),
                "nivel": nivel,
                "classe": classe,
            })
        context["itens"] = itens
        return context


#CreateView cria um novo orçamento (apenas para categorias de despesa)
class BudgetCreateView(WorkspaceMixin, SuccessMessageMixin, CreateView):
    model = Budget
    form_class = BudgetForm
    template_name = "finances/budget_form.html"
    success_url = reverse_lazy("finances:budget_list")
    success_message = "Orçamento de “%(category)s” criado com sucesso."

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["workspace"] = self.workspace
        return kwargs

    def form_valid(self, form):
        form.instance.workspace = self.workspace
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "Não foi possível salvar o orçamento. Corrija os campos destacados.")
        return super().form_invalid(form)


#DeleteView exclui um orçamento existente
class BudgetDeleteView(WorkspaceMixin, DeleteView):
    model = Budget
    template_name = "finances/budget_confirm_delete.html"
    success_url = reverse_lazy("finances:budget_list")

    def get_queryset(self):
        return Budget.objects.filter(workspace=self.workspace)

    def form_valid(self, form):
        messages.success(self.request, f"Orçamento de “{self.object.category}” excluído.")
        return super().form_valid(form)


#ListView exibe as metas com a barra de progresso e o formulário de aporte
class FinancialGoalListView(WorkspaceMixin, ListView):
    model = FinancialGoal
    template_name = "finances/goal_list.html"
    context_object_name = "goals"

    def get_queryset(self):
        return FinancialGoal.objects.filter(workspace=self.workspace).order_by("deadline", "name")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        itens = []
        for goal in context["goals"]:
            percentual = (
                round(float(goal.current_value / goal.target_value * 100), 1)
                if goal.target_value > 0
                else 0.0
            )
            itens.append({
                "goal": goal,
                "percentual": percentual,
                "percentual_barra": min(percentual, 100),
                "form_aporte": GoalDepositForm(),
            })
        context["itens"] = itens
        return context


#CreateView cria uma nova meta financeira
class FinancialGoalCreateView(WorkspaceMixin, SuccessMessageMixin, CreateView):
    model = FinancialGoal
    form_class = FinancialGoalForm
    template_name = "finances/goal_form.html"
    success_url = reverse_lazy("finances:goal_list")
    success_message = "Meta “%(name)s” criada com sucesso."

    def form_valid(self, form):
        form.instance.workspace = self.workspace
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "Não foi possível salvar a meta. Corrija os campos destacados.")
        return super().form_invalid(form)


#View (POST) registra um aporte na meta
class GoalDepositView(WorkspaceMixin, View):
    def post(self, request, pk):
        goal = get_object_or_404(FinancialGoal, pk=pk, workspace=self.workspace)
        form = GoalDepositForm(request.POST)
        if form.is_valid():
            valor = form.cleaned_data["value"]
            goal.current_value += valor
            goal.save(update_fields=["current_value"])
            messages.success(
                request, f"Aporte de R$ {valor} registrado na meta “{goal.name}”."
            )
        else:
            messages.error(request, "Não foi possível registrar o aporte. Informe um valor válido.")
        return redirect("finances:goal_list")


#DeleteView exclui uma meta financeira existente
class FinancialGoalDeleteView(WorkspaceMixin, DeleteView):
    model = FinancialGoal
    template_name = "finances/goal_confirm_delete.html"
    success_url = reverse_lazy("finances:goal_list")

    def get_queryset(self):
        return FinancialGoal.objects.filter(workspace=self.workspace)

    def form_valid(self, form):
        messages.success(self.request, f"Meta “{self.object.name}” excluída.")
        return super().form_valid(form)


#ListView exibe as transações recorrentes do workspace ativo
class RecurringTransactionListView(WorkspaceMixin, ListView):
    model = RecurringTransaction
    template_name = "finances/recurring_list.html"
    context_object_name = "recurrences"

    def get_queryset(self):
        return (
            RecurringTransaction.objects.filter(workspace=self.workspace)
            .select_related("account", "category")
            .order_by("due_day", "description")
        )


#CreateView cria uma nova transação recorrente
class RecurringTransactionCreateView(WorkspaceMixin, SuccessMessageMixin, CreateView):
    model = RecurringTransaction
    form_class = RecurringTransactionForm
    template_name = "finances/recurring_form.html"
    success_url = reverse_lazy("finances:recurring_list")
    success_message = "Transação recorrente “%(description)s” criada com sucesso."

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["workspace"] = self.workspace
        return kwargs

    def form_valid(self, form):
        form.instance.workspace = self.workspace
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "Não foi possível salvar a transação recorrente. Corrija os campos destacados.")
        return super().form_invalid(form)


#DeleteView exclui uma transação recorrente existente
class RecurringTransactionDeleteView(WorkspaceMixin, DeleteView):
    model = RecurringTransaction
    template_name = "finances/recurring_confirm_delete.html"
    success_url = reverse_lazy("finances:recurring_list")

    def get_queryset(self):
        return RecurringTransaction.objects.filter(workspace=self.workspace)

    def form_valid(self, form):
        messages.success(self.request, f"Transação recorrente “{self.object.description}” excluída.")
        return super().form_valid(form)



