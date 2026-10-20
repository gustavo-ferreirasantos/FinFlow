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
    path("categorias/", views.CategoryListView.as_view(), name="category_list"),
    path("categorias/nova/", views.CategoryCreateView.as_view(), name="category_create"),
    path("categorias/<int:pk>/editar/", views.CategoryUpdateView.as_view(), name="category_update"),
    path("categorias/<int:pk>/excluir/", views.CategoryDeleteView.as_view(), name="category_delete"),

    # Pessoa 3 — Planejamento & Crédito
    path("cartoes/", views.CreditCardListView.as_view(), name="card_list"),
    path("cartoes/novo/", views.CreditCardCreateView.as_view(), name="card_create"),
    path("faturas/<int:pk>/", views.InvoiceDetailView.as_view(), name="invoice_detail"),
    path("faturas/<int:pk>/pagar/", views.PayInvoiceView.as_view(), name="invoice_pay"),
    path("orcamentos/", views.BudgetListView.as_view(), name="budget_list"),
    path("orcamentos/novo/", views.BudgetCreateView.as_view(), name="budget_create"),
    path("orcamentos/<int:pk>/excluir/", views.BudgetDeleteView.as_view(), name="budget_delete"),
    path("metas/", views.FinancialGoalListView.as_view(), name="goal_list"),
    path("metas/nova/", views.FinancialGoalCreateView.as_view(), name="goal_create"),
    path("metas/<int:pk>/aporte/", views.GoalDepositView.as_view(), name="goal_deposit"),
    path("metas/<int:pk>/excluir/", views.FinancialGoalDeleteView.as_view(), name="goal_delete"),
    path("recorrentes/", views.RecurringTransactionListView.as_view(), name="recurring_list"),
    path("recorrentes/nova/", views.RecurringTransactionCreateView.as_view(), name="recurring_create"),
    path("recorrentes/<int:pk>/excluir/", views.RecurringTransactionDeleteView.as_view(), name="recurring_delete"),
]