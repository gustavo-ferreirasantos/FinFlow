from decimal import Decimal
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.db import models



valor_positivo = MinValueValidator(Decimal("0.01"), "O valor deve ser maior que zero.")
valor_nao_negativo = MinValueValidator(Decimal("0"), "O valor não pode ser negativo.")
dia_do_mes = [
    MinValueValidator(1, "O dia deve estar entre 1 e 31."),
    MaxValueValidator(31, "O dia deve estar entre 1 e 31."),
]

TRANSACTION_TYPES = {
    "R": "Receita",
    "D": "Despesa",
}

# 1 
class Account(models.Model):
    TYPES = {
        "C": "Corrente",
        "P": "Poupança",
        "W": "Carteira",
        "I": "Investimento",
    }

    workspace = models.ForeignKey("users.Workspace", on_delete=models.CASCADE, related_name="accounts", verbose_name="espaço")
    name = models.CharField("nome", max_length=100)
    type = models.CharField("tipo", max_length=1, choices=TYPES, default="C")
    initial_balance = models.DecimalField("saldo inicial", max_digits=12, decimal_places=2, default=0)

    created_at = models.DateTimeField("Data de criação", auto_now_add=True)

    class Meta:
        # Nome que aparece no admin ("Contas" em vez de "Accounts")
        verbose_name = "conta"
        verbose_name_plural = "contas"
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.get_type_display()})"

# 2
class Category(models.Model):
    
    workspace = models.ForeignKey("users.Workspace", on_delete=models.CASCADE, related_name="categories", verbose_name="espaço")
    name = models.CharField("nome", max_length=100)
    type = models.CharField("tipo", max_length=1, choices=TRANSACTION_TYPES)
 
    class Meta:
        verbose_name = "categoria"
        verbose_name_plural = "categorias"
        ordering = ["type", "name"]
 
    def __str__(self):
        return f"{self.name} ({self.get_type_display()})"

# 3
class CreditCard(models.Model):
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name="credit_cards", verbose_name="conta")
    name = models.CharField("nome", max_length=100)
    limit = models.DecimalField("limite", max_digits=12, decimal_places=2, validators=[valor_positivo])
    closing_day = models.PositiveSmallIntegerField("dia de fechamento", validators=dia_do_mes)
    due_day = models.PositiveSmallIntegerField("dia de vencimento", validators=dia_do_mes)

    class Meta:
        verbose_name = "cartão de crédito"
        verbose_name_plural = "cartões de crédito"
        ordering = ["name"]

    def __str__(self):
        return self.name

# 4
class Invoice(models.Model):
    STATUS = {
        "A": "Aberta",
        "F": "Fechada",
        "P": "Paga",
    }

    credit_card = models.ForeignKey(CreditCard, on_delete=models.CASCADE, related_name="invoices", verbose_name="cartão de crédito")
    reference_month = models.DateField("mês de referência")
    total_value = models.DecimalField("valor total", max_digits=12, decimal_places=2, validators=[valor_nao_negativo])
    status = models.CharField("status", max_length=1, choices=STATUS, default="A")

    class Meta:
        verbose_name = "fatura"
        verbose_name_plural = "faturas"
        ordering = ["-reference_month"]

    def __str__(self):
        return f"{self.credit_card.name} - {self.reference_month.strftime('%m/%Y')}"


# 5
class Transaction(models.Model):
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name="transactions", verbose_name="conta")
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="transactions", verbose_name="categoria")
    responsible = models.ForeignKey("users.Profile", on_delete=models.SET_NULL, related_name="transactions", verbose_name="responsável", null=True, blank=True)
    description = models.CharField("descrição", max_length=250)
    type = models.CharField("tipo", max_length=1, choices=TRANSACTION_TYPES)
    date = models.DateField("data")
    value = models.DecimalField("valor", max_digits=12, decimal_places=2, validators=[valor_positivo])

    class Meta:
        verbose_name = "transação"
        verbose_name_plural = "transações"
        ordering = ["-date"]

    def __str__(self):
        return f"{self.date: %d/%m/%Y} - {self.description}"

    def clean(self):
        # Validação entre os campos de categoria e transação
        if self.category_id and self.type and self.category.type != self.type:
            raise ValidationError({"category":  "O tipo da categoria não corresponde ao tipo da transação."})

# 6
class Budget(models.Model):
    workspace = models.ForeignKey("users.Workspace", on_delete=models.CASCADE, related_name="budgets", verbose_name="espaço")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="budgets", verbose_name="categoria", limit_choices_to={"type": "D"})
    limit_value = models.DecimalField("valor limite", max_digits=12, decimal_places=2, validators=[valor_positivo])
    reference_month = models.DateField("mês de referência")
    alert_sent = models.BooleanField("alerta enviado", default=False)

    class Meta:
        verbose_name = "orçamento"
        verbose_name_plural = "orçamentos"
        ordering = ["-reference_month"]

    def __str__(self):
        return f"{self.category.name} - {self.reference_month: %m/%Y}"

# 7 
class FinancialGoal(models.Model):
    workspace = models.ForeignKey("users.Workspace", on_delete=models.CASCADE, related_name="goals", verbose_name="espaço")
    name = models.CharField("nome", max_length=100)
    target_value = models.DecimalField("valor alvo", max_digits=12, decimal_places=2, validators=[valor_positivo])
    current_value = models.DecimalField("valor atual", max_digits=12, decimal_places=2, default=0, validators=[valor_nao_negativo])
    deadline = models.DateField("prazo")

    class Meta:
        verbose_name = "meta financeira"
        verbose_name_plural = "metas financeiras"
        ordering = ["deadline"]

    def __str__(self):
        return self.name

# 8
class RecurringTransaction(models.Model):
    workspace = models.ForeignKey("users.Workspace", on_delete=models.CASCADE, related_name="recurring_transactions", verbose_name="espaço")
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name="recurring_transactions", verbose_name="conta")
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="recurring_transactions", verbose_name="categoria")
    description = models.CharField("descrição", max_length=200)
    value = models.DecimalField("valor", max_digits=12, decimal_places=2, validators=[valor_positivo])
    type = models.CharField("tipo", max_length=1, choices=TRANSACTION_TYPES)
    due_day = models.PositiveSmallIntegerField("dia de vencimento", validators=dia_do_mes)
    reminder_sent = models.BooleanField("lembrete enviado", default=False)

    class Meta:
        verbose_name = "transação recorrente"
        verbose_name_plural = "transações recorrentes"
        ordering = ["due_day"]

    def __str__(self):
        return f"{self.description} - (dia {self.due_day})"
