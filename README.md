## Projeto Fullstack sem npm (FastAPI + SQLite + Vanilla JS)

Este projeto demonstra habilidades fullstack sem utilizar npm. O backend é em Python com FastAPI e SQLite; o frontend é HTML/CSS/JS puro servido pela própria API.

### Funcionalidades
- Autenticação com registro, login e logout (JWT em cookie HttpOnly)
- Endpoints REST para CRUD de tarefas por usuário
- Frontend simples para cadastro/login e gerenciamento de tarefas

### Requisitos
- Python 3.10+

### Como rodar (backend + frontend juntos no mesmo host)
1. Crie e ative um ambiente virtual (opcional, porém recomendado):
   - PowerShell (Windows):
     ```powershell
     python -m venv .venv
     .venv\\Scripts\\Activate.ps1
     ```
2. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```
3. Inicie o servidor (hot-reload para desenvolvimento):
   ```bash
   uvicorn app.main:app --reload
   ```
4. Acesse o frontend em `http://127.0.0.1:8000/`.

### Rodar frontend separadamente
1. Copie `frontend/config.example.js` para `frontend/config.js` e ajuste `window.API_BASE_URL` para a URL do backend (ex.: `http://127.0.0.1:8000`).
2. Sirva a pasta `frontend/` com qualquer servidor estático. Exemplo via Python:
   ```bash
   cd frontend
   python -m http.server 5500
   ```
3. Abra `http://127.0.0.1:5500/` no navegador.

Para produção em domínios diferentes, defina no backend as variáveis:
- `ALLOWED_ORIGINS`: lista separada por vírgula com as origens do frontend, por exemplo: `https://seu-frontend.hf.space,https://seu-frontend.netlify.app`
- `SECURE_COOKIES=true` quando usar HTTPS em ambos os lados para permitir `SameSite=None`.

### Rotas principais
- `POST /api/auth/register` – cria usuário `{name, email, password}`
- `POST /api/auth/login` – autentica e define cookie de sessão `{email, password}`
- `POST /api/auth/logout` – encerra sessão
- `GET /api/me` – dados do usuário autenticado
- `GET /api/tasks` – lista tarefas do usuário logado
- `POST /api/tasks` – cria tarefa `{title, description?}`
- `PUT /api/tasks/{task_id}` – atualiza tarefa `{title?, description?, done?}`
- `DELETE /api/tasks/{task_id}` – exclui tarefa

### Documentação automática
Após iniciar, verifique a documentação interativa em `http://127.0.0.1:8000/docs`.

### Notas
- Sem npm: o frontend é estático e não utiliza bundlers ou pacotes do Node.
- Banco de dados: arquivo SQLite criado automaticamente em `app/data.sqlite3`.
- Para alterar a chave JWT, defina a variável de ambiente `SECRET_KEY`.


