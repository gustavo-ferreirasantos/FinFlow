import json
from datetime import date
from decimal import Decimal
from urllib.request import Request, urlopen

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, DeleteView, UpdateView, TemplateView
from django.db.models import ProtectedError, Sum

from users.models import Workspace
from .forms import TransactionForm, AccountForm, CategoryForm, SimulatorForm
from .models import (
    Transaction,
    Account,
    Category,
    Budget,
    FinancialGoal,
    RecurringTransaction,
)
from users.utils import get_active_workspace


# # TEMPORÁRIO: trocar pelo get_active_workspace do users/utils.py
# def get_active_workspace(request):
#     workspaces = Workspace.objects.filter(workspacemember__profile__user=request.user)
#     workspace_id = request.session.get("active_workspace_id")
#     workspace = workspaces.filter(pk=workspace_id).first() if workspace_id else None
#     if workspace is None:
#         workspace = workspaces.first()
#         if workspace:
#             request.session["active_workspace_id"] = workspace.pk
#     return workspace


#Mixin para verificar se o usuário está autenticado e se possui um workspace ativo
class WorkspaceMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            self.workspace = get_active_workspace(request)
            if self.workspace is None:
                messages.warning(request, "Você ainda não participa de nenhum espaço financeiro.")
                return redirect("users:workspace_list")
                # return redirect("admin:index")
        return super().dispatch(request, *args, **kwargs)


#ListView exibe a lista de transações do workspace ativo
class TransactionListView(WorkspaceMixin, ListView):
    model = Transaction
    template_name = "finances/transaction_list.html"
    context_object_name = "transactions"
    paginate_by = 20

    def get_queryset(self):
        return Transaction.objects.filter(account__workspace=self.workspace).select_related("account", "category").order_by("-date")



#CreateView cria uma nova transação
class TransactionCreateView(WorkspaceMixin, SuccessMessageMixin, CreateView):
    model = Transaction
    form_class = TransactionForm
    template_name = "finances/transaction_form.html"
    success_url = reverse_lazy("finances:transaction_list")
    success_message = "Transação “%(description)s” cadastrada com sucesso."

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["workspace"] = self.workspace
        return kwargs


    def form_invalid(self, form):
        messages.error(self.request, "Não foi possível salvar a transação. Corrija os campos destacados.")
        return super().form_invalid(form)



#UpdateView atualiza uma contas existente
class AccountListView(WorkspaceMixin, ListView):
    model = Account
    template_name = "finances/account_list.html"
    context_object_name = "accounts"

    def get_queryset(self):
        return Account.objects.filter(workspace=self.workspace)
    


#CreateView cria uma nova conta
class AccountCreateView(WorkspaceMixin, SuccessMessageMixin, CreateView):
    model = Account
    form_class = AccountForm
    template_name = "finances/account_form.html"
    success_url = reverse_lazy("finances:account_list")
    success_message = "Conta “%(name)s” criada com sucesso."


    def form_valid(self, form):
        form.instance.workspace = self.workspace
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "Não foi possível salvar a conta. Corrija os campos destacados.")
        return super().form_invalid(form)



#UpdateView atualiza uma conta existente
class AccountUpdateView(WorkspaceMixin, SuccessMessageMixin, UpdateView):
    model = Account
    form_class = AccountForm
    template_name = "finances/account_form.html"
    success_url = reverse_lazy("finances:account_list")
    success_message = "Conta “%(name)s” atualizada com sucesso."

    def get_queryset(self):
        return Account.objects.filter(workspace=self.workspace)

    def form_invalid(self, form):
        messages.error(self.request, "Não foi possível salvar a conta. Corrija os campos destacados.")
        return super().form_invalid(form)



#DeleteView exclui uma conta existente
class AccountDeleteView(WorkspaceMixin, DeleteView):
    model = Account
    template_name = "finances/account_confirm_delete.html"
    success_url = reverse_lazy("finances:account_list")

    def get_queryset(self):
        return Account.objects.filter(workspace=self.workspace)

    def form_valid(self, form):
        messages.success(self.request, f"Conta “{self.object.name}” excluída.")
        return super().form_valid(form)    


#ListView exibe a lista de categorias do workspace ativo
class CategoryListView(WorkspaceMixin, ListView):
    model = Category
    template_name = "finances/category_list.html"
    context_object_name = "categories"

    def get_queryset(self):
        # "-type" coloca Receita "R" antes de Despesa "D"
        return Category.objects.filter(workspace=self.workspace).order_by("-type", "name")



#CreateView cria uma nova categoria
class CategoryCreateView(WorkspaceMixin, SuccessMessageMixin, CreateView):
    model = Category
    form_class = CategoryForm
    template_name = "finances/category_form.html"
    success_url = reverse_lazy("finances:category_list")
    success_message = "Categoria “%(name)s” criada com sucesso."

    def form_valid(self, form):
        form.instance.workspace = self.workspace
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "Não foi possível salvar a categoria. Corrija os campos destacados.")
        return super().form_invalid(form)



#UpdateView atualiza uma categoria existente
class CategoryUpdateView(WorkspaceMixin, SuccessMessageMixin, UpdateView):
    model = Category
    form_class = CategoryForm
    template_name = "finances/category_form.html"
    success_url = reverse_lazy("finances:category_list")
    success_message = "Categoria “%(name)s” atualizada com sucesso."

    def get_queryset(self):
        return Category.objects.filter(workspace=self.workspace)

    def form_invalid(self, form):
        messages.error(self.request, "Não foi possível salvar a categoria. Corrija os campos destacados.")
        return super().form_invalid(form)



#DeleteView exclui uma categoria existente
class CategoryDeleteView(WorkspaceMixin, DeleteView):
    model = Category
    template_name = "finances/category_confirm_delete.html"
    success_url = reverse_lazy("finances:category_list")

    def get_queryset(self):
        return Category.objects.filter(workspace=self.workspace)

    def form_valid(self, form):
        try:
            response = super().form_valid(form)
        except ProtectedError:
            messages.error(self.request, f"A categoria “{self.object.name}” não pode ser excluída porque há transações ou recorrências que a usam.",)
            return redirect("finances:category_list")
        messages.success(self.request, f"Categoria “{self.object.name}” excluída.")
        return response


# ==============================================================================
# PESSOA 4 — Dashboard Analítico, Simulador Público (50/30/20) e Cotações API
# ==============================================================================

# Dashboard principal do espaço financeiro ativo
class DashboardView(WorkspaceMixin, TemplateView):
    template_name = "finances/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        ws = self.workspace
        hoje = date.today()

        # 1. Patrimônio Líquido / Saldo Consolidado
        # Soma os saldos iniciais de todas as contas + todas as receitas - todas as despesas
        saldo_inicial_contas = (
            Account.objects.filter(workspace=ws).aggregate(total=Sum("initial_balance"))["total"]
            or Decimal("0.00")
        )
        total_receitas_geral = (
            Transaction.objects.filter(account__workspace=ws, type="R").aggregate(total=Sum("value"))["total"]
            or Decimal("0.00")
        )
        total_despesas_geral = (
            Transaction.objects.filter(account__workspace=ws, type="D").aggregate(total=Sum("value"))["total"]
            or Decimal("0.00")
        )
        patrimonio_liquido = saldo_inicial_contas + total_receitas_geral - total_despesas_geral

        # 2. Resultados do Mês Atual
        transacoes_mes = Transaction.objects.filter(
            account__workspace=ws,
            date__year=hoje.year,
            date__month=hoje.month,
        )
        receitas_mes = (
            transacoes_mes.filter(type="R").aggregate(total=Sum("value"))["total"]
            or Decimal("0.00")
        )
        despesas_mes = (
            transacoes_mes.filter(type="D").aggregate(total=Sum("value"))["total"]
            or Decimal("0.00")
        )
        saldo_mes = receitas_mes - despesas_mes

        # 3. Últimas transações cadastradas no espaço
        ultimas_transacoes = (
            Transaction.objects.filter(account__workspace=ws)
            .select_related("account", "category")
            .order_by("-date", "-id")[:6]
        )

        # 4. Orçamentos com cálculo de consumo e alerta (Normal / Atenção / Estourado)
        orcamentos_qs = Budget.objects.filter(workspace=ws).select_related("category")[:6]
        orcamentos_resumo = []
        for orc in orcamentos_qs:
            gasto_cat = (
                Transaction.objects.filter(
                    account__workspace=ws,
                    category=orc.category,
                    type="D",
                    date__year=orc.reference_month.year,
                    date__month=orc.reference_month.month,
                ).aggregate(total=Sum("value"))["total"]
                or Decimal("0.00")
            )
            percentual = (gasto_cat / orc.limit_value * Decimal("100")) if orc.limit_value > 0 else Decimal("0.00")

            if percentual > 100:
                status_label = "Estourado"
                cor_badge = "danger"
            elif percentual >= 80:
                status_label = "Atenção"
                cor_badge = "warning"
            else:
                status_label = "Normal"
                cor_badge = "success"

            orcamentos_resumo.append({
                "categoria": orc.category.name,
                "mes": orc.reference_month,
                "limite": orc.limit_value,
                "gasto": gasto_cat,
                "percentual": round(percentual, 1),
                "largura_barra": min(int(percentual), 100),
                "status_label": status_label,
                "cor": cor_badge,
            })

        # 5. Próximos vencimentos de transações recorrentes
        recorrentes = (
            RecurringTransaction.objects.filter(workspace=ws)
            .select_related("account", "category")
            .order_by("due_day")[:6]
        )

        # 6. Progresso das metas financeiras ativas
        metas_qs = FinancialGoal.objects.filter(workspace=ws).order_by("deadline")[:5]
        metas_resumo = []
        for meta in metas_qs:
            perc_meta = (
                (meta.current_value / meta.target_value * Decimal("100"))
                if meta.target_value > 0
                else Decimal("0.00")
            )
            metas_resumo.append({
                "nome": meta.name,
                "atual": meta.current_value,
                "alvo": meta.target_value,
                "prazo": meta.deadline,
                "percentual": round(perc_meta, 1),
                "largura_barra": min(int(perc_meta), 100),
            })

        context.update({
            "patrimonio_liquido": patrimonio_liquido,
            "saldo_inicial_contas": saldo_inicial_contas,
            "receitas_mes": receitas_mes,
            "despesas_mes": despesas_mes,
            "saldo_mes": saldo_mes,
            "mes_atual": hoje,
            "ultimas_transacoes": ultimas_transacoes,
            "orcamentos_resumo": orcamentos_resumo,
            "recorrentes": recorrentes,
            "metas_resumo": metas_resumo,
        })
        return context


# Simulador Público 50/30/20 (acessível sem login)
class SimulatorView(TemplateView):
    template_name = "finances/simulator.html"

    def get(self, request, *args, **kwargs):
        form = SimulatorForm()
        return render(request, self.template_name, {"form": form})

    def post(self, request, *args, **kwargs):
        form = SimulatorForm(request.POST)
        resultado = None

        if form.is_valid():
            renda = form.cleaned_data["monthly_income"]
            moradia = form.cleaned_data["housing_expense"]
            alimentacao = form.cleaned_data["food_expense"]
            transporte = form.cleaned_data["transport_expense"]
            lazer = form.cleaned_data["leisure_expense"]
            outros = form.cleaned_data["other_expenses"]

            # Agrupamento pela regra 50/30/20
            necessidades = moradia + alimentacao + transporte
            desejos = lazer + outros
            total_gastos = necessidades + desejos
            poupanca_restante = renda - total_gastos

            # Valores ideais recomendados para a renda informada
            ideal_necessidades = renda * Decimal("0.50")
            ideal_desejos = renda * Decimal("0.30")
            ideal_poupanca = renda * Decimal("0.20")

            # Percentuais reais sobre a renda líquida
            perc_necessidades = round((necessidades / renda) * Decimal("100"), 1)
            perc_desejos = round((desejos / renda) * Decimal("100"), 1)
            perc_poupanca = round((poupanca_restante / renda) * Decimal("100"), 1)

            # Geração de alertas e dicas de acordo com o diagnóstico
            alertas = []
            superendividado = total_gastos > renda

            if superendividado:
                deficit = total_gastos - renda
                alertas.append({
                    "tipo": "danger",
                    "titulo": "Alerta de Superendividamento!",
                    "texto": f"Seus gastos totais superam sua renda líquida em R$ {deficit:.2f}. É urgente cortar despesas não essenciais para evitar dívidas com juros altos.",
                })

            if perc_necessidades > 50:
                alertas.append({
                    "tipo": "warning",
                    "titulo": "Gastos Essenciais Acima de 50%",
                    "texto": f"Suas necessidades básicas consomem {perc_necessidades}% da renda (o ideal é até 50%). Avalie renegociar contas fixas ou otimizar compras de supermercado e transporte.",
                })
            else:
                alertas.append({
                    "tipo": "success",
                    "titulo": "Necessidades Sob Controle",
                    "texto": f"Muito bem! Seus gastos essenciais representam {perc_necessidades}% da renda, dentro do limite recomendado de 50%.",
                })

            if perc_desejos > 30:
                alertas.append({
                    "tipo": "warning",
                    "titulo": "Estilo de Vida e Lazer Acima de 30%",
                    "texto": f"Seus gastos com desejos e estilo de vida estão em {perc_desejos}% da renda (o recomendado é até 30%). Reduzir assinaturas pouco usadas e pedidos de delivery pode liberar margem no orçamento.",
                })
            else:
                alertas.append({
                    "tipo": "success",
                    "titulo": "Gastos com Estilo de Vida Equilibrados",
                    "texto": f"Seus desejos consomem {perc_desejos}% da renda, respeitando o teto saudável de 30%.",
                })

            if perc_poupanca < 20:
                alertas.append({
                    "tipo": "info",
                    "titulo": "Meta de Poupança Abaixo de 20%",
                    "texto": f"Atualmente sobram {perc_poupanca}% para investir (meta recomendada: pelo menos 20%, ou R$ {ideal_poupanca:.2f}). Tente separar o valor de investimento assim que receber o salário.",
                })
            else:
                alertas.append({
                    "tipo": "success",
                    "titulo": "Excelente Capacidade de Poupança!",
                    "texto": f"Você consegue reservar {perc_poupanca}% da sua renda (R$ {poupanca_restante:.2f}) para investimentos e metas futuras.",
                })

            resultado = {
                "renda": renda,
                "total_gastos": total_gastos,
                "necessidades": necessidades,
                "desejos": desejos,
                "poupanca": poupanca_restante,
                "ideal_necessidades": ideal_necessidades,
                "ideal_desejos": ideal_desejos,
                "ideal_poupanca": ideal_poupanca,
                "perc_necessidades": perc_necessidades,
                "perc_desejos": perc_desejos,
                "perc_poupanca": perc_poupanca,
                "barra_necessidades": min(max(int(perc_necessidades), 0), 100),
                "barra_desejos": min(max(int(perc_desejos), 0), 100),
                "barra_poupanca": min(max(int(perc_poupanca), 0), 100),
                "superendividado": superendividado,
                "alertas": alertas,
            }

        return render(request, self.template_name, {"form": form, "resultado": resultado})


# Consulta de Cotações em Tempo Real via AwesomeAPI com Fallback Seguro
class CurrencyQuoteView(TemplateView):
    template_name = "finances/currency_quotes.html"
    API_URL = "https://economia.awesomeapi.com.br/last/USD-BRL,EUR-BRL,BTC-BRL"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        usando_fallback = False

        # Dados de fallback caso a máquina esteja sem internet ou a API retorne erro
        dados_padrao = {
            "USDBRL": {
                "code": "USD",
                "name": "Dólar Americano / Real Brasileiro",
                "bid": "5.65",
                "high": "5.70",
                "low": "5.61",
                "pctChange": "0.35",
                "create_date": "Cotação de referência (modo offline)",
            },
            "EURBRL": {
                "code": "EUR",
                "name": "Euro / Real Brasileiro",
                "bid": "6.15",
                "high": "6.20",
                "low": "6.11",
                "pctChange": "-0.18",
                "create_date": "Cotação de referência (modo offline)",
            },
            "BTCBRL": {
                "code": "BTC",
                "name": "Bitcoin / Real Brasileiro",
                "bid": "385400.00",
                "high": "391000.00",
                "low": "379500.00",
                "pctChange": "1.82",
                "create_date": "Cotação de referência (modo offline)",
            },
        }

        try:
            req = Request(self.API_URL, headers={"User-Agent": "FinFlow-DjangoApp/1.0"})
            with urlopen(req, timeout=5) as response:
                dados_api = json.loads(response.read().decode("utf-8"))
        except Exception:
            # Se falhar conexão, DNS, timeout ou limite de requisições, usa os valores de segurança
            dados_api = dados_padrao
            usando_fallback = True

        moedas_config = [
            ("USDBRL", "Dólar Comercial (USD)", "bi-currency-dollar", "success"),
            ("EURBRL", "Euro (EUR)", "bi-currency-euro", "primary"),
            ("BTCBRL", "Bitcoin (BTC)", "bi-currency-bitcoin", "warning"),
        ]

        cotacoes = []
        for chave, titulo, icone, cor in moedas_config:
            item = dados_api.get(chave) or dados_padrao[chave]
            variacao = float(item.get("pctChange", 0))
            cotacoes.append({
                "codigo": item.get("code", chave[:3]),
                "titulo": titulo,
                "icone": icone,
                "cor": cor,
                "compra": Decimal(str(item.get("bid", "0"))),
                "maxima": Decimal(str(item.get("high", "0"))),
                "minima": Decimal(str(item.get("low", "0"))),
                "variacao": variacao,
                "em_alta": variacao >= 0,
                "atualizado_em": item.get("create_date", ""),
            })

        context["cotacoes"] = cotacoes
        context["usando_fallback"] = usando_fallback
        return context
