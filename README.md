## Projeto Fullstack (FastAPI + SQLite + Vanilla JS)

O backend é em Python com FastAPI e SQLite; o frontend é HTML/CSS/JS puro servido pela própria API.

### Funcionalidades
- Autenticação com registro, login e logout (JWT em cookie HttpOnly)
- Endpoints REST para CRUD de tarefas por usuário
- Frontend simples para cadastro/login e gerenciamento de tarefas

### Rotas principais
- `POST /api/auth/register` – cria usuário `{name, email, password}`
- `POST /api/auth/login` – autentica e define cookie de sessão `{email, password}`
- `POST /api/auth/logout` – encerra sessão
- `GET /api/me` – dados do usuário autenticado
- `GET /api/tasks` – lista tarefas do usuário logado
- `POST /api/tasks` – cria tarefa `{title, description?}`
- `PUT /api/tasks/{task_id}` – atualiza tarefa `{title?, description?, done?}`
- `DELETE /api/tasks/{task_id}` – exclui tarefa
