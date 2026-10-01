# FinFlow

Sistema de gestão financeira desenvolvido em **Django 5.2** — gerencia usuários, espaços financeiros compartilhados, contas, transações, cartões de crédito, faturas, orçamentos, metas e transações recorrentes.

## Requisitos

- Python 3.10 ou superior
- `pip`

## Instalação

```bash
# 1. Criar o ambiente virtual
python -m venv venv

# 2. Ativar (PowerShell / CMD)
.\venv\Scripts\Activate.ps1

# 3. Instalar as dependências
pip install -r requirements.txt
```

## Executar o projeto

```bash
python manage.py runserver
```

Acesse: **http://127.0.0.1:8000/admin/**

## Popular o banco do zero

Caso o arquivo `db.sqlite3` não exista (ou queira recomeçar), execute **nesta ordem**:

```bash
python manage.py migrate            # cria as tabelas
python manage.py popular_usuarios   # 1º: usuários, perfis, espaços e convites
python manage.py popular_financas   # 2º: contas, transações, faturas, metas etc.
python manage.py createsuperuser    # admin do painel
```

> ⚠️ A ordem importa: o `popular_financas` precisa que os espaços criados pelo
> `popular_usuarios` já existam, senão ele encerra com erro.

## Credenciais

### Superusuário (admin)

| Campo | Valor |
|---|---|
| URL | http://127.0.0.1:8000/admin/ |
| Usuário | `admin` |
| Senha | `admin123` |

### Usuários gerados pelo script `popular_usuarios`

| Campo | Valor |
|---|---|
| Senha (de todos) | `password123` |
| Usuário | `<nome>_<sobrenome>_<numero>` (ex: `joao_silva_1`) |
| E-mail | `<usuario>@<dominio>` |

Os nomes de usuário são gerados aleatoriamente com o **Faker** — consulte a
listagem completa no admin (**Auth → Users**) ou no banco de dados.

## Estrutura do projeto

```
FinFlow/
├── finflow/        # configurações do projeto (settings, urls, wsgi)
├── users/          # app de usuários: Profile, Workspace, WorkspaceMember, Invitation
├── finances/       # app financeira: Account, Category, Transaction, CreditCard,
│                   # Invoice, Budget, FinancialGoal, RecurringTransaction
├── manage.py
├── requirements.txt
├── credenciais.txt
└── db.sqlite3      # banco local (gerado pelo migrate; não versionado)
```

## Comandos úteis

| Comando | Função |
|---|---|
| `python manage.py runserver` | Sobe o servidor de desenvolvimento |
| `python manage.py check` | Verifica o projeto sem executar o servidor |
| `python manage.py makemigrations` | Gera migrações a partir dos models |
| `python manage.py migrate` | Aplica as migrações no banco |
| `python manage.py popular_usuarios` | Carga de usuários, espaços e convites |
| `python manage.py popular_financas` | Carga de dados financeiros |
| `python manage.py createsuperuser` | Cria o administrador do `/admin/` |
| `python manage.py changepassword admin` | Redefine a senha do admin |
