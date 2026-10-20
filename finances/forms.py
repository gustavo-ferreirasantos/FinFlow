from decimal import Decimal
from django import forms
from users.models import Profile
from .models import Account, Category, Transaction


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


# Formulário do Simulador Público (Regra 50/30/20)
class SimulatorForm(forms.Form):
    monthly_income = forms.DecimalField(
        label="Renda Mensal Líquida (R$)",
        max_digits=12,
        decimal_places=2,
        min_value=Decimal("0.01"),
        widget=forms.NumberInput(attrs={"class": "form-control", "placeholder": "Ex: 5000.00", "step": "0.01"}),
    )
    housing_expense = forms.DecimalField(
        label="Moradia (Aluguel, luz, água, internet)",
        max_digits=12,
        decimal_places=2,
        min_value=Decimal("0.00"),
        required=False,
        initial=Decimal("0.00"),
        widget=forms.NumberInput(attrs={"class": "form-control", "placeholder": "0.00", "step": "0.01"}),
    )
    food_expense = forms.DecimalField(
        label="Alimentação (Mercado, feira)",
        max_digits=12,
        decimal_places=2,
        min_value=Decimal("0.00"),
        required=False,
        initial=Decimal("0.00"),
        widget=forms.NumberInput(attrs={"class": "form-control", "placeholder": "0.00", "step": "0.01"}),
    )
    transport_expense = forms.DecimalField(
        label="Transporte (Combustível, ônibus, Uber)",
        max_digits=12,
        decimal_places=2,
        min_value=Decimal("0.00"),
        required=False,
        initial=Decimal("0.00"),
        widget=forms.NumberInput(attrs={"class": "form-control", "placeholder": "0.00", "step": "0.01"}),
    )
    leisure_expense = forms.DecimalField(
        label="Lazer (Restaurantes, passeios, streaming)",
        max_digits=12,
        decimal_places=2,
        min_value=Decimal("0.00"),
        required=False,
        initial=Decimal("0.00"),
        widget=forms.NumberInput(attrs={"class": "form-control", "placeholder": "0.00", "step": "0.01"}),
    )
    other_expenses = forms.DecimalField(
        label="Outros gastos (Compras, assinaturas diversas)",
        max_digits=12,
        decimal_places=2,
        min_value=Decimal("0.00"),
        required=False,
        initial=Decimal("0.00"),
        widget=forms.NumberInput(attrs={"class": "form-control", "placeholder": "0.00", "step": "0.01"}),
    )

    def clean(self):
        cleaned_data = super().clean()
        # Se algum campo de despesa ficar em branco, define como 0.00 para não quebrar o cálculo
        campos_despesa = [
            "housing_expense",
            "food_expense",
            "transport_expense",
            "leisure_expense",
            "other_expenses",
        ]
        for campo in campos_despesa:
            if cleaned_data.get(campo) is None:
                cleaned_data[campo] = Decimal("0.00")
        return cleaned_data
