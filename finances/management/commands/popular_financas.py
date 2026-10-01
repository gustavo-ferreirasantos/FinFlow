import random
from datetime import date, timedelta
from decimal import Decimal
from django.core.management.base import BaseCommand
from faker import Faker

# Removi profile porque ele já é obtido a partir de membros_espaco
from users.models import Workspace, WorkspaceMember
from finances.models import (
    Account,
    Category,
    CreditCard,
    Invoice,
    Transaction,
    Budget,
    FinancialGoal,
    RecurringTransaction,
)

# Usar Decimal() evita as imprecisões do tipo float 
class Command(BaseCommand):
    help = "Carga massiva de dados financeiros (contas, categorias, transações, faturas, orçamentos, metas e recorrentes)."

    def handle(self, *args, **options):
        fake = Faker('pt_BR')
        self.stdout.write(self.style.WARNING("Iniciando a carga de dados financeiros..."))

        espacos = list(Workspace.objects.all())
        if not espacos:
            self.stdout.write(
                self.style.ERROR( # Formata a mensagem com cor vermelha
                    "Nenhum Espaço Financeiro encontrado! Execute 'python manage.py popular_usuarios' primeiro."
                )
            )
            return

        bancos_disponiveis = ["Nubank", "Itaú", "Inter", "Bradesco", "Carteira"]
        # Códigos das choices do model Account.TYPES (C, P, W, I)
        tipos_conta = ["C", "P", "W", "I"]

        categorias_receita = ["Salário", "Rendimentos", "Freelance", "Vendas", "Outras Receitas"]
        categorias_despesa = ["Alimentação", "Moradia", "Transporte", "Lazer", "Saúde", "Educação", "Assinaturas"]

        total_transacoes = 0
        total_faturas = 0
        total_outros = 0

        for espaco in espacos:
            self.stdout.write(f"Processando espaço: {espaco.name}...")

            # 1. Criar Contas Bancárias (2 a 4 por espaço)
            qtd_contas = random.randint(2, 4)
            contas_espaco = []
            for _ in range(qtd_contas):
                nome_banco = random.choice(bancos_disponiveis)
                # Como o faker pode gerar qualquer palavra da língua portuguesa, os nomes gerados podem ser bastante estranhos
                nome_conta = f"{nome_banco} - {fake.word().capitalize()}"
                conta = Account.objects.create(
                    workspace=espaco,
                    name=nome_conta,
                    type=random.choice(tipos_conta),
                    initial_balance=Decimal(f"{random.uniform(500.0, 15000.0):.2f}"),
                )
                contas_espaco.append(conta) # Vai conter a lista de contas bancárias

            # 2. Criar Categorias de Receitas e Despesas (cat é a abreviação de categoria)
            cats_espaco = []
            for nome_cat in categorias_receita:
                cat = Category.objects.create(workspace=espaco, name=nome_cat, type="R")
                cats_espaco.append(cat)
            for nome_cat in categorias_despesa:
                cat = Category.objects.create(workspace=espaco, name=nome_cat, type="D")
                cats_espaco.append(cat)

            membros_espaco = list(WorkspaceMember.objects.filter(workspace=espaco).select_related('profile'))
            responsaveis = [m.profile for m in membros_espaco] if membros_espaco else []

            # 3. Geração Massiva de Transações (~50 por espaço)
            cat_receitas = [c for c in cats_espaco if c.type == "R"]
            cat_despesas = [c for c in cats_espaco if c.type == "D"]

            # Gera aleatoriamente receitas e despesas com igual chance
            for _ in range(50):
                tipo_transacao = random.choice(["R", "D"])
                categoria = random.choice(cat_receitas if tipo_transacao == "R" else cat_despesas)
                conta = random.choice(contas_espaco)
                responsavel = random.choice(responsaveis) if responsaveis and random.random() > 0.2 else None
                
                valor = Decimal(f"{random.uniform(10.0, 3000.0) if tipo_transacao == 'D' else random.uniform(1000.0, 8000.0):.2f}")
                data_transacao = fake.date_between(start_date='-6m', end_date='today')
                # Cria uma nova linha na tabela finances_transaction
                Transaction.objects.create(
                    account=conta,
                    category=categoria,
                    responsible=responsavel,
                    description=fake.sentence(nb_words=4),
                    value=valor,
                    type=tipo_transacao,
                    date=data_transacao,
                )
                total_transacoes += 1

            # 4. Cartões de Crédito e Faturas (últimos 6 meses por cartão)
            # Pega a primeira conta corrente da lista caso ela exista, caso contrário, retorna a primeira conta da lista
            conta_corrente = next((c for c in contas_espaco if c.type == "C"), contas_espaco[0])
            hoje = date.today()

            marcas_cartao = ["Mastercard", "Visa", "Elo", "American Express"]
            # Cria de 1 a 2 cartões para cada espaço financeiro
            for _ in range(random.randint(1, 2)):
                dia_fechamento = random.randint(1, 28)
                dia_vencimento = random.randint(1, 28)
                while dia_vencimento == dia_fechamento:
                    dia_vencimento = random.randint(1, 28)

                cartao = CreditCard.objects.create(
                    account=conta_corrente,
                    name=f"{random.choice(marcas_cartao)} {fake.word().capitalize()}",
                    limit=Decimal(f"{random.uniform(1500.0, 15000.0):.2f}"),
                    closing_day=dia_fechamento,
                    due_day=dia_vencimento,
                )

                for i in range(6):
                    # Calcula o primeiro dia do mês de referência das faturas, retrocedendo i meses a partir de hoje
                    mes_ref = (hoje.replace(day=1) - timedelta(days=30 * i)).replace(day=1)

                    if i > 1:
                        status_fatura = "P"
                    elif i == 1:
                        status_fatura = "F"
                    else:
                        status_fatura = "A"

                    valor_fatura = Decimal(f"{random.uniform(200.0, 3500.0):.2f}")
                    # 6 faturas, cada uma dos últimos 6 meses pra cada cartão
                    Invoice.objects.create(
                        credit_card=cartao,
                        reference_month=mes_ref,
                        total_value=valor_fatura,
                        status=status_fatura,
                    )
                    total_faturas += 1

            # 5. Orçamentos, Metas e Recorrentes
            # Orçamentos: sorteia de 2 a 4 categorias de despesa por espaço
            qtd_orcamentos = random.randint(2, 4)
            cats_orcamento = random.sample(cat_despesas, min(qtd_orcamentos, len(cat_despesas)))
            for cat_d in cats_orcamento:
                # mês de referência sorteado entre os últimos 3 meses
                meses_atras = random.randint(0, 2)
                mes_ref_orc = (hoje.replace(day=1) - timedelta(days=30 * meses_atras)).replace(day=1)
                Budget.objects.create(
                    workspace=espaco,
                    category=cat_d,
                    limit_value=Decimal(f"{random.uniform(300.0, 3000.0):.2f}"),
                    reference_month=mes_ref_orc,
                    alert_sent=random.choice([True, False]),
                )
                total_outros += 1

            # Metas financeiras: de 1 a 3 por espaço, com prazos e valores variados
            nomes_metas = [
                "Reserva de Emergência",
                "Viagem",
                "Carro Novo",
                "Entrada de Imóvel",
                "Educação",
            ]
            qtd_metas = random.randint(1, 3)
            for nome_meta in random.sample(nomes_metas, qtd_metas):
                valor_alvo = Decimal(f"{random.uniform(3000.0, 50000.0):.2f}")
                # valor_atual entre 0% e 90% do alvo (sempre menor ou igual ao alvo)
                valor_atual = Decimal(f"{float(valor_alvo) * random.uniform(0.0, 0.9):.2f}")
                # prazo entre 3 e 24 meses no futuro
                prazo_meta = hoje + timedelta(days=random.randint(90, 730))
                FinancialGoal.objects.create(
                    workspace=espaco,
                    name=nome_meta,
                    target_value=valor_alvo,
                    current_value=valor_atual,
                    deadline=prazo_meta,
                )
                total_outros += 1

            # Transações recorrentes: de 3 a 5 por espaço
            recorrentes_base = [
                ("Aluguel", 1200.0, "D"),
                ("Internet", 120.0, "D"),
                ("Condomínio", 600.0, "D"),
                ("Streaming", 55.0, "D"),
                ("Academia", 100.0, "D"),
                ("Salário", 4500.0, "R"),
            ]
            qtd_recorrentes = random.randint(3, 5)
            for descricao_rec, valor_base, tipo_rec in random.sample(recorrentes_base, qtd_recorrentes):
                # variação de ±20% no valor base
                valor_rec = Decimal(f"{valor_base * random.uniform(0.8, 1.2):.2f}")
                RecurringTransaction.objects.create(
                    workspace=espaco,
                    account=conta_corrente,
                    category=random.choice(cat_receitas if tipo_rec == "R" else cat_despesas),
                    description=descricao_rec,
                    value=valor_rec,
                    type=tipo_rec,
                    due_day=random.randint(1, 28),
                    reminder_sent=random.choice([True, False]),
                )
                total_outros += 1

        self.stdout.write(
            self.style.SUCCESS( # Formata a mensagem com cor verde
                f"\nCarga concluída com sucesso!\n"
                f"- Transações geradas: {total_transacoes}\n"
                f"- Faturas geradas: {total_faturas}\n"
                f"- Orçamentos, Metas e Recorrentes: {total_outros}"
            )
        )
