const $ = (id) => document.getElementById(id);
const toast = (msg) => {
    const t = $("toast");
    t.textContent = msg;
    t.classList.remove("hidden");
    setTimeout(() => t.classList.add("hidden"), 2000);
};

async function api(path, options = {}) {
    const res = await fetch(path, {
        method: options.method || "GET",
        headers: { "Content-Type": "application/json" },
        body: options.body ? JSON.stringify(options.body) : undefined,
        credentials: "include",
    });
    if (!res.ok) {
        let err = "Erro";
        try { const data = await res.json(); err = data.detail || err; } catch {}
        throw new Error(err);
    }
    const ct = res.headers.get("content-type") || "";
    return ct.includes("application/json") ? res.json() : res.text();
}

async function refreshMe() {
    try {
        const me = await api("/api/me");
        $("me").textContent = `Logado como: ${me.name} <${me.email}>`;
        $("auth-forms").classList.add("hidden");
        $("me").classList.remove("hidden");
        $("btn-logout").classList.remove("hidden");
        $("tasks-section").classList.remove("hidden");
        await loadTasks();
    } catch {
        $("auth-forms").classList.remove("hidden");
        $("me").classList.add("hidden");
        $("btn-logout").classList.add("hidden");
        $("tasks-section").classList.add("hidden");
        $("tasks").innerHTML = "";
    }
}

async function loadTasks() {
    const list = await api("/api/tasks");
    const ul = $("tasks");
    ul.innerHTML = "";
    for (const task of list) {
        const li = document.createElement("li");
        const left = document.createElement("div");
        left.className = "col";
        const title = document.createElement("div");
        title.className = "task-title";
        title.textContent = task.title + (task.done ? " ✓" : "");
        const desc = document.createElement("div");
        desc.className = "task-desc";
        desc.textContent = task.description || "";
        left.appendChild(title);
        left.appendChild(desc);
        const right = document.createElement("div");
        right.className = "row";
        const btnToggle = document.createElement("button");
        btnToggle.textContent = task.done ? "Reabrir" : "Concluir";
        btnToggle.onclick = async () => {
            await api(`/api/tasks/${task.id}`, { method: "PUT", body: { done: !task.done } });
            await loadTasks();
        };
        const btnEdit = document.createElement("button");
        btnEdit.textContent = "Editar";
        btnEdit.onclick = async () => {
            const title = prompt("Novo título", task.title);
            if (title === null) return;
            const description = prompt("Nova descrição", task.description || "");
            await api(`/api/tasks/${task.id}`, { method: "PUT", body: { title, description } });
            await loadTasks();
        };
        const btnDel = document.createElement("button");
        btnDel.textContent = "Excluir";
        btnDel.onclick = async () => {
            await api(`/api/tasks/${task.id}`, { method: "DELETE" });
            await loadTasks();
        };
        right.appendChild(btnToggle);
        right.appendChild(btnEdit);
        right.appendChild(btnDel);
        li.appendChild(left);
        li.appendChild(right);
        ul.appendChild(li);
    }
}

$("btn-register").onclick = async () => {
    const name = $("reg-name").value.trim();
    const email = $("reg-email").value.trim();
    const password = $("reg-password").value;
    if (!name || !email || !password) return toast("Preencha todos os campos");
    try { await api("/api/auth/register", { method: "POST", body: { name, email, password } }); toast("Conta criada, faça login."); }
    catch (e) { toast(e.message); }
};

$("btn-login").onclick = async () => {
    const email = $("login-email").value.trim();
    const password = $("login-password").value;
    if (!email || !password) return toast("Informe email e senha");
    try { await api("/api/auth/login", { method: "POST", body: { email, password } }); await refreshMe(); }
    catch (e) { toast(e.message); }
};

$("btn-logout").onclick = async () => {
    await api("/api/auth/logout", { method: "POST" });
    await refreshMe();
};

$("btn-add").onclick = async () => {
    const title = $("task-title").value.trim();
    const description = $("task-desc").value.trim();
    if (!title) return toast("Informe um título");
    await api("/api/tasks", { method: "POST", body: { title, description: description || null } });
    $("task-title").value = "";
    $("task-desc").value = "";
    await loadTasks();
};

refreshMe();


