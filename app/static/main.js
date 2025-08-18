// Animated particles background
        function createParticles() {
            const particlesContainer = document.getElementById('particles');
            const particleCount = 50;
            
            for (let i = 0; i < particleCount; i++) {
                const particle = document.createElement('div');
                particle.className = 'particle';
                particle.style.left = Math.random() * 100 + '%';
                particle.style.top = Math.random() * 100 + '%';
                particle.style.animationDelay = Math.random() * 6 + 's';
                particle.style.animationDuration = (3 + Math.random() * 6) + 's';
                particlesContainer.appendChild(particle);
            }
        }

        const $ = (id) => document.getElementById(id);
        
        const toast = (msg, type = 'info') => {
            const t = $("toast");
            t.textContent = msg;
            t.className = `toast show ${type}`;
            setTimeout(() => t.classList.remove("show"), 3000);
        };

        async function api(path, options = {}) {
            const res = await fetch(path, {
                method: options.method || "GET",
                headers: { "Content-Type": "application/json" },
                body: options.body ? JSON.stringify(options.body) : undefined,
                credentials: "include",
            });
            if (!res.ok) {
                let err = "Erro na requisição";
                try { 
                    const data = await res.json(); 
                    err = data.detail || err; 
                } catch {}
                throw new Error(err);
            }
            const ct = res.headers.get("content-type") || "";
            return ct.includes("application/json") ? res.json() : res.text();
        }

        async function refreshMe() {
            try {
                const me = await api("/api/me");
                $("me").innerHTML = `👋 Olá, <strong>${me.name}</strong> <br><small>${me.email}</small>`;
                $("auth-forms").classList.add("hidden");
                $("me").classList.remove("hidden");
                $("btn-logout").classList.remove("hidden");
                $("tasks-section").classList.remove("hidden");
                $("tasks-section").classList.add("fade-in");
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
            try {
                const list = await api("/api/tasks");
                const ul = $("tasks");
                ul.innerHTML = "";
                
                if (list.length === 0) {
                    ul.innerHTML = '<li style="text-align: center; color: var(--muted); padding: 2rem;">🎯 Nenhuma tarefa ainda. Que tal adicionar sua primeira?</li>';
                    return;
                }

                for (const task of list) {
                    const li = document.createElement("li");
                    li.className = `task-item slide-in ${task.done ? 'completed' : ''}`;
                    
                    const content = document.createElement("div");
                    content.className = "task-content";
                    
                    const title = document.createElement("div");
                    title.className = `task-title ${task.done ? 'completed' : ''}`;
                    title.innerHTML = `
                        ${task.done ? '✅' : '📌'} 
                        ${task.title}
                        <span class="status-badge ${task.done ? 'completed' : 'pending'}">
                            ${task.done ? 'Concluída' : 'Pendente'}
                        </span>
                    `;
                    
                    const desc = document.createElement("div");
                    desc.className = "task-desc";
                    desc.textContent = task.description || "";
                    
                    content.appendChild(title);
                    if (task.description) content.appendChild(desc);
                    
                    const actions = document.createElement("div");
                    actions.className = "task-actions";
                    
                    const btnToggle = document.createElement("button");
                    btnToggle.className = `btn ${task.done ? 'btn-secondary' : 'btn-success'}`;
                    btnToggle.innerHTML = task.done ? '↩️ Reabrir' : '✅ Concluir';
                    btnToggle.onclick = async () => {
                        btnToggle.innerHTML = '<div class="loading"></div>';
                        try {
                            await api(`/api/tasks/${task.id}`, { 
                                method: "PUT", 
                                body: { done: !task.done } 
                            });
                            toast(task.done ? '✅ Tarefa reaberta!' : '🎉 Tarefa concluída!', 'success');
                            await loadTasks();
                        } catch (e) {
                            toast(e.message, 'error');
                        }
                    };
                    
                    const btnEdit = document.createElement("button");
                    btnEdit.className = "btn btn-secondary";
                    btnEdit.innerHTML = '✏️ Editar';
                    btnEdit.onclick = async () => {
                        const title = prompt("✏️ Novo título:", task.title);
                        if (title === null) return;
                        const description = prompt("📝 Nova descrição:", task.description || "");
                        try {
                            await api(`/api/tasks/${task.id}`, { 
                                method: "PUT", 
                                body: { title, description } 
                            });
                            toast('📝 Tarefa atualizada!', 'success');
                            await loadTasks();
                        } catch (e) {
                            toast(e.message, 'error');
                        }
                    };
                    
                    const btnDel = document.createElement("button");
                    btnDel.className = "btn btn-danger";
                    btnDel.innerHTML = '🗑️ Excluir';
                    btnDel.onclick = async () => {
                        if (!confirm('🗑️ Tem certeza que deseja excluir esta tarefa?')) return;
                        try {
                            await api(`/api/tasks/${task.id}`, { method: "DELETE" });
                            toast('🗑️ Tarefa excluída!', 'success');
                            li.style.animation = 'fadeOut 0.3s ease-out forwards';
                            setTimeout(() => loadTasks(), 300);
                        } catch (e) {
                            toast(e.message, 'error');
                        }
                    };
                    
                    actions.appendChild(btnToggle);
                    actions.appendChild(btnEdit);
                    actions.appendChild(btnDel);
                    
                    li.appendChild(content);
                    li.appendChild(actions);
                    ul.appendChild(li);
                }
            } catch (e) {
                toast('Erro ao carregar tarefas: ' + e.message, 'error');
            }
        }

        // Event listeners
        $("btn-register").onclick = async () => {
            const btn = $("btn-register");
            const originalText = btn.textContent;
            const name = $("reg-name").value.trim();
            const email = $("reg-email").value.trim();
            const password = $("reg-password").value;
            
            if (!name || !email || !password) {
                toast("📝 Preencha todos os campos", 'error');
                return;
            }
            
            btn.innerHTML = '<div class="loading"></div>';
            try { 
                await api("/api/auth/register", { 
                    method: "POST", 
                    body: { name, email, password } 
                }); 
                toast("🎉 Conta criada! Agora faça login.", 'success');
                // Clear fields
                $("reg-name").value = "";
                $("reg-email").value = "";
                $("reg-password").value = "";
            } catch (e) { 
                toast(e.message, 'error'); 
            } finally {
                btn.textContent = originalText;
            }
        };

        $("btn-login").onclick = async () => {
            const btn = $("btn-login");
            const originalText = btn.textContent;
            const email = $("login-email").value.trim();
            const password = $("login-password").value;
            
            if (!email || !password) {
                toast("📧 Informe email e senha", 'error');
                return;
            }
            
            btn.innerHTML = '<div class="loading"></div>';
            try { 
                await api("/api/auth/login", { 
                    method: "POST", 
                    body: { email, password } 
                }); 
                toast("🚀 Login realizado com sucesso!", 'success');
                await refreshMe(); 
            } catch (e) { 
                toast(e.message, 'error'); 
            } finally {
                btn.textContent = originalText;
            }
        };

        $("btn-logout").onclick = async () => {
            try {
                await api("/api/auth/logout", { method: "POST" });
                toast("👋 Até logo!", 'success');
                await refreshMe();
            } catch (e) {
                toast(e.message, 'error');
            }
        };

        $("btn-add").onclick = async () => {
            const btn = $("btn-add");
            const originalText = btn.innerHTML;
            const title = $("task-title").value.trim();
            const description = $("task-desc").value.trim();
            
            if (!title) {
                toast("📝 Informe um título para a tarefa", 'error');
                return;
            }
            
            btn.innerHTML = '<div class="loading"></div>';
            try {
                await api("/api/tasks", { 
                    method: "POST", 
                    body: { title, description: description || null } 
                });
                $("task-title").value = "";
                $("task-desc").value = "";
                toast("✨ Tarefa adicionada!", 'success');
                await loadTasks();
            } catch (e) {
                toast(e.message, 'error');
            } finally {
                btn.innerHTML = originalText;
            }
        };

        // Enter key support
        document.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                const activeElement = document.activeElement;
                if (activeElement.id === 'task-title' || activeElement.id === 'task-desc') {
                    $("btn-add").click();
                } else if (activeElement.id === 'login-email' || activeElement.id === 'login-password') {
                    $("btn-login").click();
                } else if (activeElement.id.includes('reg-')) {
                    $("btn-register").click();
                }
            }
        });

        // Initialize
        createParticles();
        refreshMe();

        // CSS for fade out animation
        const style = document.createElement('style');
        style.textContent = `
            @keyframes fadeOut {
                from { opacity: 1; transform: scale(1); }
                to { opacity: 0; transform: scale(0.95) translateY(-10px); }
            }
        `;
        document.head.appendChild(style);