## Como executar localmente (Windows)

1. Crie e ative um virtualenv (se ainda não existir):

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

2. Instale dependências:

```powershell
python -m pip install -r requirements.txt
```

3. Executar migrações e criar superuser:

```powershell
python manage.py migrate
python manage.py createsuperuser
```

4. Rodar a aplicação localmente:

```powershell
python manage.py runserver
```

5. Rodar testes:

```powershell
python manage.py test reciclAI -v 2
```
