# Etapa 2

# Setup + Modelos usuarios (finflow)

## 🎯 Objetivo da Etapa
Configurar o ambiente virtual do projeto Django


## ⚙️ Setup inicial

> 📌 **Referência no vídeo:** [ Curso de Django - Aula 1 - criando o projeto Django  ](https://youtu.be/p5MCJLIn_is?si=M2l_9WoX0unG9KDC)  

```bash
# 1. Criar pasta do projeto e entrar nela
mkdir nome_do_projeto
cd nome_do_projeto
# 2. Criar ambiente virtual
python -m venv venv
# 3. Ativar (Windows)
.\venv\Scripts\Activate.ps1
# 4. Instalar dependências
pip install django faker
# 5. Salvar dependências
pip freeze > requirements.txt
# 6. Criar projeto Django
django-admin startproject finflow .
# 7. Criar as duas apps
python manage.py startapp users
python manage.py startapp finances

```

## ⚙️ Validação e Execução dos modelos criados para usuários

> 📌 **Referência no vídeo:** [ Curso de Django - Aula 2 - Aprendendo sobre models (criando tabelas no Banco de Dados com Django) ](https://www.youtube.com/watch?v=XGTdhVZW8V8&list=PLLVddSbilcumgeyk0z6ko5U_FYPfbRO2C&index=4)  

## >_ Criação do migrations e aplicando no banco de dados
```bash
python manage.py makemigrations users
python manage.py migrate
```

## >_ Criação de um admin e entrar na sua página

```bash
python manage.py createsuperuser 
Username: admin
Email address: admin@gmail.com
Password: admindsw
python manage.py runserver
http://127.0.0.1:8000/admin/
```

## >_ Remover banco de dados e migrations para modificações maiores
```bash
Remove-Item db.sqlite3
Remove-Item users\migrations\0*.py
```

## ⚙️ Customização do Django Admin (usuarios/admin.py)



> 📌 **Referência na documentação:** [ Escrevendo sua primeira aplicação Django, parte 2 ](https://docs.djangoproject.com/pt-br/6.1/intro/tutorial02/)  






## ⚙️ Extras




## ⚙️ Aprimorar interface do Dashboard Admin

> 📌 **Referência no vídeo:** [  Django Custom Admin Panel In One Minute || Django Tricks || Python Hindi Tutorials  ](https://youtu.be/Ugo1HzcQZjI?si=MWALMJOlBKDHRTu_)  


## >_ Em finflow/settings.py
```bash
INSTALLED_APPS = [
    'jazzmin',     
    ...
]


pip install django-jazzmin
```