## 🔄️ Última Atualização 20/01/2026
- Módulo Serviços completamente finalizado e testado
- Back-end e Front-end otimizados com **código limpo**
- Interface Swagger da API otimizada com a remoção da seção Schemas


## ➡️ Próximas atualizações
- Desenvolver testes de integração de rota, dando prioridade a intregridade dos dados pelos endpoint;
- Desenvolver testes para endpoint que retornar HTMLResponse para o Jinja, com foco em entregar os dados sem quebrar o template;
- Desenvolver testes de serviço para validações de filtros, ordenações;
- Após os testes existentes, uma análise será feita para avaliar necessidade e utilidade de outros endpoints utilizando métodos **POST, PUT** e **DELETE**.

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
    models/   # Models SQLAlchemy
    routers/   # Rotas organizadas por módulo
    templates/   # Templates do Jinja2
    utils/   # Funcionalidades úteis (ex. validador de documentos)
.gitignore
alembic.ini
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
- O servidor será iniciado em: http://127.0.0.1:8000

### 🔒 Segurança

- CSRF token incluído em todos os forms para evitar ataques de cross-site.
- Sessões baseadas em cookie com SessionMiddleware do Starlette.
- Rotas administrativas protegidas pelo decorator require_session.
### 👩‍💻 Resumo das tecnologias utilizadas

- __Backend__: Python, FastAPI, SQLAlchemy, Alembic, MySQL
- __Frontend__: HTML, Jinja2, Bootstrap 5, jQuery, Select2, SweetAlert2, InputMask
- __DevOps__: Uvicorn, Git
### 📝 Licença

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

