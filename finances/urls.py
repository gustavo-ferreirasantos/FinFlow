from django.urls import path
from . import views as views

app_name = "finances"

urlpatterns = [
    path("transacoes/", views.TransactionListView.as_view(), name="transaction_list"),
    path("transacoes/nova/", views.TransactionCreateView.as_view(), name="transaction_create"),
    path("extrato/", views.StatementView.as_view(), name="statement"),
    path("contas/", views.AccountListView.as_view(), name="account_list"),
    path("contas/nova/", views.AccountCreateView.as_view(), name="account_create"),
    path("contas/<int:pk>/editar/", views.AccountUpdateView.as_view(), name="account_update"),
    path("contas/<int:pk>/excluir/", views.AccountDeleteView.as_view(), name="account_delete"),
    path("categorias/", views.CategoryListView.as_view(), name="category_list"),
    path("categorias/nova/", views.CategoryCreateView.as_view(), name="category_create"),
    path("categorias/<int:pk>/editar/", views.CategoryUpdateView.as_view(), name="category_update"),
    path("categorias/<int:pk>/excluir/", views.CategoryDeleteView.as_view(), name="category_delete"),
]