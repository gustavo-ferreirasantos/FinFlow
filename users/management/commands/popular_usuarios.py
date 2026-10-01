import random
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from django.db import transaction
from faker import Faker

from users.models import Profile, Workspace, WorkspaceMember, Invitation


class Command(BaseCommand):
    help = "Cria a carga inicial de usuarios, perfis, espacos financeiros, membros e convites."

    def handle(self, *args, **options):
        fake = Faker('pt_BR')

        self.stdout.write(self.style.WARNING("Iniciando a carga de dados de usuarios..."))
        senha_criptografada = make_password("password123")

        with transaction.atomic():
            # 1. Gerar 5000 Usuarios e Perfis associados
            perfis = []
            for i in range(1, 5001):
                nome = fake.first_name()
                sobrenome = fake.last_name()
                username = f"{nome.lower()}_{sobrenome.lower()}_{i}"
                email = f"{username}@{fake.free_email_domain()}"

                user = User(
                    username=username,
                    email=email,
                    password=senha_criptografada,
                    first_name=nome,
                    last_name=sobrenome
                )
                user.save()

                perfil = Profile.objects.create(
                    user=user,
                    telephone=fake.cellphone_number()
                )
                perfis.append(perfil)

            self.stdout.write(self.style.SUCCESS("[+] 5000 usuarios e perfis criados."))

            # 2. Criar 1000 Espacos Financeiros 
            espacos = []
            tipos_espaco = ["Familia", "Casa", "Projeto", "Financas", "Republica", "Casal", "Viagem"]

            for i in range(1000):
                titular = perfis[i]
                nome_espaco = f"{random.choice(tipos_espaco)} {titular.user.last_name}"

                espaco = Workspace.objects.create(
                    name=nome_espaco,
                    holder=titular
                )
                espacos.append(espaco)

            self.stdout.write(self.style.SUCCESS("[+] 1000 espacos financeiros criados."))

            # 3. Vincular Titulares e Membros adicionais aos Espacos
            total_membros = 0
            for espaco in espacos:
                # Titular do espaco
                WorkspaceMember.objects.create(
                    workspace=espaco,
                    profile=espaco.holder,
                    role='T'
                )
                total_membros += 1

                # Sorteia entre 1 e 3 outros perfis cadastrados para serem membros do mesmo espaco
                candidatos = [p for p in perfis if p != espaco.holder]
                qtd_membros = random.randint(1, 3)
                membros_sorteados = random.sample(candidatos, qtd_membros)

                for perfil_membro in membros_sorteados:
                    WorkspaceMember.objects.create(
                        workspace=espaco,
                        profile=perfil_membro,
                        role='M'
                    )
                    total_membros += 1

            self.stdout.write(self.style.SUCCESS(f"[+] {total_membros} vinculos de membros registrados."))

            # 4. Gerar 2000 Convites distribuidos aleatoriamente entre os espacos
            status_opcoes = ['P', 'A', 'R', 'E']
            for _ in range(2000):
                espaco_sorteado = random.choice(espacos)
                Invitation.objects.create(
                    workspace=espaco_sorteado,
                    email=fake.email(),
                    status=random.choice(status_opcoes)
                )

            self.stdout.write(self.style.SUCCESS("[+] 2000 convites gerados com sucesso."))

        self.stdout.write(self.style.SUCCESS("\n[OK] Carga de usuarios finalizada com sucesso!"))
