## 🔄️ Última Atualização 23/01/2026
- Testes de integração dos endpoints da API configurados e testados (necessário instalar novas dependências);
- Testes no endpoint usado pela lib JS `DataTables` para consultar dados de pedidos periodicamente, com objetivo de garantir a integridade dos dados e evitando quebras do template.
- Correções nos tipos de dados nos schemas de saída do `Pydantic`.


## ➡️ Próximas atualizações
- Análise para avaliar necessidade e utilidade de outros endpoints utilizando métodos **POST, PUT** e **DELETE**;
- Criar o back-end para uma função de notificar o hotel pelo dashboard da aplicação sobre um novo pedido de serviço e demais relevantes notificações.

# RoomControl

### 📌 Visão Geral

__RoomControl__ é um sistema de gerenciamento de hotéis, desenvolvido com FastAPI no backend e Jinja2 para templates HTML.

A aplicação permite simples, mas extremamente úteis e eficientes funcionalidades:

- Cadastro e autenticação de hotéis.
- Gestão de quartos e reservas.
- Controle de hóspedes e verificação de disponibilidade.
- Dashboard administrativo com filtros, buscas e relatórios.
- Funcionalidades de front-end com JavaScript, Select2, SweetAlert2, InputMask e integração com APIs.

O sistema é pensado para uso em __tablet ou desktop__, com foco em simplicidade e fluxo contínuo.

A aplicação é acompanhada de uma API (com interface no __Swagger__) funcional para fazer consultas dentro das tabelas do projeto, sendo possível consultar dados de hotéis, hóspedes, reservas e mais.

O projeto ainda está em __desenvolvimento__, mas estou a procura de dicas e contribuições para o projeto.


### 🏗 Arquitetura

Backend

- Framework: __FastAPI__
- Banco de dados: __MySQL__ (SQLAlchemy ORM)
- Migrações: __Alembic__
- Autenticação e sessão: __cookies + CSRF token__
- Estrutura de pastas:

```bash
alembic/
    versions/
    env.py
app/
    core/   # Configs do SQLAlchemy, CSRF-Token e Encrypt
    helpers/  # Funções criadas para evitar repetição e código longo nas routers
    models/   # Models SQLAlchemy
    routers/   # Rotas organizadas por módulo
    schemas/   # Schemas do Pydantic para definir as respostas da API
    templates/   # Templates do Jinja2
    utils/   # Funcionalidades úteis (ex. validador de documentos)
tests/
    conftest.py   # Arquivo de configuração dos testes
.gitignore
alembic.ini
pytest.ini
README.md
requirements.txt
```

Frontend

- Templates: Jinja2

Bibliotecas:

- jQuery
- Bootstrap 5
- Select2 → selects avançados com busca e filtro
- InputMask → máscaras de inputs (CNPJ, telefone, valores monetários)
- SweetAlert2 → alertas interativos
- DataTables → Cria tabelas dinâmicas no template

Funcionalidades:

- Formulários de login e registro com validação de CSRF
- Atualização dinâmica de selects (quartos e hóspedes)
- Filtros avançados de reservas e quartos
### ⚙️ Como rodar o projeto

Pré-requisitos para rodar o projeto:
- Python >= 3.10
- MySQL
- Virtualenv (recomendado)

#### Passos:

1- Clone o repositório:
``` bash
git clone https://github.com/CaianMorais/roomcontrol.git
cd RoomControl
```

2- Crie o ambiente virtual:
``` bash
python -m venv venv
source venv/bin/activate   # Linux / Mac
venv\Scripts\activate      # Windows
```

3- Instale as dependências:
``` bash
pip install -r requirements.txt
```

4- Crie o .env e configure as variáveis de ambiente:
``` bash
SECRET_KEY=uma_chave_segura

DB_HOST=localhost
DB_NAME=roomcontrol
DB_USER=root
DB_PASSWORD=password
```

5- Crie o banco e rode as migrations:

No MySQL:
``` bash
CREATE DATABASE roomcontrol;
```

No terminal:
``` bash
alembic upgrade head
```

6- Rodar no ambiente de desenvolvimento:
``` bash
uvicorn app.main:app --reload
```
- A aplicação será iniciada em: http://127.0.0.1:8000
- O Swagger será iniciado em: http://127.0.0.1:8000/docs

### 🔒 Segurança

- CSRF token incluído em todos os forms para evitar ataques de cross-site.
- Sessões baseadas em cookie com SessionMiddleware do Starlette.
- Rotas administrativas protegidas pelo decorator require_session.
### 👩‍💻 Resumo das tecnologias utilizadas

- __Backend__: Python, FastAPI, Pydantic, SQLAlchemy, Alembic, MySQL
- __Frontend__: HTML, Jinja2, Bootstrap 5, jQuery, Select2, SweetAlert2, InputMask, DataTables
- __DevOps__: Uvicorn, Git
- __Testes__: Pytest
### 📝 Licença

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

