## 🔄️ Última Atualização 09/04/2026
- Routers `dashboard_api_keys.py` migradas para Services Layer e Repositories.
- Otimizações em `core/dependencies.py` para melhorar e simplificar a validação da chave da API.

## ➡️ Próximas atualizações

- (Neste momento, em andamento) Desenvolvimento das **Services** para definir a regra de negócio da aplicação e desenvolvimento dos **Repositories** para centralizar os acessos aos dados SQL, visando **consistência na arquitetura do software** e mantendo apenas validações básicas e a coordenação do fluxo HTTP.
- Endpoint com métodos `POST`, `PUT` e `DELETE` para possibilitar a manipulação de dados através de outros sistemas e oferecendo autonomia dos dados aos usuários da API embarcada ao sistema.
- Função para alterar o quarto da reserva após a reserva já ter sido criada.

# RoomControl

### 📌 Visão Geral

__RoomControl__ é um sistema de gerenciamento de hotéis, desenvolvido com FastAPI no backend e Jinja2 para templates HTML.

A aplicação permite simples, mas extremamente úteis e eficientes funcionalidades:

- Cadastro e autenticação de hotéis.
- Gestão de quartos e reservas.
- Controle de hóspedes e verificação de disponibilidade.
- Dashboard administrativo com filtros, buscas e relatórios.
- Funcionalidades de front-end com JavaScript, Select2, SweetAlert2, InputMask e integração com APIs.
- Cadastro de colaboradores para executarem as funções operacionais do hotel.
- Controle de auditoria com rastreabilidade eficiente.
- Registro de chaves de API para integração entre sistemas e análise de dados.

O sistema é pensado para uso em __tablet ou desktop__, com foco em simplicidade e fluxo contínuo.

A aplicação é acompanhada de uma API (com interface/documentação __Swagger__) funcional para fazer consultas dentro das tabelas do projeto, sendo possível consultar dados de hotéis, hóspedes, reservas e mais.

O projeto ainda está em __desenvolvimento__, mas estou a procura de dicas e contribuições para o projeto.


### 🏗 Arquitetura

Backend

- Framework: __FastAPI__
- Banco de dados: __MySQL__ (SQLAlchemy ORM)
- Migrações: __Alembic__
- Autenticação e sessão: __Starlette + cookies + CSRF token__
- Estrutura de pastas:

```bash
alembic/
    versions/   # Arquivos de migração do Alembic
    env.py
app/
    core/   # Configs do SQLAlchemy, CSRF-Token, Encrypt e API Keys
    helpers/  # Funções simples que evitam código longo nas routers
    models/   # Models SQLAlchemy
    repositories/   # Controla a persistência e manipulação dos dados
    routers/   # Rotas organizadas por módulo
    schemas/   # Schemas do Pydantic para definir as respostas da API
    services/   # Define a regra de negócios e prepara transações
    templates/   # Templates do Jinja2
    utils/   # Funcionalidades úteis (ex. validador de documentos)
    main.py     # Builda e inicia aplicação com Uvicorn
tests/
    unit/    # Testes unitários
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
- Filtros avançados e combináveis de reservas e quartos

Decisões técnicas sobre a arquitetura:

- Método Service e Repostiories adotado para **definição de regras de negócios, validações e preparar alterações com o ORM (SQLAlchemy)** e **contrução de queries, inserções, atualizações, remoções e persistência (camada que conversa com o banco de dados)**, respectivamente. Conforme o projeto foi ficando maior, naturalmente adotei esse estilo de arquitetura mais limpa onde a Service "não sabe que o banco existe e controla a transação" e o Repository apenas modifica, persiste e acessa os objetos.

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
DB_HOST=localhost
DB_NAME=roomcontrol
DB_USER=root
DB_PASSWORD=password

SECRET_KEY=uma_chave_segura

GLOBAL_API_KEY="SUA_CHAVE_GLOBAL_DA_API_AQUI"

DOCS_USERNAME="admin"
DOCS_PASSWORD="admin"
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
- A docuemntação da API no Swagger será iniciado em: http://127.0.0.1:8000/docs

**OBS**: É necessário gerar uma API Key, pelo login do hotel para consultar os dados no endpoints da API ou use a `GLOBAL_API_KEY` configurada em `.env`.

### 🔒 Segurança

- CSRF token incluído em todos os forms para evitar ataques de cross-site.
- Sessões baseadas em cookie com SessionMiddleware do Starlette.
- Rotas administrativas protegidas pelo decorator require_admin_session.
- Na API, os endpoints que consultam dados administrativos só podem ser consultados pela API Global definida no `.env`
### 👩‍💻 Resumo das tecnologias utilizadas

- __Backend__: Python, FastAPI, Pydantic, SQLAlchemy, Alembic, MySQL
- __Frontend__: HTML, Jinja2, Bootstrap 5, jQuery, Select2, SweetAlert2, InputMask, DataTables
- __DevOps__: Uvicorn, Git
- __Testes__: Pytest
### 📝 Licença

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

