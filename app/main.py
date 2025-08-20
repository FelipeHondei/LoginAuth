from typing import Optional
import os

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from .db import get_connection, initialize_database
from .security import create_access_token, decode_access_token, hash_password, verify_password
from .schemas import RegisterRequest, LoginRequest, TaskCreate, TaskUpdate, UserOut, TaskOut


COOKIE_NAME = "access_token"


def get_current_user_id(request: Request) -> Optional[int]:
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        return None
    payload = decode_access_token(token)
    if not payload:
        return None
    try:
        return int(payload.get("sub"))
    except (TypeError, ValueError):
        return None


app = FastAPI(title="Projeto Fullstack")


@app.on_event("startup")
def on_startup() -> None:
    initialize_database()


# CORS para hospedar frontend em outro domínio
allowed_origins_env = os.getenv("ALLOWED_ORIGINS", "")
allowed_origins = []
for o in allowed_origins_env.split(","):
    o = o.strip()
    if not o:
        continue
    # Normaliza removendo barra final
    if o.endswith("/"):
        o = o[:-1]
    allowed_origins.append(o)
if not allowed_origins:
    # Defaults de desenvolvimento/produção (sem barra no final)
    allowed_origins = [
        "http://127.0.0.1:5500",
        "http://localhost:5500",
        "https://loginauthtask.netlify.app",
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Configuração de cookies para cross-site
secure_cookies = os.getenv("SECURE_COOKIES", "true").lower() in ("1", "true", "yes")
samesite_policy = "none" if secure_cookies else "lax"
secure_flag = True if secure_cookies else False


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/api/auth/register")
def register(payload: RegisterRequest):
    with get_connection() as conn:
        with conn.cursor() as cur:
            try:
                cur.execute(
                    "INSERT INTO users (name, email, password_hash) VALUES (%s, %s, %s) RETURNING id",
                    (payload.name, payload.email.lower(), hash_password(payload.password)),
                )
                user_id = cur.fetchone()[0]
                conn.commit()
            except Exception as e:
                conn.rollback()
                raise HTTPException(status_code=400, detail="Email já cadastrado") from e
            return {"id": user_id, "name": payload.name, "email": payload.email}


@app.post("/api/auth/login")
def login(payload: LoginRequest, response: Response):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, password_hash FROM users WHERE email = %s", (payload.email.lower(),))
            row = cur.fetchone()
            if not row or not verify_password(payload.password, row[1]):
                raise HTTPException(status_code=401, detail="Credenciais inválidas")
            token = create_access_token(str(row[0]))
        response = JSONResponse({"ok": True})
        response.set_cookie(
            key=COOKIE_NAME,
            value=token,
            httponly=True,
            samesite=samesite_policy,
            secure=secure_flag,
            max_age=60 * 60 * 24,
            path="/",
        )
        return response


@app.post("/api/auth/logout")
def logout(response: Response):
    # Para remoção confiável em ambiente cross-site, use os mesmos atributos do cookie de login
    response = JSONResponse({"ok": True})
    response.set_cookie(
        key=COOKIE_NAME,
        value="",
        max_age=0,
        expires=0,
        path="/",
        httponly=True,
        samesite=samesite_policy,
        secure=secure_flag,
    )
    return response


@app.get("/api/me", response_model=UserOut)
def me(request: Request):
    user_id = get_current_user_id(request)
    if not user_id:
        raise HTTPException(status_code=401, detail="Não autenticado")
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, name, email FROM users WHERE id = %s", (user_id,))
            row = cur.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Usuário não encontrado")
            return {"id": row[0], "name": row[1], "email": row[2]}


@app.get("/api/tasks", response_model=list[TaskOut])
def list_tasks(request: Request):
    user_id = get_current_user_id(request)
    if not user_id:
        raise HTTPException(status_code=401, detail="Não autenticado")
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, title, description, done FROM tasks WHERE user_id = %s ORDER BY created_at DESC",
                (user_id,),
            )
            rows = cur.fetchall()
    return [
        {
            "id": r[0],
            "title": r[1],
            "description": r[2],
            "done": bool(r[3]),
        }
        for r in rows
    ]


@app.post("/api/tasks", response_model=TaskOut)
def create_task(payload: TaskCreate, request: Request):
    user_id = get_current_user_id(request)
    if not user_id:
        raise HTTPException(status_code=401, detail="Não autenticado")
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO tasks (user_id, title, description) VALUES (%s, %s, %s) RETURNING id, title, description, done",
                (user_id, payload.title, payload.description),
            )
            row = cur.fetchone()
            conn.commit()
            return {
                "id": row[0],
                "title": row[1],
                "description": row[2],
                "done": bool(row[3]),
            }


@app.put("/api/tasks/{task_id}", response_model=TaskOut)
def update_task(task_id: int, payload: TaskUpdate, request: Request):
    user_id = get_current_user_id(request)
    if not user_id:
        raise HTTPException(status_code=401, detail="Não autenticado")
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM tasks WHERE id = %s AND user_id = %s", (task_id, user_id))
            if not cur.fetchone():
                raise HTTPException(status_code=404, detail="Tarefa não encontrada")
            sets = []
            values: list[object] = []
            if payload.title is not None:
                sets.append("title = %s")
                values.append(payload.title)
            if payload.description is not None:
                sets.append("description = %s")
                values.append(payload.description)
            if payload.done is not None:
                sets.append("done = %s")
                values.append(bool(payload.done))
            if not sets:
                raise HTTPException(status_code=400, detail="Nada para atualizar")
            values.append(task_id)
            sql = f"UPDATE tasks SET {', '.join(sets)} WHERE id = %s RETURNING id, title, description, done"
            cur.execute(sql, tuple(values))
            row = cur.fetchone()
            conn.commit()
            return {
                "id": row[0],
                "title": row[1],
                "description": row[2],
                "done": bool(row[3]),
            }


@app.delete("/api/tasks/{task_id}")
def delete_task(task_id: int, request: Request):
    user_id = get_current_user_id(request)
    if not user_id:
        raise HTTPException(status_code=401, detail="Não autenticado")
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM tasks WHERE id = %s AND user_id = %s", (task_id, user_id))
            if cur.rowcount == 0:
                raise HTTPException(status_code=404, detail="Tarefa não encontrada")
            conn.commit()
            return {"ok": True}


# --------- Rotas administrativas (usar Postman com X-Admin-Key) ---------

def _is_admin(request: Request) -> bool:
    admin_key = os.getenv("ADMIN_KEY")
    if not admin_key:
        return False
    provided = request.headers.get("x-admin-key") or request.headers.get("X-Admin-Key")
    return provided == admin_key


@app.get("/api/users")
def list_users(request: Request):
    if not _is_admin(request):
        raise HTTPException(status_code=403, detail="Admin key ausente ou inválida")
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, name, email FROM users ORDER BY created_at DESC")
            rows = cur.fetchall()
            return [
                {"id": r[0], "name": r[1], "email": r[2]}
                for r in rows
            ]


@app.get("/api/users/{user_id}")
def get_user(user_id: int, request: Request):
    if not _is_admin(request):
        raise HTTPException(status_code=403, detail="Admin key ausente ou inválida")
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, name, email FROM users WHERE id = %s", (user_id,))
            row = cur.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Usuário não encontrado")
            return {"id": row[0], "name": row[1], "email": row[2]}


@app.delete("/api/users/{user_id}")
def delete_user(user_id: int, request: Request):
    if not _is_admin(request):
        raise HTTPException(status_code=403, detail="Admin key ausente ou inválida")
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM users WHERE id = %s", (user_id,))
            if cur.rowcount == 0:
                raise HTTPException(status_code=404, detail="Usuário não encontrado")
            conn.commit()
            return {"ok": True}