// Минимальное клиентское приложение Telegram WebApp без фреймворков

const webApp = window.Telegram?.WebApp;
const apiBase = window.location.origin; // предполагается тот же домен, что и backend

const tabsContent = {
  windows: `1) Скачайте v2rayN: https://github.com/2dust/v2rayN/releases
2) Откройте приложение → "Sub" → "Import URL from clipboard"
3) Вставьте ссылку подписки и обновите.`,
  android: `1) Скачайте v2RayTun или Nekoray из Google Play / GitHub.
2) Добавьте подписку через кнопку "Импорт по ссылке".
3) Обновите узлы и выберите любой сервер.`,
  macos: `1) Установите Nekoray для macOS: https://github.com/MatsuriDayo/nekoray/releases
2) Импортируйте подписку по ссылке.
3) Обновите узлы и выберите сервер.`,
  linux: `1) Установите Clash/Clash.Meta или Nekoray для Linux.
2) Добавьте подписку URL и обновите.
3) Запустите клиент и выберите сервер.`,
};

function setStatus(status) {
  const badge = document.getElementById("sub-status");
  badge.textContent = status === "active" ? "Активна" : status === "expired" ? "Истекла" : "Нет подписки";
  badge.classList.remove("active", "expired", "inactive");
  if (status === "active") badge.classList.add("active");
  else if (status === "inactive") badge.classList.add("inactive");
  else badge.classList.add("expired");
}

function setSubscriptionView(data) {
  document.getElementById("sub-id").textContent = data.subscription_id ?? "—";
  document.getElementById("sub-days").textContent =
    data.expires_in_days != null ? `${data.expires_in_days} дн` : "—";
  document.getElementById("sub-url").value = data.sub_url ?? "Нет активной подписки";
  document.getElementById("copy-btn").disabled = !data.sub_url;
  setStatus(data.status || "inactive");
}

async function apiPostAuth(initData) {
  const res = await fetch(`${apiBase}/api/auth/telegram`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ initData }),
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Ошибка аутентификации: ${text}`);
  }
  return res.json();
}

async function apiGetSubscription(initData) {
  const res = await fetch(`${apiBase}/api/me/subscription`, {
    method: "GET",
    headers: {
      "X-Telegram-Init-Data": initData,
    },
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Ошибка загрузки подписки: ${text}`);
  }
  return res.json();
}

function showError(message) {
  const card = document.getElementById("subscription-card");
  let err = card.querySelector(".error");
  if (!err) {
    err = document.createElement("div");
    err.className = "error";
    card.appendChild(err);
  }
  err.textContent = message;
}

function setupTabs() {
  const tabs = document.querySelectorAll(".tab");
  const content = document.getElementById("tab-content");
  const applyContent = (platform) => {
    content.textContent = tabsContent[platform] || "Инструкция будет позже.";
  };

  tabs.forEach((tab) => {
    tab.addEventListener("click", () => {
      tabs.forEach((t) => t.classList.remove("active"));
      tab.classList.add("active");
      applyContent(tab.dataset.platform);
    });
  });

  applyContent("windows");
}

function setupCopy() {
  const btn = document.getElementById("copy-btn");
  btn.addEventListener("click", async () => {
    const text = document.getElementById("sub-url").value;
    try {
      await navigator.clipboard.writeText(text);
      if (webApp?.showPopup) {
        webApp.showPopup({ title: "Скопировано", message: "Ссылка подписки в буфере" });
      }
    } catch (err) {
      showError("Не удалось скопировать ссылку");
    }
  });
}

function setupActions() {
  document.getElementById("download-btn").addEventListener("click", () => {
    webApp?.openLink?.("https://vpn.example.com/app");
  });
  document.getElementById("add-btn").addEventListener("click", () => {
    const url = document.getElementById("sub-url").value;
    webApp?.openLink?.(url);
  });
}

async function init() {
  if (!webApp) {
    showError("Telegram WebApp API недоступно");
    return;
  }
  webApp.ready();
  const initData = webApp.initData;
  if (!initData) {
    showError("initData не найдено");
    return;
  }

  try {
    await apiPostAuth(initData);
    const sub = await apiGetSubscription(initData);
    setSubscriptionView(sub);
  } catch (err) {
    showError(err.message || "Ошибка");
  }
}

setupTabs();
setupCopy();
setupActions();
init();
