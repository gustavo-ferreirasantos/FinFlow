from django.urls import path
from . import views as views

app_name = "finances"

urlpatterns = [
    path("transacoes/", views.TransactionListView.as_view(), name="transaction_list"),
    path("transacoes/nova/", views.TransactionCreateView.as_view(), name="transaction_create"),
    path("contas/", views.AccountListView.as_view(), name="account_list"),
    path("contas/nova/", views.AccountCreateView.as_view(), name="account_create"),
    path("contas/<int:pk>/editar/", views.AccountUpdateView.as_view(), name="account_update"),
    path("contas/<int:pk>/excluir/", views.AccountDeleteView.as_view(), name="account_delete"),
]