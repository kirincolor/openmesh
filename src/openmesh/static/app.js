const $ = (id) => document.getElementById(id);

const I18N = {
  en: {
    search: "Search",
    settings: "Settings",
    addTeammate: "Add teammate",
    mention: "Mention a teammate",
    send: "Send",
    back: "Back",
    provider: "Provider",
    status: "Status",
    model: "Model",
    apiKey: "API key",
    baseUrl: "Base URL",
    saveLocally: "Save locally",
    keyHint: "Saved to this machine's .env only. Works with OpenAI, DeepSeek, Groq, or Ollama.",
    appearance: "Appearance",
    theme: "Theme",
    light: "Light",
    dark: "Dark",
    language: "Language",
    room: "Room",
    clearRoom: "Clear room",
    newTeammate: "New teammate",
    editTeammate: "Edit teammate",
    name: "Name",
    id: "ID",
    idHint: "Lowercase letters, numbers, _ or -. Used as @mention.",
    color: "Color",
    role: "Role",
    tools: "Tools",
    saveTeammate: "Save teammate",
    deleteTeammate: "Delete teammate",
    empty: "The room is empty. Open Settings to save an API key, then send the first job.",
    noKey: "No API key yet. Open Settings (bottom left) and save one to this machine.",
    keyOnDisk: "key on disk",
    noKeyStatus: "no key",
    saved: "Saved.",
    confirmDelete: "Delete this teammate? The workspace folder stays on disk.",
    confirmClear: "Clear the room log on this machine?",
    lastTeammate: "You need at least one teammate.",
    you: "You",
    talkingTo: "Talking to",
    chiefRoutes: "Chief routes unless you @mention someone.",
    working: "working",
    message: "Message",
    keyPlaceholder: "sk-…",
    urlPlaceholder: "https://api.openai.com/v1",
    modelPlaceholder: "gpt-4o-mini",
    namePlaceholder: "Researcher",
    rolePlaceholder: "What this teammate does, and what they must not do.",
  },
  zh: {
    search: "搜索",
    settings: "设置",
    addTeammate: "添加同事",
    mention: "点名一位同事",
    send: "发送",
    back: "返回",
    provider: "模型服务",
    status: "状态",
    model: "模型",
    apiKey: "API 密钥",
    baseUrl: "接口地址",
    saveLocally: "保存到本机",
    keyHint: "只写入这台机器的 .env，不会上传。兼容 OpenAI / DeepSeek / Groq / Ollama。",
    appearance: "外观",
    theme: "主题",
    light: "浅色",
    dark: "深色",
    language: "语言",
    room: "房间",
    clearRoom: "清空房间",
    newTeammate: "新同事",
    editTeammate: "编辑同事",
    name: "名称",
    id: "ID",
    idHint: "小写字母、数字、_ 或 -，用作 @点名。",
    color: "颜色",
    role: "职责",
    tools: "工具",
    saveTeammate: "保存同事",
    deleteTeammate: "删除同事",
    empty: "房间是空的。到设置里保存 API 密钥，再派第一件事。",
    noKey: "还没有 API 密钥。点左下角设置，保存到这台机器即可。",
    keyOnDisk: "密钥已在磁盘",
    noKeyStatus: "无密钥",
    saved: "已保存。",
    confirmDelete: "删除这位同事？工作区文件夹会留在磁盘上。",
    confirmClear: "清空这台机器上的房间记录？",
    lastTeammate: "至少要留一位同事。",
    you: "你",
    talkingTo: "正在对话",
    chiefRoutes: "不 @ 任何人时，由主管分派。",
    working: "工作中",
    message: "发消息给",
    keyPlaceholder: "sk-…",
    urlPlaceholder: "https://api.openai.com/v1",
    modelPlaceholder: "gpt-4o-mini",
    namePlaceholder: "研究员",
    rolePlaceholder: "这位同事做什么，以及不该做什么。",
  },
};

let state = { agents: [], events: [], provider: {}, mesh: {}, running: false, prefs: {}, tools: [] };
const seen = new Set();
let bannerKind = "";
let selectedId = "";
let prefs = { theme: "light", language: "en" };
let searchQuery = "";

function t(key) {
  return (I18N[prefs.language] || I18N.en)[key] || I18N.en[key] || key;
}

function agentById(id) {
  return state.agents.find((a) => a.id === id);
}

function selectedAgent() {
  return agentById(selectedId) || agentById(state.mesh?.chief) || state.agents[0];
}

function initials(name) {
  const text = (name || "?").trim();
  if (/[\u4e00-\u9fff]/.test(text)) return text.slice(0, 1);
  const parts = text.split(/\s+/);
  if (parts.length >= 2) return (parts[0][0] + parts[1][0]).toUpperCase();
  return text.slice(0, 2).toUpperCase();
}

function applyPrefs(next) {
  prefs = {
    theme: next?.theme === "dark" ? "dark" : "light",
    language: next?.language === "zh" ? "zh" : "en",
  };
  document.documentElement.dataset.theme = prefs.theme;
  document.documentElement.lang = prefs.language === "zh" ? "zh-CN" : "en";
  localStorage.setItem("openmesh.prefs", JSON.stringify(prefs));
  paintI18n();
}

function paintI18n() {
  for (const node of document.querySelectorAll("[data-i18n]")) {
    node.textContent = t(node.dataset.i18n);
  }
  for (const node of document.querySelectorAll("[data-i18n-title]")) {
    node.title = t(node.dataset.i18nTitle);
  }
  $("search").placeholder = t("search");
  $("api-key").placeholder = t("keyPlaceholder");
  $("base-url").placeholder = t("urlPlaceholder");
  $("model").placeholder = t("modelPlaceholder");
  $("agent-name").placeholder = t("namePlaceholder");
  $("agent-role").placeholder = t("rolePlaceholder");
  $("empty").textContent = t("empty");
  renderMeta();
  renderHeader();
  renderAgents();
}

function setBanner(text, kind) {
  const node = $("banner");
  if (!text) {
    node.classList.add("hidden");
    node.textContent = "";
    bannerKind = "";
    return;
  }
  node.textContent = text;
  node.classList.remove("hidden");
  bannerKind = kind || "";
}

function formatWhen(ts) {
  if (!ts) return "";
  const date = new Date(ts * 1000);
  const now = new Date();
  const sameDay = date.toDateString() === now.toDateString();
  if (sameDay) {
    return date.toLocaleTimeString(prefs.language === "zh" ? "zh-CN" : "en-US", {
      hour: "2-digit",
      minute: "2-digit",
      hour12: false,
    });
  }
  return `${date.getMonth() + 1}/${date.getDate()}`;
}

function renderAgents() {
  const q = searchQuery.trim().toLowerCase();
  const items = (state.agents || []).filter((a) => {
    if (!q) return true;
    return [a.id, a.name, a.role, a.preview].join(" ").toLowerCase().includes(q);
  });
  $("agents").innerHTML = items
    .map((a) => {
      const active = a.id === selectedId ? "active" : "";
      return `<div class="agent-row ${active}" data-id="${escapeAttr(a.id)}">
        <span class="avatar" style="background:${escapeAttr(a.color || "#5B8DEF")}">${escapeHtml(initials(a.name))}</span>
        <div class="agent-copy">
          <b>${escapeHtml(a.name)}</b>
          <small>${escapeHtml(a.busy ? t("working") : a.preview || "@" + a.id)}</small>
        </div>
        <div class="agent-meta">
          <span class="when">${escapeHtml(formatWhen(a.preview_ts))}</span>
          <button type="button" class="edit" data-edit="${escapeAttr(a.id)}" title="${escapeAttr(t("editTeammate"))}">✎</button>
        </div>
      </div>`;
    })
    .join("");
  for (const row of document.querySelectorAll(".agent-row")) {
    row.addEventListener("click", (ev) => {
      if (ev.target.closest("[data-edit]")) return;
      selectedId = row.dataset.id;
      renderAgents();
      renderHeader();
      $("input").focus();
    });
  }
  for (const btn of document.querySelectorAll("[data-edit]")) {
    btn.addEventListener("click", (ev) => {
      ev.stopPropagation();
      openEditor(btn.dataset.edit);
    });
  }
}

function renderHeader() {
  const agent = selectedAgent();
  if (!agent) return;
  $("header-avatar").textContent = initials(agent.name);
  $("header-avatar").style.background = agent.color || "#5B8DEF";
  $("header-name").textContent = agent.name;
  $("header-sub").textContent = agent.busy ? t("working") : `${t("talkingTo")} @${agent.id}`;
  $("input").placeholder = `${t("message")} ${agent.name}`;
  $("you-name").textContent = state.mesh?.name || "OpenMesh";
}

function renderMeta() {
  $("key-status").textContent = state.provider?.has_key ? t("keyOnDisk") : t("noKeyStatus");
  $("key-model").textContent = state.provider?.model || "—";
  if (!$("base-url").value) $("base-url").value = state.provider?.base_url || "";
  if (!$("model").value) $("model").value = state.provider?.model || "";
  if (!state.provider?.has_key) setBanner(t("noKey"), "key");
  else if (bannerKind === "key") setBanner("");
  if (!state.running && bannerKind === "busy") setBanner("");
  $("send").disabled = !!state.running;
  for (const btn of document.querySelectorAll("#theme-seg [data-theme]")) {
    btn.classList.toggle("active", btn.dataset.theme === prefs.theme);
  }
  for (const btn of document.querySelectorAll("#lang-seg [data-lang]")) {
    btn.classList.toggle("active", btn.dataset.lang === prefs.language);
  }
}

function renderTools(selected) {
  const chosen = new Set(selected || []);
  $("tool-list").innerHTML = (state.tools || [])
    .map(
      (tool) => `<label><input type="checkbox" value="${escapeAttr(tool)}" ${chosen.has(tool) ? "checked" : ""}/> ${escapeHtml(tool)}</label>`
    )
    .join("");
}

function resetLog() {
  seen.clear();
  $("log").innerHTML = `<div id="empty" class="empty">${t("empty")}</div>`;
}

function addEvent(event) {
  if (!event?.id || seen.has(event.id)) return;
  seen.add(event.id);
  state.events.push(event);
  $("empty")?.classList.add("hidden");
  const log = $("log");
  const el = document.createElement("article");
  el.className = `msg ${event.kind}`;
  const who = event.sender === "you" ? t("you") : agentById(event.sender)?.name || event.sender;
  const dest = event.to ? ` → ${event.to}` : "";
  el.innerHTML = `<div class="meta">${escapeHtml(who + dest)}</div>
    <div class="body">${escapeHtml(event.text || "")}</div>`;
  log.appendChild(el);
  log.scrollTop = log.scrollHeight;
}

function escapeHtml(text) {
  return String(text).replace(/[&<>"']/g, (ch) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;",
  })[ch]);
}

function escapeAttr(text) {
  return escapeHtml(text);
}

function openPage(id) {
  $(id).classList.remove("hidden");
  $(id).setAttribute("aria-hidden", "false");
}

function closePage(id) {
  $(id).classList.add("hidden");
  $(id).setAttribute("aria-hidden", "true");
}

function openEditor(id) {
  const agent = id ? agentById(id) : null;
  $("edit-id").value = agent ? agent.id : "";
  $("agent-name").value = agent?.name || "";
  $("agent-slug").value = agent?.id || "";
  $("agent-slug").readOnly = Boolean(agent);
  $("agent-color").value = agent?.color || "#5B8DEF";
  $("agent-role").value = agent?.role || "";
  $("editor-title").textContent = agent ? t("editTeammate") : t("newTeammate");
  $("delete-agent").classList.toggle("hidden", !agent);
  renderTools(agent?.tools || ["handoff"]);
  openPage("page-editor");
}

async function refresh() {
  const res = await fetch("/api/state");
  state = await res.json();
  if (!selectedId || !agentById(selectedId)) {
    selectedId = state.mesh?.chief || state.agents[0]?.id || "";
  }
  if (state.prefs) applyPrefs({ ...prefs, ...state.prefs });
  else paintI18n();
  for (const event of state.events || []) addEvent(event);
  if ((state.events || []).length === 0) $("empty")?.classList.remove("hidden");
}

async function savePrefs(partial) {
  applyPrefs({ ...prefs, ...partial });
  await fetch("/api/prefs", {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(partial),
  });
}

function collectedTools() {
  return [...document.querySelectorAll("#tool-list input:checked")].map((node) => node.value);
}

$("search").addEventListener("input", () => {
  searchQuery = $("search").value;
  renderAgents();
});

$("add-agent").addEventListener("click", () => openEditor(null));
$("open-settings").addEventListener("click", () => openPage("page-settings"));
$("close-settings").addEventListener("click", () => closePage("page-settings"));
$("close-editor").addEventListener("click", () => closePage("page-editor"));

$("mention").addEventListener("click", () => {
  const agent = selectedAgent();
  if (!agent) return;
  const box = $("input");
  const tag = `@${agent.id} `;
  if (!box.value.includes(tag)) box.value = tag + box.value;
  box.focus();
});

for (const btn of document.querySelectorAll("#theme-seg [data-theme]")) {
  btn.addEventListener("click", () => savePrefs({ theme: btn.dataset.theme }));
}
for (const btn of document.querySelectorAll("#lang-seg [data-lang]")) {
  btn.addEventListener("click", () => savePrefs({ language: btn.dataset.lang }));
}

$("save-key").addEventListener("click", async () => {
  const body = {
    api_key: $("api-key").value || undefined,
    base_url: $("base-url").value || undefined,
    model: $("model").value || undefined,
  };
  const res = await fetch("/api/secrets", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const data = await res.json();
  $("api-key").value = "";
  state.provider = { ...state.provider, has_key: data.has_key, model: $("model").value || state.provider.model };
  renderMeta();
  if (data.has_key && (bannerKind === "key" || !bannerKind)) setBanner(t("saved"), "ok");
});

$("clear-room").addEventListener("click", async () => {
  if (!confirm(t("confirmClear"))) return;
  await fetch("/api/room", { method: "DELETE" });
  state.events = [];
  resetLog();
  await refresh();
});

$("agent-form").addEventListener("submit", async (ev) => {
  ev.preventDefault();
  const existing = $("edit-id").value;
  const body = {
    id: $("agent-slug").value.trim() || undefined,
    name: $("agent-name").value.trim(),
    role: $("agent-role").value,
    color: $("agent-color").value,
    tools: collectedTools(),
  };
  const res = await fetch(existing ? `/api/agents/${encodeURIComponent(existing)}` : "/api/agents", {
    method: existing ? "PUT" : "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const data = await res.json().catch(() => ({ detail: res.statusText }));
  if (!res.ok) {
    setBanner(data.detail || "save failed", "error");
    return;
  }
  if (!existing && data.agent?.id) selectedId = data.agent.id;
  closePage("page-editor");
  await refresh();
});

$("delete-agent").addEventListener("click", async () => {
  const id = $("edit-id").value;
  if (!id) return;
  if (state.agents.length <= 1) {
    setBanner(t("lastTeammate"), "error");
    return;
  }
  if (!confirm(t("confirmDelete"))) return;
  const res = await fetch(`/api/agents/${encodeURIComponent(id)}`, { method: "DELETE" });
  const data = await res.json().catch(() => ({ detail: res.statusText }));
  if (!res.ok) {
    setBanner(data.detail || "delete failed", "error");
    return;
  }
  if (selectedId === id) selectedId = data.chief || "";
  closePage("page-editor");
  await refresh();
});

$("composer").addEventListener("submit", async (ev) => {
  ev.preventDefault();
  const text = $("input").value.trim();
  if (!text) return;
  const res = await fetch("/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text, to: selectedId || undefined }),
  });
  if (res.ok) {
    $("input").value = "";
    if (bannerKind === "busy") setBanner("");
    return;
  }
  const data = await res.json().catch(() => ({ detail: res.statusText }));
  setBanner(data.detail || "send failed", res.status === 409 ? "busy" : "error");
});

$("input").addEventListener("keydown", (ev) => {
  if (ev.key === "Enter" && !ev.shiftKey) {
    ev.preventDefault();
    $("composer").requestSubmit();
  }
});

function listen() {
  const stream = new EventSource("/api/stream");
  stream.onmessage = (msg) => {
    const data = JSON.parse(msg.data);
    if (data.hello) return;
    addEvent(data);
    if (data.kind === "status") refresh();
  };
  stream.onerror = () => {
    stream.close();
    setTimeout(listen, 1500);
  };
}

applyPrefs(JSON.parse(localStorage.getItem("openmesh.prefs") || "{}"));
listen();
refresh();
