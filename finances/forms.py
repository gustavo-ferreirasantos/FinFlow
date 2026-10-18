from django import forms
from users.models import Profile
from .models import TRANSACTION_TYPES ,Account, Category, Transaction


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


class StatementFilterForm(forms.Form):
    start_date = forms.DateField(label="De", required=False, widget=forms.DateInput(attrs={"type": "date"}))
    end_date = forms.DateField(label="Até", required=False, widget=forms.DateInput(attrs={"type": "date"}))
    account = forms.ModelChoiceField(label="Conta", queryset=Account.objects.none(), required=False, empty_label="Todas as contas")
    category = forms.ModelChoiceField(label="Categoria", queryset=Category.objects.none(), required=False, empty_label="Todas as categorias")
    type = forms.ChoiceField(label="Tipo", required=False, choices=[("", "Todos os tipos"), *TRANSACTION_TYPES.items()])


    def __init__(self, *args, workspace=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["account"].queryset = Account.objects.filter(workspace=workspace)
        self.fields["category"].queryset = Category.objects.filter(workspace=workspace)


    def clean(self):
        cleaned_data = super().clean()
        start = cleaned_data.get("start_date")
        end = cleaned_data.get("end_date")
        if start and end and start > end:
            raise forms.ValidationError("A data inicial não pode ser maior que a data final.")
        return cleaned_data

