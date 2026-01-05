// Админ-интерфейс Telegram WebApp для управления серверами
const webApp = window.Telegram?.WebApp;
const apiBase = window.location.origin;

const state = {
  initData: "",
  servers: [],
  editingId: null,
};

const formEl = document.getElementById("server-form");
const formTitleEl = document.getElementById("form-title");
const serversTbody = document.getElementById("servers-tbody");

function showError(message) {
  webApp?.showAlert?.(message);
}

function notify(message) {
  webApp?.showPopup?.({ title: "Успех", message });
}

async function apiAuth() {
  const res = await fetch(`${apiBase}/api/auth/telegram`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ initData: state.initData }),
  });
  if (!res.ok) {
    throw new Error("Ошибка аутентификации");
  }
  return res.json();
}

async function apiGetServers() {
  const res = await fetch(`${apiBase}/api/admin/servers`, {
    headers: { "X-Telegram-Init-Data": state.initData },
  });
  if (!res.ok) {
    throw new Error("Не удалось загрузить сервера");
  }
  return res.json();
}

async function apiCreateServer(payload) {
  const res = await fetch(`${apiBase}/api/admin/servers`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Telegram-Init-Data": state.initData,
    },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || "Не удалось создать сервер");
  }
  return res.json();
}

async function apiUpdateServer(id, payload) {
  const res = await fetch(`${apiBase}/api/admin/servers/${id}`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
      "X-Telegram-Init-Data": state.initData,
    },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || "Не удалось обновить сервер");
  }
  return res.json();
}

async function apiPatchServer(id, payload) {
  const res = await fetch(`${apiBase}/api/admin/servers/${id}`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
      "X-Telegram-Init-Data": state.initData,
    },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || "Не удалось обновить сервер");
  }
  return res.json();
}

async function apiDeleteServer(id) {
  const res = await fetch(`${apiBase}/api/admin/servers/${id}`, {
    method: "DELETE",
    headers: { "X-Telegram-Init-Data": state.initData },
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || "Не удалось удалить сервер");
  }
}

function renderServers() {
  if (!state.servers.length) {
    serversTbody.innerHTML = `<tr><td colspan="9" class="muted">Серверов пока нет</td></tr>`;
    return;
  }

  serversTbody.innerHTML = "";
  state.servers.forEach((srv) => {
    const tr = document.createElement("tr");

    tr.innerHTML = `
      <td>${srv.id}</td>
      <td>${srv.country_code}</td>
      <td>${srv.name ?? "—"}</td>
      <td>${srv.host}</td>
      <td>${srv.port}</td>
      <td>${srv.network}</td>
      <td>${srv.sni ?? "—"}</td>
      <td>
        <label class="switch">
          <input type="checkbox" ${srv.enabled ? "checked" : ""} data-id="${srv.id}" class="toggle-enabled" />
          <span class="badge-table ${srv.enabled ? "enabled" : "disabled"}">${srv.enabled ? "On" : "Off"}</span>
        </label>
      </td>
      <td>
        <button class="action-btn action-small" data-id="${srv.id}" data-action="edit">Редактировать</button>
        <button class="action-btn action-small secondary" data-id="${srv.id}" data-action="delete">Удалить</button>
      </td>
    `;

    serversTbody.appendChild(tr);
  });
}

function fillForm(server) {
  formTitleEl.textContent = server ? `Редактирование #${server.id}` : "Новый сервер";
  document.getElementById("server-id").value = server?.id ?? "";
  document.getElementById("country_code").value = server?.country_code ?? "";
  document.getElementById("name").value = server?.name ?? "";
  document.getElementById("host").value = server?.host ?? "";
  document.getElementById("port").value = server?.port ?? "";
  document.getElementById("network").value = server?.network ?? "tcp";
  document.getElementById("public_key").value = server?.public_key ?? "";
  document.getElementById("sni").value = server?.sni ?? "";
  document.getElementById("enabled").checked = server?.enabled ?? true;
}

function resetForm() {
  state.editingId = null;
  formEl.reset();
  fillForm(null);
}

async function loadServers() {
  try {
    state.servers = await apiGetServers();
    renderServers();
  } catch (err) {
    showError(err.message || "Ошибка при загрузке серверов");
  }
}

async function handleSave(e) {
  e.preventDefault();
  const payload = {
    country_code: document.getElementById("country_code").value.trim(),
    name: document.getElementById("name").value.trim() || null,
    host: document.getElementById("host").value.trim(),
    port: Number(document.getElementById("port").value),
    network: document.getElementById("network").value,
    public_key: document.getElementById("public_key").value.trim(),
    sni: document.getElementById("sni").value.trim() || null,
    enabled: document.getElementById("enabled").checked,
  };

  try {
    if (state.editingId) {
      await apiUpdateServer(state.editingId, payload);
      notify("Сервер обновлен");
    } else {
      await apiCreateServer(payload);
      notify("Сервер добавлен");
    }
    resetForm();
    await loadServers();
  } catch (err) {
    showError(err.message || "Ошибка сохранения");
  }
}

function handleTableClick(e) {
  const action = e.target.dataset.action;
  const id = Number(e.target.dataset.id);
  if (!action || !id) return;

  const server = state.servers.find((s) => s.id === id);
  if (!server) return;

  if (action === "edit") {
    state.editingId = id;
    fillForm(server);
  } else if (action === "delete") {
    webApp?.showPopup?.(
      {
        title: "Удалить сервер?",
        message: `#${id} (${server.host}) будет удален`,
        buttons: [
          { id: "delete", type: "destructive", text: "Удалить" },
          { id: "cancel", type: "default", text: "Отмена" },
        ],
      },
      async (btnId) => {
        if (btnId === "delete") {
          try {
            await apiDeleteServer(id);
            notify("Сервер удален");
            await loadServers();
          } catch (err) {
            showError(err.message || "Ошибка удаления");
          }
        }
      }
    );
  }
}

async function handleToggle(e) {
  if (!e.target.classList.contains("toggle-enabled")) return;
  const id = Number(e.target.dataset.id);
  const enabled = e.target.checked;
  try {
    await apiPatchServer(id, { enabled });
    await loadServers();
  } catch (err) {
    showError(err.message || "Ошибка обновления статуса");
  }
}

async function bootstrap() {
  if (!webApp) {
    showError("Telegram WebApp API недоступно");
    return;
  }
  webApp.ready();
  state.initData = webApp.initData;
  if (!state.initData) {
    showError("initData не найдено");
    return;
  }

  const accessCard = document.getElementById("access-card");
  accessCard.hidden = false;

  try {
    const { role } = await apiAuth();
    if (role !== "admin") {
      document.getElementById("access-message").textContent = "Доступ запрещен. Нужна роль admin.";
      document.getElementById("servers-card").hidden = true;
      document.getElementById("form-card").hidden = true;
      return;
    }

    accessCard.hidden = true;
    await loadServers();
  } catch (err) {
    document.getElementById("access-message").textContent = "Ошибка авторизации";
    showError(err.message || "Ошибка авторизации");
  }
}

document.getElementById("back-btn").addEventListener("click", () => {
  window.location.href = "index.html";
});

document.getElementById("refresh-btn").addEventListener("click", loadServers);
formEl.addEventListener("submit", handleSave);
document.getElementById("cancel-btn").addEventListener("click", resetForm);
serversTbody.addEventListener("click", handleTableClick);
serversTbody.addEventListener("change", handleToggle);

bootstrap();
