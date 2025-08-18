from typing import Optional

from fastapi import FastAPI, Depends, HTTPException, Request, Response
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

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


app = FastAPI(title="Projeto Fullstack sem npm")


@app.on_event("startup")
def on_startup() -> None:
    initialize_database()


app.mount("/static", StaticFiles(directory="app/static"), name="static")


@app.get("/", response_class=HTMLResponse)
def serve_index() -> HTMLResponse:
    with open("app/static/index.html", "r", encoding="utf-8") as f:
        return HTMLResponse(f.read())


@app.post("/api/auth/register")
def register(payload: RegisterRequest):
    with get_connection() as conn:
        cur = conn.cursor()
        try:
            cur.execute(
                "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
                (payload.name, payload.email.lower(), hash_password(payload.password)),
            )
            conn.commit()
        except Exception as e:
            # Email duplicado
            raise HTTPException(status_code=400, detail="Email já cadastrado") from e
        user_id = cur.lastrowid
        return {"id": user_id, "name": payload.name, "email": payload.email}


@app.post("/api/auth/login")
def login(payload: LoginRequest, response: Response):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id, password_hash FROM users WHERE email = ?", (payload.email.lower(),))
        row = cur.fetchone()
        if not row or not verify_password(payload.password, row["password_hash"]):
            raise HTTPException(status_code=401, detail="Credenciais inválidas")
        token = create_access_token(str(row["id"]))
        response = JSONResponse({"ok": True})
        response.set_cookie(
            key=COOKIE_NAME,
            value=token,
            httponly=True,
            samesite="lax",
            secure=False,
            max_age=60 * 60 * 24,
            path="/",
        )
        return response


@app.post("/api/auth/logout")
def logout(response: Response):
    response = JSONResponse({"ok": True})
    response.delete_cookie(COOKIE_NAME, path="/")
    return response


@app.get("/api/me", response_model=UserOut)
def me(request: Request):
    user_id = get_current_user_id(request)
    if not user_id:
        raise HTTPException(status_code=401, detail="Não autenticado")
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id, name, email FROM users WHERE id = ?", (user_id,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Usuário não encontrado")
        return {"id": row["id"], "name": row["name"], "email": row["email"]}


@app.get("/api/tasks", response_model=list[TaskOut])
def list_tasks(request: Request):
    user_id = get_current_user_id(request)
    if not user_id:
        raise HTTPException(status_code=401, detail="Não autenticado")
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT id, title, description, done FROM tasks WHERE user_id = ? ORDER BY created_at DESC",
            (user_id,),
        )
        rows = cur.fetchall()
    return [
        {
            "id": r["id"],
            "title": r["title"],
            "description": r["description"],
            "done": bool(r["done"]),
        }
        for r in rows
    ]


@app.post("/api/tasks", response_model=TaskOut)
def create_task(payload: TaskCreate, request: Request):
    user_id = get_current_user_id(request)
    if not user_id:
        raise HTTPException(status_code=401, detail="Não autenticado")
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO tasks (user_id, title, description) VALUES (?, ?, ?)",
            (user_id, payload.title, payload.description),
        )
        conn.commit()
        task_id = cur.lastrowid
        cur.execute("SELECT id, title, description, done FROM tasks WHERE id = ?", (task_id,))
        row = cur.fetchone()
        return {
            "id": row["id"],
            "title": row["title"],
            "description": row["description"],
            "done": bool(row["done"]),
        }


@app.put("/api/tasks/{task_id}", response_model=TaskOut)
def update_task(task_id: int, payload: TaskUpdate, request: Request):
    user_id = get_current_user_id(request)
    if not user_id:
        raise HTTPException(status_code=401, detail="Não autenticado")
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id FROM tasks WHERE id = ? AND user_id = ?", (task_id, user_id))
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail="Tarefa não encontrada")
        sets = []
        values: list[object] = []
        if payload.title is not None:
            sets.append("title = ?")
            values.append(payload.title)
        if payload.description is not None:
            sets.append("description = ?")
            values.append(payload.description)
        if payload.done is not None:
            sets.append("done = ?")
            values.append(1 if payload.done else 0)
        if not sets:
            raise HTTPException(status_code=400, detail="Nada para atualizar")
        sets.append("updated_at = CURRENT_TIMESTAMP")
        sql = f"UPDATE tasks SET {', '.join(sets)} WHERE id = ?"
        values.append(task_id)
        cur.execute(sql, tuple(values))
        conn.commit()
        cur.execute("SELECT id, title, description, done FROM tasks WHERE id = ?", (task_id,))
        row = cur.fetchone()
        return {
            "id": row["id"],
            "title": row["title"],
            "description": row["description"],
            "done": bool(row["done"]),
        }


@app.delete("/api/tasks/{task_id}")
def delete_task(task_id: int, request: Request):
    user_id = get_current_user_id(request)
    if not user_id:
        raise HTTPException(status_code=401, detail="Não autenticado")
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM tasks WHERE id = ? AND user_id = ?", (task_id, user_id))
        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="Tarefa não encontrada")
        conn.commit()
        return {"ok": True}


