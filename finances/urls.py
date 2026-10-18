from django.urls import path
from . import views as views

app_name = "finances"

urlpatterns = [
    path("transacoes/", views.TransactionListView.as_view(), name="transaction_list"),
    path("transacoes/nova/", views.TransactionCreateView.as_view(), name="transaction_create"),
]