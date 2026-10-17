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
