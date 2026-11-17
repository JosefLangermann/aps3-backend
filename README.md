# Central de Eventos Acadêmicos — API

API REST feita em **FastAPI** para organizar a agenda de eventos de uma instituição de ensino: palestras,
workshops, minicursos, seminários e competições. Além do cadastro dos eventos, o sistema controla os
participantes e as inscrições de cada um nos eventos disponíveis.

> **APS 3:** nesta versão os dados deixaram de ficar em listas na memória e passaram a ser salvos em um banco
> **SQLite**, acessado pelo **SQLAlchemy ORM**. Também foram criados **relatórios** que consolidam as informações
> (ocupação dos eventos, eventos por categoria e participação por curso).

## Sobre o projeto

Um evento tem um número limitado de vagas, e um participante pode se inscrever nele desde que:

- o evento exista;
- o participante exista;
- ele ainda não esteja inscrito ali;
- ainda sobre vaga.

Se qualquer uma dessas condições falhar, a API responde com um status HTTP apropriado e uma mensagem explicando o motivo.

## Tecnologias

- Python 3.10+
- FastAPI
- SQLite + SQLAlchemy ORM (2.x)
- Pydantic (validação de dados)
- Uvicorn (servidor ASGI)
- Pytest + HTTPX (testes automatizados)

## Organização do código

O projeto segue o padrão **MVC**, dividido em camadas dentro de `app/`:

```
.
├── main.py                 → cria o app, registra as rotas e trata erros de banco
├── requirements.txt
├── eventos.db              → banco SQLite (criado automaticamente na 1ª execução)
├── tests/                  → testes automatizados
└── app/
    ├── database.py         → conexão com o SQLite, sessões e criação das tabelas
    ├── models/             → tabelas e relacionamentos (SQLAlchemy)
    │   ├── evento.py
    │   ├── participante.py
    │   └── inscricao.py
    ├── routers/            → recebe as requisições HTTP (rotas)
    │   ├── eventos.py
    │   ├── participantes.py
    │   ├── inscricoes.py
    │   └── relatorios.py
    ├── schemas/            → validação dos dados de entrada e formato das respostas (Pydantic)
    │   ├── evento.py
    │   ├── participante.py
    │   ├── inscricao.py
    │   └── relatorio.py
    └── regras/             → regras de negócio, persistência e consultas dos relatórios
        ├── eventos.py
        ├── participantes.py
        ├── inscricoes.py
        └── relatorios.py
```

`routers` cuida só de HTTP, `schemas` valida o formato dos dados, `models` representa as tabelas, e `regras`
concentra a lógica de negócio e as consultas ao banco (inclusive os relatórios) — nada disso fica misturado na rota.

## Banco de dados

- **SQLite**, arquivo `eventos.db` salvo **na raiz do projeto** (mesma pasta do `main.py`). Ele é criado sozinho na
  primeira vez que a API sobe, e os dados continuam lá depois de fechar e abrir a aplicação de novo.
- `app/database.py` configura o `engine`, a `SessionLocal` e a função `obter_sessao()`, que abre uma sessão para cada
  requisição e a **fecha no final**.
- As tabelas `eventos`, `participantes` e `inscricoes` são criadas a partir dos modelos
  (`Base.metadata.create_all`). Não foi usado Alembic.
- Para apagar todos os dados, é só parar a API e excluir o arquivo `eventos.db`.
- O arquivo `eventos.db` está no `.gitignore` (não vai para o repositório).

### Relacionamentos e integridade

- `Evento 1 —— N Inscricao N —— 1 Participante`
- `UNIQUE (evento_id, participante_id)` na inscrição: o mesmo participante não se inscreve duas vezes no mesmo evento.
- E-mail do participante `UNIQUE` (salvo em minúsculas).
- `CHECK (capacidade > 0)` no evento.
- **Exclusão:** ao excluir um evento ou um participante, as inscrições ligadas a ele são excluídas junto
  (cascade), então não sobram registros órfãos.
- **Atualização:** não dá para reduzir a capacidade de um evento para menos que o número de inscritos (409).

## Como rodar

```bash
# 1. (opcional) crie e ative um ambiente virtual
python -m venv venv
venv\Scripts\activate          # Windows
source venv/bin/activate       # Linux/Mac

# 2. Instale as dependências
python -m pip install -r requirements.txt

# 3. Suba o servidor
python -m uvicorn main:app --reload
```

A API sobe em `http://127.0.0.1:8000`. A documentação interativa (Swagger) fica em
`http://127.0.0.1:8000/docs`, e dá pra testar todas as rotas direto pelo navegador.

## Endpoints

**Eventos**

| Método | Rota | O que faz |
|---|---|---|
| POST | `/eventos` | cria um evento |
| GET | `/eventos` | lista todos os eventos |
| GET | `/eventos/{id}` | busca um evento pelo id |
| PUT | `/eventos/{id}` | atualiza um evento |
| DELETE | `/eventos/{id}` | remove um evento (e suas inscrições) |

**Participantes**

| Método | Rota | O que faz |
|---|---|---|
| POST | `/participantes` | cria um participante |
| GET | `/participantes` | lista todos os participantes |
| GET | `/participantes/{id}` | busca um participante pelo id |
| PUT | `/participantes/{id}` | atualiza um participante |
| DELETE | `/participantes/{id}` | remove um participante (e suas inscrições) |

**Inscrições**

| Método | Rota | O que faz |
|---|---|---|
| POST | `/eventos/{evento_id}/inscricoes/{participante_id}` | inscreve um participante em um evento |
| GET | `/eventos/{evento_id}/inscricoes` | lista quem está inscrito em um evento |

**Relatórios**

| Método | Rota | O que faz |
|---|---|---|
| GET | `/relatorios/eventos/ocupacao` | ocupação de cada evento |
| GET | `/relatorios/eventos/categorias` | consolidado por categoria |
| GET | `/relatorios/participantes/cursos` | consolidado por curso |

## Relatórios (consolidação dos dados)

Todos são calculados na hora, com consultas do SQLAlchemy (`JOIN`, `GROUP BY`, `COUNT`, `SUM`), a partir do que
está no banco — não existe nenhum valor fixo no código. Se não houver registros, a resposta é uma lista vazia `[]`.

**1. Ocupação dos eventos** — `GET /relatorios/eventos/ocupacao`
Para cada evento: id, título, capacidade, total de inscritos, vagas disponíveis e percentual de ocupação
(`inscritos / capacidade * 100`). Usa `LEFT JOIN`, então eventos **sem inscrições** também aparecem (0 inscritos, 0%).
Há proteção contra divisão por zero.

**2. Eventos por categoria** — `GET /relatorios/eventos/categorias`
Para cada categoria: total de eventos, capacidade total e total de inscrições. As inscrições são contadas por evento
antes de agrupar, para a capacidade não ser somada em duplicidade.

**3. Participação por curso** — `GET /relatorios/participantes/cursos`
Para cada curso: total de participantes (`COUNT DISTINCT`, então ninguém é contado duas vezes mesmo com várias
inscrições) e total de inscrições.

## Exemplos

Criar um evento:

```http
POST /eventos
Content-Type: application/json

{
  "titulo": "Semana de Tecnologia",
  "descricao": "Palestras sobre Inteligência Artificial",
  "data": "2026-10-15",
  "horario": "14:00:00",
  "local": "Auditório Central",
  "capacidade": 2,
  "categoria": "Palestra"
}
```

Resposta (`201`):

```json
{
  "titulo": "Semana de Tecnologia",
  "descricao": "Palestras sobre Inteligência Artificial",
  "data": "2026-10-15",
  "horario": "14:00:00",
  "local": "Auditório Central",
  "capacidade": 2,
  "categoria": "Palestra",
  "id": 1,
  "inscritos_atuais": 0
}
```

Criar um participante (`POST /participantes`):

```json
{ "nome": "Ana Souza", "email": "ana@exemplo.com", "curso": "Engenharia de Software" }
```

Inscrever um participante (`POST /eventos/1/inscricoes/1`, resposta `201`):

```json
{ "id": 1, "evento_id": 1, "participante_id": 1, "data_inscricao": "2026-11-17T19:22:25.133783" }
```

Listar inscritos (`GET /eventos/1/inscricoes`):

```json
[ { "nome": "Ana Souza", "email": "ana@exemplo.com", "curso": "Engenharia de Software", "id": 1 } ]
```

Relatório de ocupação (`GET /relatorios/eventos/ocupacao`):

```json
[
  {
    "evento_id": 1,
    "titulo": "Semana de Tecnologia",
    "capacidade": 2,
    "total_inscritos": 1,
    "vagas_disponiveis": 1,
    "percentual_ocupacao": 50.0
  }
]
```

Relatório por categoria (`GET /relatorios/eventos/categorias`):

```json
[ { "categoria": "Palestra", "total_eventos": 1, "capacidade_total": 2, "total_inscricoes": 1 } ]
```

Relatório por curso (`GET /relatorios/participantes/cursos`):

```json
[ { "curso": "Engenharia de Software", "total_participantes": 1, "total_inscricoes": 1 } ]
```

## Erros tratados

| Situação | Status | Resposta |
|---|---|---|
| Evento não existe | 404 | `{"detail": "Evento não encontrado."}` |
| Participante não existe | 404 | `{"detail": "Participante não encontrado."}` |
| Participante já inscrito | 409 | `{"detail": "Participante já está inscrito neste evento."}` |
| Evento sem vaga | 409 | `{"detail": "Não existem vagas disponíveis para este evento."}` |
| E-mail já cadastrado | 409 | `{"detail": "Já existe um participante cadastrado com este e-mail."}` |
| Capacidade menor que o nº de inscritos | 409 | `{"detail": "A capacidade não pode ser menor que o número de inscritos no evento."}` |
| Dado inválido (e-mail, capacidade ≤ 0, campo vazio, data/hora inválida, categoria inexistente...) | 422 | detalhamento automático do Pydantic |
| Falha inesperada do banco | 500 | `{"detail": "Erro ao processar a operação no banco de dados."}` (sem detalhes técnicos) |

> Na APS 2 "já inscrito" e "sem vaga" retornavam 400. Agora retornam 409 (Conflict), como pede a APS 3.

## Testes

### Automatizados

```bash
python -m pytest -v
```

Usam um banco temporário (não mexem no `eventos.db`) e cobrem: CRUD de eventos e participantes, inscrição,
inscrição duplicada, evento/participante inexistente, evento sem vagas, e-mail duplicado, validações (422),
persistência no arquivo SQLite, os três relatórios, a atualização dos relatórios depois de excluir/atualizar
registros e a exclusão em cascata das inscrições.

### Manuais, pelo Swagger (`/docs`)

1. `POST /eventos` (crie um evento com `capacidade: 1`) e `GET /eventos`.
2. `POST /participantes` (crie dois participantes) e `GET /participantes`.
3. `PUT` e `DELETE` em um evento e um participante de teste.
4. `POST /eventos/{evento_id}/inscricoes/{participante_id}` → 201.
5. Repita o mesmo POST → 409 (já inscrito).
6. Use um `evento_id` que não existe (ex.: 999) → 404.
7. Inscreva o segundo participante no evento de capacidade 1 → 409 (sem vagas).
8. Pare a API (`Ctrl+C`), suba de novo e faça `GET /eventos` → os dados continuam lá.
9. `GET /relatorios/eventos/ocupacao`
10. `GET /relatorios/eventos/categorias`
11. `GET /relatorios/participantes/cursos`
12. Exclua ou atualize registros e consulte os três relatórios de novo: os números acompanham o banco.
