from django import forms
from users.models import Profile
from .models import Account, Category, Transaction, CreditCard, Budget, FinancialGoal, RecurringTransaction


class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ["description", "value", "type", "date", "account", "category", "responsible"]
        widgets = {
                #type="date" mostra o calendário do navegador; o format garante que a data apareça preenchida ao editar uma transação
                "date": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            }


    def __init__(self, *args, workspace = None, **kwargs):
        super().__init__(*args, **kwargs)

        # Só mostra e aceita registros do workspace ativo
        self.fields["account"].queryset = Account.objects.filter(workspace=workspace)
        self.fields["category"].queryset = Category.objects.filter(workspace=workspace)
        self.fields["responsible"].queryset = Profile.objects.filter(workspacemember__workspace=workspace).distinct()


class AccountForm(forms.ModelForm):
    class Meta:
        model = Account
        fields = ["name", "type", "initial_balance"]


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ["name", "type"]


# ---------------------------------------------------------------------------
# Pessoa 3 — Planejamento & Crédito: Cartões, Orçamentos, Metas e Recorrentes
# ---------------------------------------------------------------------------

class CreditCardForm(forms.ModelForm):
    class Meta:
        model = CreditCard
        fields = ["name", "account", "limit", "closing_day", "due_day"]
        widgets = {
            "closing_day": forms.NumberInput(attrs={"min": 1, "max": 31}),
            "due_day": forms.NumberInput(attrs={"min": 1, "max": 31}),
        }

    def __init__(self, *args, workspace=None, **kwargs):
        super().__init__(*args, **kwargs)
        # Só mostra contas do workspace ativo
        self.fields["account"].queryset = Account.objects.filter(workspace=workspace)


class BudgetForm(forms.ModelForm):
    class Meta:
        model = Budget
        fields = ["category", "limit_value", "reference_month"]
        widgets = {
            # type="month" mostra o seletor de mês do navegador
            "reference_month": forms.DateInput(attrs={"type": "month"}, format="%Y-%m-%d"),
        }

    def __init__(self, *args, workspace=None, **kwargs):
        super().__init__(*args, **kwargs)
        # Orçamento só pode ser criado para categorias de DESPESA do workspace ativo
        self.fields["category"].queryset = Category.objects.filter(workspace=workspace, type="D")


class FinancialGoalForm(forms.ModelForm):
    class Meta:
        model = FinancialGoal
        fields = ["name", "target_value", "current_value", "deadline"]
        widgets = {
            "deadline": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
        }


class GoalDepositForm(forms.Form):
    # Form comum (não é ModelForm): apenas registra o valor do aporte
    value = forms.DecimalField(
        label="Valor do aporte",
        max_digits=12,
        decimal_places=2,
        widget=forms.NumberInput(attrs={"step": "0.01"}),
    )


class RecurringTransactionForm(forms.ModelForm):
    class Meta:
        model = RecurringTransaction
        fields = ["description", "value", "type", "account", "category", "due_day"]
        widgets = {
            "due_day": forms.NumberInput(attrs={"min": 1, "max": 31}),
        }

    def __init__(self, *args, workspace=None, **kwargs):
        super().__init__(*args, **kwargs)
        # Só mostra registros do workspace ativo
        self.fields["account"].queryset = Account.objects.filter(workspace=workspace)
        self.fields["category"].queryset = Category.objects.filter(workspace=workspace)

