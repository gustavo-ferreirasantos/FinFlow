from django.contrib import admin

from .models import Transaction, Account, Category, Budget, RecurringTransaction, FinancialGoal, CreditCard, Invoice

# 1 
@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ("name", "type", "initial_balance", "workspace", "created_at")
    list_filter = ("type",)
    search_fields = ("name",)
    readonly_fields = ("created_at",)

    fieldsets = (
        ("Identificação", {"fields": ("workspace", "name", "type")}),
        ("Saldo", {"fields": ("initial_balance",)}),
        ("Informações adicionais", {"fields": ("created_at",), "classes": ("collapse",)}),
    )

# 2
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "type", "workspace")
    list_filter = ("type",)
    search_fields = ("name",)


class InvoiceInline(admin.TabularInline): #inline para cartão de crédito
    model = Invoice
    extra = 1

# 3
@admin.register(CreditCard)
class CreditCardAdmin(admin.ModelAdmin):
    list_display = ("name", "account", "limit", "closing_day", "due_day")
    search_fields = ("name",)
    inlines = [InvoiceInline]

    fieldsets = (
        (None, {"fields": ("account", "name", "limit")}),
        ("Ciclo de fatura", {"fields": ("closing_day", "due_day")}),
    )

# 4
@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ("credit_card", "reference_month", "total_value", "status")
    list_filter = ("status", "credit_card",)
    date_hierarchy = "reference_month"

# 5
@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ("date", "description", "value", "type", "category", "account", "responsible")
    list_filter = ("type", "category", "account", "account__workspace")
    search_fields = ("description",)
    date_hierarchy = "date"
    list_per_page = 25
    list_select_related = ("category", "account", "responsible__user")
    fieldsets = (
        ("Dados da transação", {"fields": ("description", "value","type", "date")}),
        ("Classificação", {"fields": ("category", "account", "responsible")}),
    )


# 6
@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    list_display = ("category", "reference_month", "limit_value", "alert_sent", "workspace")
    list_filter = ("workspace", "reference_month")
#7
@admin.register(FinancialGoal)
class FinancialGoalAdmin(admin.ModelAdmin):
    list_display = ("name", "target_value", "current_value", "deadline", "workspace")
    list_filter = ("workspace", )
    search_fields = ("name",)

# 8
@admin.register(RecurringTransaction)
class RecurringTransactionAdmin(admin.ModelAdmin):
    list_display = ("description", "value", "type", "due_day", "reminder_sent", "workspace")
    list_filter = ("type", "reminder_sent", "workspace")
    search_fields = ("description",)
