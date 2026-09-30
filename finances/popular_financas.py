import random
from datetime import date, timedelta
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.utils import timezone
from faker import Faker

from usuarios.models import EspacoFinanceiro, Perfil, MembroEspaco
from financas.models import (
    Conta,
    Categoria,
    CartaoCredito,
    Fatura,
    Transacao,
    Orcamento,
    MetaFinanceira,
    TransacaoRecorrente,
)


class Command(BaseCommand):
    help = "Carga massiva de dados financeiros (contas, categorias, transações, faturas, orçamentos, metas e recorrentes)."

    def handle(self, *args, **options):
        fake = Faker('pt_BR')
        self.stdout.write(self.style.WARNING("Iniciando a carga de dados financeiros..."))

        espacos = list(EspacoFinanceiro.objects.all())
        if not espacos:
            self.stdout.write(
                self.style.ERROR(
                    "Nenhum Espaço Financeiro encontrado! Execute 'python manage.py popular_usuarios' primeiro."
                )
            )
            return

        bancos_disponiveis = ["Nubank", "Itaú", "Inter", "Bradesco", "Carteira"]
        tipos_conta = ["Corrente", "Poupança", "Carteira", "Investimento"]

        categorias_receita = ["Salário", "Rendimentos", "Freelance", "Vendas", "Outras Receitas"]
        categorias_despesa = ["Alimentação", "Moradia", "Transporte", "Lazer", "Saúde", "Educação", "Assinaturas"]

        total_transacoes = 0
        total_faturas = 0
        total_outros = 0

        for espaco in espacos:
            self.stdout.write(f"Processando espaço: {espaco.nome}...")

            # 1. Criar Contas Bancárias (2 a 4 por espaço)
            qtd_contas = random.randint(2, 4)
            contas_espaco = []
            for _ in range(qtd_contas):
                nome_banco = random.choice(bancos_disponiveis)
                nome_conta = f"{nome_banco} - {fake.word().capitalize()}"
                conta = Conta.objects.create(
                    espaco=espaco,
                    nome=nome_conta,
                    tipo=random.choice(tipos_conta),
                    saldo_inicial=Decimal(str(random.uniform(500.0, 15000.0)).format(".2f")),
                )
                contas_espaco.append(conta)

            # 2. Criar Categorias de Receitas e Despesas
            cats_espaco = []
            for nome_cat in categorias_receita:
                cat = Categoria.objects.create(espaco=espaco, nome=nome_cat, tipo="Receita")
                cats_espaco.append(cat)
            for nome_cat in categorias_despesa:
                cat = Categoria.objects.create(espaco=espaco, nome=nome_cat, tipo="Despesa")
                cats_espaco.append(cat)

            membros_espaco = list(MembroEspaco.objects.filter(espaco=espaco).select_related('perfil'))
            responsaveis = [m.perfil for m in membros_espaco] if membros_espaco else []

            # 3. Geração Massiva de Transações (~50 por espaço)
            cat_receitas = [c for c in cats_espaco if c.tipo == "Receita"]
            cat_despesas = [c for c in cats_espaco if c.tipo == "Despesa"]

            for _ in range(50):
                tipo_transacao = random.choice(["Receita", "Despesa"])
                categoria = random.choice(cat_receitas if tipo_transacao == "Receita" else cat_despesas)
                conta = random.choice(contas_espaco)
                responsavel = random.choice(responsaveis) if responsaveis and random.random() > 0.2 else None
                
                valor = Decimal(str(random.uniform(10.0, 3000.0) if tipo_transacao == "Despesa" else random.uniform(1000.0, 8000.0)).format(".2f"))
                data_transacao = fake.date_between(start_date='-6m', end_date='today')

                Transacao.objects.create(
                    conta=conta,
                    categoria=categoria,
                    responsavel=responsavel,
                    descricao=fake.sentence(nb_words=4),
                    valor=valor,
                    tipo=tipo_transacao,
                    data=data_transacao,
                )
                total_transacoes += 1

            # 4. Cartões de Crédito e Faturas (últimos 6 meses)
            conta_corrente = next((c for c in contas_espaco if c.tipo == "Corrente"), contas_espaco[0])
            cartao = CartaoCredito.objects.create(
                conta=conta_corrente,
                nome=f"Mastercard {fake.word().capitalize()}",
                limite=Decimal("5000.00"),
                dia_fechamento=25,
                dia_vencimento=5,
            )

            hoje = date.today()
            for i in range(6):
                mes_ref = (hoje.replace(day=1) - timedelta(days=30 * i)).replace(day=1)
                
                if i > 1:
                    status_fatura = "Paga"
                elif i == 1:
                    status_fatura = "Fechada"
                else:
                    status_fatura = "Aberta"

                valor_fatura = Decimal(str(random.uniform(200.0, 3500.0)).format(".2f"))

                Fatura.objects.create(
                    cartao=cartao,
                    mes_referencia=mes_ref,
                    valor_total=valor_fatura,
                    status=status_fatura,
                )
                total_faturas += 1

            # 5. Orçamentos, Metas e Recorrentes
            for cat_d in cat_despesas[:3]:
                Orcamento.objects.create(
                    espaco=espaco,
                    categoria=cat_d,
                    valor_limite=Decimal("1500.00"),
                    mes_referencia=hoje.replace(day=1),
                    alerta_enviado=False,
                )
                total_outros += 1

            MetaFinanceira.objects.create(
                espaco=espaco,
                nome="Reserva de Emergência",
                valor_alvo=Decimal("10000.00"),
                valor_atual=Decimal("3500.00"),
                prazo=hoje + timedelta(days=365),
            )
            total_outros += 1

            cat_recorrente = cat_despesas[0]
            TransacaoRecorrente.objects.create(
                espaco=espaco,
                conta=conta_corrente,
                categoria=cat_recorrente,
                descricao="Aluguel / Condomínio",
                valor=Decimal("1200.00"),
                tipo="Despesa",
                dia_vencimento=10,
                lembrete_enviado=True,
            )
            total_outros += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"\nCarga concluída com sucesso!\n"
                f"- Transações geradas: {total_transacoes}\n"
                f"- Faturas geradas: {total_faturas}\n"
                f"- Orçamentos, Metas e Recorrentes: {total_outros}"
            )
        )
