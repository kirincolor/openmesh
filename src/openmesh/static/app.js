const $ = (id) => document.getElementById(id);

const I18N = {
  en: {
    search: "Search",
    settings: "Settings",
    add: "Add",
    addTeammate: "Add teammate",
    newGroup: "New group",
    editGroup: "Edit group",
    manageGroup: "Manage",
    groupName: "Group name",
    members: "Members",
    membersHint: "Pick at least two teammates. You are in the group too.",
    saveGroup: "Save group",
    deleteGroup: "Delete group",
    attach: "Attach",
    uploadFile: "Upload file",
    newDoc: "New document",
    docTitle: "Title",
    docBody: "Document",
    saveDoc: "Save to this chat",
    mention: "Mention someone in this chat",
    fileTooLarge: "File is larger than 10 MB.",
    uploaded: "Uploaded.",
    document: "Document",
    download: "Download",
    send: "Send",
    back: "Back",
    provider: "Provider",
    apis: "API accounts",
    apiName: "Name",
    addApi: "New API",
    saveApi: "Save API",
    deleteApi: "Delete",
    noApis: "No APIs yet. Add one below. The chat header only lists these.",
    confirmDeleteApi: "Remove this API from this machine?",
    computer: "This computer",
    computerHint: "Agents may create files and run commands only in these folders. One path per line.",
    folders: "Folders",
    saveFolders: "Save folders",
    skills: "Skills",
    plugins: "Plugins",
    skillsHint: "Drop SKILL.md files in the skills/ folder. A plugin is a folder with plugin.json.",
    status: "Status",
    model: "Model",
    apiKey: "API key",
    baseUrl: "Base URL",
    saveLocally: "Save locally",
    keyHint: "Keys stay on this machine. Add as many OpenAI-compatible APIs as you want. The header picker uses only this list.",
    apiNamePlaceholder: "OpenAI",
    appearance: "Appearance",
    theme: "Theme",
    light: "Light",
    dark: "Dark",
    language: "Language",
    thisChat: "This chat",
    clearChat: "Clear this chat",
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
    empty: "No messages yet. This is a private chat — other teammates cannot see it.",
    emptyGroup: "No messages yet. Everyone you added can see this group.",
    noKey: "No API key yet. Open Settings (bottom left) and save one to this machine.",
    keyOnDisk: "key on disk",
    noKeyStatus: "no key",
    saved: "Saved.",
    confirmDelete: "Delete this teammate? The workspace folder stays on disk.",
    confirmDeleteGroup: "Delete this group and its messages?",
    confirmClear: "Clear messages in this chat only?",
    lastTeammate: "You need at least one teammate.",
    you: "You",
    talkingTo: "Private chat",
    groupChat: "Group",
    working: "working",
    stop: "Stop",
    schedules: "Schedules",
    scheduleHint: "Repeating or one-off jobs for the current chat. Agents can also create these with schedule_task.",
    scheduleText: "Message",
    everyMinutes: "Every (minutes)",
    cron: "Or cron (m h dom mon dow)",
    addSchedule: "Add schedule",
    title: "Title",
    message: "Message",
    keyPlaceholder: "sk-…",
    urlPlaceholder: "https://api.openai.com/v1",
    modelPlaceholder: "gpt-4o-mini",
    namePlaceholder: "Researcher",
    rolePlaceholder: "What this teammate does, and what they must not do.",
    groupPlaceholder: "Launch crew",
  },
  zh: {
    search: "搜索",
    settings: "设置",
    add: "添加",
    addTeammate: "添加同事",
    newGroup: "新建群聊",
    editGroup: "编辑群聊",
    manageGroup: "管理",
    groupName: "群名称",
    members: "成员",
    membersHint: "至少拉两位同事。你自己也在群里。",
    saveGroup: "保存群聊",
    deleteGroup: "删除群聊",
    attach: "附件",
    uploadFile: "上传文件",
    newDoc: "写文档",
    docTitle: "标题",
    docBody: "正文",
    saveDoc: "保存到当前聊天",
    mention: "点名这个聊天里的人",
    fileTooLarge: "文件超过 10 MB。",
    uploaded: "已上传。",
    document: "文档",
    download: "下载",
    send: "发送",
    back: "返回",
    provider: "模型服务",
    apis: "API 账号",
    apiName: "名称",
    addApi: "新 API",
    saveApi: "保存 API",
    deleteApi: "删除",
    noApis: "还没有 API。在下面添加。聊天顶栏只显示这里配置过的。",
    confirmDeleteApi: "从这台机器删除这个 API？",
    computer: "这台电脑",
    computerHint: "同事只能在这些文件夹里建文件、跑命令。一行一个路径。",
    folders: "文件夹",
    saveFolders: "保存文件夹",
    skills: "Skills",
    plugins: "插件",
    skillsHint: "把 SKILL.md 放到 skills/ 文件夹。插件是带 plugin.json 的文件夹。",
    status: "状态",
    model: "模型",
    apiKey: "API 密钥",
    baseUrl: "接口地址",
    saveLocally: "保存到本机",
    keyHint: "密钥只留在这台机器。可以加多个兼容 OpenAI 的接口。顶栏选择器只用这份列表。",
    apiNamePlaceholder: "OpenAI",
    appearance: "外观",
    theme: "主题",
    light: "浅色",
    dark: "深色",
    language: "语言",
    thisChat: "当前聊天",
    clearChat: "清空当前聊天",
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
    empty: "还没有消息。这是私聊，其他同事看不到。",
    emptyGroup: "还没有消息。你拉进来的人都能看到这个群。",
    noKey: "还没有 API 密钥。点左下角设置，保存到这台机器即可。",
    keyOnDisk: "密钥已在磁盘",
    noKeyStatus: "无密钥",
    saved: "已保存。",
    confirmDelete: "删除这位同事？工作区文件夹会留在磁盘上。",
    confirmDeleteGroup: "删除这个群和群里的消息？",
    confirmClear: "只清空当前这个聊天？",
    lastTeammate: "至少要留一位同事。",
    you: "你",
    talkingTo: "私聊",
    groupChat: "群聊",
    working: "工作中",
    stop: "停止",
    schedules: "定时任务",
    scheduleHint: "给当前聊天加重复或一次性任务。同事也可以用 schedule_task 创建。",
    scheduleText: "到期发送的话",
    everyMinutes: "每隔（分钟）",
    cron: "或 cron（分 时 日 月 周）",
    addSchedule: "添加定时任务",
    title: "标题",
    message: "发消息给",
    keyPlaceholder: "sk-…",
    urlPlaceholder: "https://api.openai.com/v1",
    modelPlaceholder: "gpt-4o-mini",
    namePlaceholder: "研究员",
    rolePlaceholder: "这位同事做什么，以及不该做什么。",
    groupPlaceholder: "上线小组",
  },
};

let state = { agents: [], chats: [], events: [], provider: {}, mesh: {}, running: false, prefs: {}, tools: [], models: {}, schedules: [], busy_threads: [], jobs: [] };
const seen = new Set();
let bannerKind = "";
let selectedChat = localStorage.getItem("openmesh.chat") || "";
let paintedChat = "";
let prefs = { theme: "light", language: "en" };
let searchQuery = "";

function t(key) {
  return (I18N[prefs.language] || I18N.en)[key] || I18N.en[key] || key;
}

function agentById(id) {
  return state.agents.find((a) => a.id === id);
}

function currentChat() {
  return (state.chats || []).find((c) => c.id === selectedChat);
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
    const text = t(node.dataset.i18nTitle);
    node.title = text;
    if (node.tagName === "BUTTON") node.setAttribute("aria-label", text);
  }
  $("search").placeholder = t("search");
  $("api-name").placeholder = t("apiNamePlaceholder");
  $("api-key").placeholder = t("keyPlaceholder");
  $("base-url").placeholder = t("urlPlaceholder");
  $("model").placeholder = t("modelPlaceholder");
  $("agent-name").placeholder = t("namePlaceholder");
  $("agent-role").placeholder = t("rolePlaceholder");
  $("group-name").placeholder = t("groupPlaceholder");
  $("doc-title").placeholder = t("docTitle");
  $("doc-body").placeholder = t("docBody");
  renderMeta();
  renderHeader();
  renderChats();
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

function face(agent, extra) {
  const color = agent?.color || "#6B7280";
  const label = initials(agent?.name || "?");
  return `<span class="avatar ${extra || ""}" style="background:${escapeAttr(color)}">${escapeHtml(label)}</span>`;
}

function chatBusy(chat) {
  return (chat.members || []).some((id) => agentById(id)?.busy);
}

function renderChats() {
  const q = searchQuery.trim().toLowerCase();
  const items = (state.chats || []).filter((c) => {
    if (!q) return true;
    const names = (c.members || []).map((id) => agentById(id)?.name || id).join(" ");
    return [c.id, c.title, c.kind, c.preview, names].join(" ").toLowerCase().includes(q);
  });
  $("agents").innerHTML = items
    .map((c) => {
      const active = c.id === selectedChat ? "active" : "";
      const first = agentById(c.members?.[0]);
      const avatar =
        c.kind === "group"
          ? `<div class="faces">${(c.members || [])
              .slice(0, 2)
              .map((id) => face(agentById(id), "sm"))
              .join("")}</div>`
          : face(first);
      const badge = c.kind === "group" ? `<span class="kind">${escapeHtml(t("groupChat"))}</span>` : "";
      const editKey = c.kind === "group" ? "data-edit-group" : "data-edit";
      const editId = c.kind === "group" ? c.id : c.members?.[0] || "";
      return `<div class="agent-row ${active}" data-chat="${escapeAttr(c.id)}">
        ${avatar}
        <div class="agent-copy">
          <b>${escapeHtml(c.title || first?.name || c.id)}${badge}</b>
          <small>${escapeHtml(chatBusy(c) ? t("working") : c.preview || "")}</small>
        </div>
        <div class="agent-meta">
          <span class="when">${escapeHtml(formatWhen(c.preview_ts))}</span>
          <button type="button" class="edit" ${editKey}="${escapeAttr(editId)}" title="${escapeAttr(c.kind === "group" ? t("editGroup") : t("editTeammate"))}">✎</button>
        </div>
      </div>`;
    })
    .join("");
  for (const row of document.querySelectorAll(".agent-row")) {
    row.addEventListener("click", (ev) => {
      if (ev.target.closest("[data-edit], [data-edit-group]")) return;
      selectChat(row.dataset.chat);
      $("input").focus();
    });
  }
  for (const btn of document.querySelectorAll("[data-edit]")) {
    btn.addEventListener("click", (ev) => {
      ev.stopPropagation();
      openEditor(btn.dataset.edit);
    });
  }
  for (const btn of document.querySelectorAll("[data-edit-group]")) {
    btn.addEventListener("click", (ev) => {
      ev.stopPropagation();
      openGroup(btn.dataset.editGroup);
    });
  }
}

function selectChat(id) {
  selectedChat = id;
  paintedChat = id;
  localStorage.setItem("openmesh.chat", id);
  resetLog();
  for (const event of state.events || []) addEvent(event);
  renderChats();
  renderHeader();
}

function renderHeader() {
  const chat = currentChat();
  const peer = chat?.kind === "dm" ? agentById(chat.members?.[0]) : null;
  $("manage-chat").classList.toggle("hidden", chat?.kind !== "group");
  if (chat?.kind === "group") {
    $("header-avatar").classList.add("hidden");
    $("header-faces").classList.remove("hidden");
    $("header-faces").innerHTML = (chat.members || [])
      .slice(0, 3)
      .map((id) => face(agentById(id), "sm"))
      .join("");
    $("header-name").textContent = chat.title;
    const names = (chat.members || []).map((id) => agentById(id)?.name || id).join(", ");
    $("header-sub").textContent = chatBusy(chat) ? t("working") : `${t("you")}, ${names}`;
    $("input").placeholder = `${t("message")} ${chat.title}`;
    $("empty").textContent = t("emptyGroup");
  } else if (peer) {
    $("header-avatar").classList.remove("hidden");
    $("header-faces").classList.add("hidden");
    $("header-avatar").textContent = initials(peer.name);
    $("header-avatar").style.background = peer.color || "#5B8DEF";
    $("header-name").textContent = peer.name;
    $("header-sub").textContent = peer.busy ? t("working") : `${t("talkingTo")} · @${peer.id}`;
    $("input").placeholder = `${t("message")} ${peer.name}`;
    $("empty").textContent = t("empty");
  }
  $("you-name").textContent = state.mesh?.name || "OpenMesh";
  renderModels();
  const busyHere = (state.busy_threads || []).includes(selectedChat);
  $("stop-job").classList.toggle("hidden", !busyHere);
  $("send").disabled = busyHere;
}

function modelOptions() {
  return (state.models?.options || []).map((item) =>
    typeof item === "string" ? { id: item, label: item } : item
  );
}

function renderModels() {
  const box = $("chat-model");
  const options = modelOptions();
  const ids = options.map((item) => item.id);
  const current = state.models?.by_chat?.[selectedChat] || state.models?.default || ids[0] || "";
  const value = box.value;
  box.innerHTML = options
    .map((item) => `<option value="${escapeAttr(item.id)}">${escapeHtml(item.label || item.id)}</option>`)
    .join("");
  box.value = ids.includes(value) ? value : ids.includes(current) ? current : ids[0] || "";
  box.disabled = !ids.length;
}

function renderSchedules() {
  const items = state.schedules || [];
  $("schedule-list").innerHTML = items.length
    ? items
        .map((item) => {
          const when = item.cron || (item.every_seconds ? `every ${Math.round(item.every_seconds / 60)}m` : "once");
          return `<div class="schedule-row">
            <span><b>${escapeHtml(item.title)}</b><br/><small>${escapeHtml(when)} · ${escapeHtml(item.thread)}</small></span>
            <button type="button" data-cancel-sched="${escapeAttr(item.id)}">×</button>
          </div>`;
        })
        .join("")
    : `<p class="hint">${escapeHtml(t("scheduleHint"))}</p>`;
  for (const btn of document.querySelectorAll("[data-cancel-sched]")) {
    btn.addEventListener("click", async () => {
      await fetch(`/api/schedules/${encodeURIComponent(btn.dataset.cancelSched)}`, { method: "DELETE" });
      await refresh();
    });
  }
}

function accounts() {
  return state.provider?.accounts || [];
}

function renderApis() {
  const items = accounts();
  $("api-list").innerHTML = items.length
    ? items
        .map((item) => {
          const status = item.has_key ? t("keyOnDisk") : t("noKeyStatus");
          return `<div class="schedule-row">
            <span><b>${escapeHtml(item.name)}</b><br/><small>${escapeHtml(item.model)} · ${escapeHtml(status)}</small></span>
            <span class="row-btns">
              <button type="button" data-edit-api="${escapeAttr(item.id)}">✎</button>
              <button type="button" data-del-api="${escapeAttr(item.id)}">×</button>
            </span>
          </div>`;
        })
        .join("")
    : `<p class="hint">${escapeHtml(t("noApis"))}</p>`;
  for (const btn of document.querySelectorAll("[data-edit-api]")) {
    btn.addEventListener("click", () => fillApi(btn.dataset.editApi));
  }
  for (const btn of document.querySelectorAll("[data-del-api]")) {
    btn.addEventListener("click", () => deleteApi(btn.dataset.delApi));
  }
}

function fillApi(id) {
  const item = accounts().find((acc) => acc.id === id);
  if (!item) return;
  $("api-id").value = item.id;
  $("api-name").value = item.name;
  $("base-url").value = item.base_url || "";
  $("model").value = item.model || "";
  $("api-key").value = "";
  $("api-key").placeholder = item.has_key ? t("keyOnDisk") : t("keyPlaceholder");
}

function clearApiForm() {
  $("api-id").value = "";
  $("api-name").value = "";
  $("api-key").value = "";
  $("api-key").placeholder = t("keyPlaceholder");
  $("base-url").value = "";
  $("model").value = "";
}

function renderComputer() {
  const roots = state.computer?.roots || [];
  if (!$("computer-roots").value) $("computer-roots").value = roots.join("\n");
  const skills = (state.skills || []).map((item) => item.id).join(", ");
  const plugins = (state.plugins || []).map((item) => item.id).join(", ");
  $("skill-list-view").textContent = skills || "—";
  $("plugin-list-view").textContent = plugins || "—";
}

function renderMeta() {
  const items = accounts();
  const current = items.find((item) => item.id === state.models?.default) || items[0];
  $("key-status").textContent = state.provider?.has_key ? t("keyOnDisk") : t("noKeyStatus");
  $("key-model").textContent = current ? `${current.name} · ${current.model}` : "—";
  if (!$("api-id").value && !$("api-name").value && current) {
    $("api-name").value = current.name;
    if (!$("base-url").value) $("base-url").value = current.base_url || "";
    if (!$("model").value) $("model").value = current.model || "";
  }
  if (!state.provider?.has_key) setBanner(t("noKey"), "key");
  else if (bannerKind === "key") setBanner("");
  if (!(state.busy_threads || []).includes(selectedChat) && bannerKind === "busy") setBanner("");
  $("send").disabled = (state.busy_threads || []).includes(selectedChat);
  renderApis();
  renderComputer();
  renderSchedules();
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

function renderMembers(selected) {
  const chosen = new Set(selected || []);
  $("member-list").innerHTML = (state.agents || [])
    .map(
      (agent) =>
        `<label><input type="checkbox" value="${escapeAttr(agent.id)}" ${chosen.has(agent.id) ? "checked" : ""}/> ${escapeHtml(agent.name)}</label>`
    )
    .join("");
}

function resetLog() {
  seen.clear();
  const chat = currentChat();
  $("log").innerHTML = `<div id="empty" class="empty">${chat?.kind === "group" ? t("emptyGroup") : t("empty")}</div>`;
}

function addEvent(event) {
  if (!event?.id) return;
  if (!state.events.some((item) => item.id === event.id)) state.events.push(event);
  if (event.thread !== selectedChat) return;
  if (seen.has(event.id)) return;
  seen.add(event.id);
  $("empty")?.classList.add("hidden");
  const log = $("log");
  const el = document.createElement("article");
  el.className = `msg ${event.kind}`;
  const who = event.sender === "you" ? t("you") : agentById(event.sender)?.name || event.sender;
  const dest = event.to ? ` → ${event.to}` : "";
  const fileId = event.meta?.file_id || event.meta?.id;
  if (event.kind === "file" && fileId) {
    const size = prettySize(event.meta.size || 0);
    const kind = event.meta.kind === "doc" ? t("document") : t("download");
    el.innerHTML = `<div class="meta">${escapeHtml(who)}</div>
      <a class="body file-card" href="/api/files/${encodeURIComponent(fileId)}" download="${escapeAttr(event.meta.name || event.text || "file")}">
        <b>${escapeHtml(event.meta.name || event.text || "file")}</b>
        <small>${escapeHtml(size)} · ${escapeHtml(kind)}</small>
      </a>`;
  } else {
    el.innerHTML = `<div class="meta">${escapeHtml(who + dest)}</div>
      <div class="body">${escapeHtml(event.text || "")}</div>`;
  }
  log.appendChild(el);
  log.scrollTop = log.scrollHeight;
}

function prettySize(n) {
  const size = Number(n) || 0;
  if (size < 1024) return `${size} B`;
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`;
  return `${(size / 1024 / 1024).toFixed(1)} MB`;
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

function toggleMenu(id, show) {
  $(id).classList.toggle("hidden", show === undefined ? !$(id).classList.contains("hidden") : !show);
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
  renderTools(agent?.tools || ["handoff", "inbox_list", "inbox_read", "doc_write", "skill_list", "skill_read"]);
  closePage("page-group");
  openPage("page-editor");
}

function openGroup(id) {
  const chat = id ? (state.chats || []).find((c) => c.id === id) : null;
  $("group-id").value = chat?.id || "";
  $("group-name").value = chat?.title || "";
  $("group-title-label").textContent = chat ? t("editGroup") : t("newGroup");
  $("delete-group").classList.toggle("hidden", !chat);
  renderMembers(chat?.members || []);
  closePage("page-editor");
  openPage("page-group");
}

async function refresh() {
  const res = await fetch("/api/state");
  state = await res.json();
  if (!selectedChat || !currentChat()) {
    selectedChat = state.chats?.[0]?.id || "";
    if (selectedChat) localStorage.setItem("openmesh.chat", selectedChat);
  }
  if (selectedChat !== paintedChat) {
    resetLog();
    paintedChat = selectedChat;
  }
  if (state.prefs) applyPrefs({ ...prefs, ...state.prefs });
  else paintI18n();
  for (const event of state.events || []) addEvent(event);
  if (![...$("log").querySelectorAll(".msg")].length) $("empty")?.classList.remove("hidden");
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

function collectedMembers() {
  return [...document.querySelectorAll("#member-list input:checked")].map((node) => node.value);
}

$("search").addEventListener("input", () => {
  searchQuery = $("search").value;
  renderChats();
});

$("add-menu-btn").addEventListener("click", (ev) => {
  ev.stopPropagation();
  toggleMenu("add-menu");
  $("mention-menu").classList.add("hidden");
});
$("add-agent").addEventListener("click", () => {
  $("add-menu").classList.add("hidden");
  openEditor(null);
});
$("add-group").addEventListener("click", () => {
  $("add-menu").classList.add("hidden");
  openGroup(null);
});
$("open-settings").addEventListener("click", () => openPage("page-settings"));
$("close-settings").addEventListener("click", () => closePage("page-settings"));
$("close-editor").addEventListener("click", () => closePage("page-editor"));
$("close-group").addEventListener("click", () => closePage("page-group"));
$("close-doc").addEventListener("click", () => closePage("page-doc"));
$("manage-chat").addEventListener("click", () => openGroup(selectedChat));
$("chat-model").addEventListener("change", async () => {
  if (!selectedChat) return;
  await fetch(`/api/chats/${encodeURIComponent(selectedChat)}/model`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ model: $("chat-model").value }),
  });
});
$("stop-job").addEventListener("click", async () => {
  if (!selectedChat) return;
  await fetch(`/api/chats/${encodeURIComponent(selectedChat)}/stop`, { method: "POST" });
  await refresh();
});
$("save-schedule").addEventListener("click", async () => {
  if (!selectedChat) return;
  const minutes = Number($("sched-every").value);
  const body = {
    title: $("sched-title").value.trim(),
    thread: selectedChat,
    text: $("sched-text").value.trim(),
    every_seconds: minutes > 0 ? Math.round(minutes * 60) : undefined,
    cron: $("sched-cron").value.trim() || undefined,
  };
  const res = await fetch("/api/schedules", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const data = await res.json().catch(() => ({ detail: res.statusText }));
  if (!res.ok) {
    setBanner(data.detail || "schedule failed", "error");
    return;
  }
  $("sched-title").value = "";
  $("sched-text").value = "";
  $("sched-every").value = "";
  $("sched-cron").value = "";
  await refresh();
});

$("mention").addEventListener("click", (ev) => {
  ev.stopPropagation();
  const chat = currentChat();
  const members = chat?.members || [];
  const mentions = members
    .map((id) => {
      const agent = agentById(id);
      return `<button type="button" data-mention="${escapeAttr(id)}">@${escapeHtml(agent?.id || id)} · ${escapeHtml(agent?.name || id)}</button>`;
    })
    .join("");
  $("mention-menu").innerHTML = `
    <button type="button" id="pick-file">${escapeHtml(t("uploadFile"))}</button>
    <button type="button" id="open-doc">${escapeHtml(t("newDoc"))}</button>
    ${mentions}`;
  toggleMenu("mention-menu");
  $("add-menu").classList.add("hidden");
  $("pick-file").addEventListener("click", () => {
    $("mention-menu").classList.add("hidden");
    $("file-input").click();
  });
  $("open-doc").addEventListener("click", () => {
    $("mention-menu").classList.add("hidden");
    $("doc-title").value = "";
    $("doc-body").value = "";
    openPage("page-doc");
  });
  for (const btn of document.querySelectorAll("[data-mention]")) {
    btn.addEventListener("click", () => {
      const box = $("input");
      const tag = `@${btn.dataset.mention} `;
      if (!box.value.includes(tag)) box.value = tag + box.value;
      $("mention-menu").classList.add("hidden");
      box.focus();
    });
  }
});

$("file-input").addEventListener("change", async () => {
  const files = [...($("file-input").files || [])];
  $("file-input").value = "";
  if (!selectedChat || !files.length) return;
  for (const file of files) {
    if (file.size > 10 * 1024 * 1024) {
      setBanner(t("fileTooLarge"), "error");
      continue;
    }
    const body = new FormData();
    body.append("file", file);
    const res = await fetch(`/api/chats/${encodeURIComponent(selectedChat)}/files`, {
      method: "POST",
      body,
    });
    const data = await res.json().catch(() => ({ detail: res.statusText }));
    if (!res.ok) {
      setBanner(data.detail || "upload failed", "error");
      return;
    }
  }
  await refresh();
});

$("doc-form").addEventListener("submit", async (ev) => {
  ev.preventDefault();
  if (!selectedChat) return;
  const res = await fetch(`/api/chats/${encodeURIComponent(selectedChat)}/docs`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title: $("doc-title").value.trim(), content: $("doc-body").value }),
  });
  const data = await res.json().catch(() => ({ detail: res.statusText }));
  if (!res.ok) {
    setBanner(data.detail || "save failed", "error");
    return;
  }
  closePage("page-doc");
  await refresh();
});

document.addEventListener("click", () => {
  $("add-menu").classList.add("hidden");
  $("mention-menu").classList.add("hidden");
});

for (const btn of document.querySelectorAll("#theme-seg [data-theme]")) {
  btn.addEventListener("click", () => savePrefs({ theme: btn.dataset.theme }));
}
for (const btn of document.querySelectorAll("#lang-seg [data-lang]")) {
  btn.addEventListener("click", () => savePrefs({ language: btn.dataset.lang }));
}

$("new-api").addEventListener("click", () => clearApiForm());

$("save-key").addEventListener("click", async () => {
  const existing = $("api-id").value;
  const body = {
    name: $("api-name").value.trim() || "API",
    api_key: $("api-key").value || undefined,
    base_url: $("base-url").value || undefined,
    model: $("model").value || undefined,
  };
  const res = await fetch(existing ? `/api/providers/${encodeURIComponent(existing)}` : "/api/providers", {
    method: existing ? "PUT" : "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const data = await res.json().catch(() => ({ detail: res.statusText }));
  if (!res.ok) {
    setBanner(data.detail || "save failed", "error");
    return;
  }
  $("api-key").value = "";
  if (data.account?.id) $("api-id").value = data.account.id;
  await refresh();
  setBanner(t("saved"), "ok");
});

$("save-computer").addEventListener("click", async () => {
  const roots = $("computer-roots").value.split(/\r?\n/).map((line) => line.trim()).filter(Boolean);
  const res = await fetch("/api/computer", {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ roots }),
  });
  const data = await res.json().catch(() => ({ detail: res.statusText }));
  if (!res.ok) {
    setBanner(data.detail || "save failed", "error");
    return;
  }
  $("computer-roots").value = (data.roots || roots).join("\n");
  await refresh();
  setBanner(t("saved"), "ok");
});

async function deleteApi(id) {
  if (!id || !confirm(t("confirmDeleteApi"))) return;
  const res = await fetch(`/api/providers/${encodeURIComponent(id)}`, { method: "DELETE" });
  const data = await res.json().catch(() => ({ detail: res.statusText }));
  if (!res.ok) {
    setBanner(data.detail || "delete failed", "error");
    return;
  }
  if ($("api-id").value === id) clearApiForm();
  await refresh();
}

$("clear-room").addEventListener("click", async () => {
  if (!selectedChat || !confirm(t("confirmClear"))) return;
  await fetch(`/api/chats/${encodeURIComponent(selectedChat)}/messages`, { method: "DELETE" });
  state.events = (state.events || []).filter((event) => event.thread !== selectedChat);
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
  if (!existing && data.agent?.id) selectedChat = `dm:${data.agent.id}`;
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
  if (selectedChat === `dm:${id}`) selectedChat = "";
  closePage("page-editor");
  await refresh();
});

$("group-form").addEventListener("submit", async (ev) => {
  ev.preventDefault();
  const existing = $("group-id").value;
  const body = { title: $("group-name").value.trim(), members: collectedMembers() };
  const res = await fetch(existing ? `/api/chats/${encodeURIComponent(existing)}` : "/api/chats", {
    method: existing ? "PUT" : "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const data = await res.json().catch(() => ({ detail: res.statusText }));
  if (!res.ok) {
    setBanner(data.detail || "save failed", "error");
    return;
  }
  closePage("page-group");
  if (data.chat?.id) selectChat(data.chat.id);
  await refresh();
});

$("delete-group").addEventListener("click", async () => {
  const id = $("group-id").value;
  if (!id || !confirm(t("confirmDeleteGroup"))) return;
  const res = await fetch(`/api/chats/${encodeURIComponent(id)}`, { method: "DELETE" });
  const data = await res.json().catch(() => ({ detail: res.statusText }));
  if (!res.ok) {
    setBanner(data.detail || "delete failed", "error");
    return;
  }
  if (selectedChat === id) selectedChat = "";
  closePage("page-group");
  await refresh();
});

$("composer").addEventListener("submit", async (ev) => {
  ev.preventDefault();
  const text = $("input").value.trim();
  if (!text || !selectedChat) return;
  const res = await fetch("/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text, thread: selectedChat, model: $("chat-model").value || undefined }),
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
