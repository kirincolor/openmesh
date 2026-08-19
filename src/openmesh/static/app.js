const $ = (id) => document.getElementById(id);
let state = { agents: [], events: [], provider: {}, mesh: {}, running: false };
const seen = new Set();
let bannerKind = "";

function agentById(id) {
  return state.agents.find((a) => a.id === id);
}

function colorOf(id) {
  return agentById(id)?.color || "#8B93A7";
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

function renderAgents() {
  $("agents").innerHTML = state.agents
    .map((a) => {
      const tools = (a.tools || []).map((t) => `<span class="chip">${t}</span>`).join("");
      return `<article class="agent" data-id="${a.id}">
        <div class="agent-top">
          <div class="who"><span class="dot" style="background:${a.color}"></span> ${a.name}</div>
          <div class="busy">${a.busy ? "working" : "@" + a.id}</div>
        </div>
        <div class="role">${(a.role || "").slice(0, 140)}</div>
        <div class="chips">${tools}</div>
      </article>`;
    })
    .join("");
  for (const node of document.querySelectorAll(".agent")) {
    node.addEventListener("click", () => {
      const box = $("input");
      const tag = `@${node.dataset.id} `;
      if (!box.value.includes(tag)) box.value = tag + box.value;
      box.focus();
    });
  }
}

function renderMeta() {
  $("mesh-name").textContent = state.mesh?.name || "openmesh";
  $("key-status").textContent = state.provider?.has_key ? "key on disk" : "no key";
  $("key-model").textContent = state.provider?.model || "—";
  if (!$("base-url").value) $("base-url").value = state.provider?.base_url || "";
  if (!$("model").value) $("model").value = state.provider?.model || "";
  if (!state.provider?.has_key) setBanner("还没有 API key。写在左边，只存在这台机器的 .env。", "key");
  else if (bannerKind === "key") setBanner("");
  if (!state.running && bannerKind === "busy") setBanner("");
  $("composer").querySelector("button").disabled = !!state.running;
}

function resetLog() {
  seen.clear();
  $("log").innerHTML = '<div id="empty" class="empty">房间是空的。先存一把 API key，再派第一件事。</div>';
}

function addEvent(event) {
  if (!event?.id || seen.has(event.id)) return;
  seen.add(event.id);
  state.events.push(event);
  $("empty").classList.add("hidden");
  const log = $("log");
  const el = document.createElement("article");
  el.className = `msg ${event.kind}`;
  const who = event.sender === "you" ? "You" : agentById(event.sender)?.name || event.sender;
  const dest = event.to ? ` → ${event.to}` : "";
  el.innerHTML = `<div class="meta"><span>${who}${dest}</span><span>${event.kind}</span></div>
    <div class="body" style="border-left-color:${colorOf(event.sender)}">${escapeHtml(event.text || "")}</div>`;
  log.appendChild(el);
  log.scrollTop = log.scrollHeight;
}

function escapeHtml(text) {
  return text.replace(/[&<>"']/g, (ch) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;",
  })[ch]);
}

async function refresh() {
  const res = await fetch("/api/state");
  state = await res.json();
  renderAgents();
  renderMeta();
  for (const event of state.events || []) addEvent(event);
  if ((state.events || []).length === 0) $("empty").classList.remove("hidden");
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
  $("key-status").textContent = data.has_key ? "key on disk" : "no key";
  if (data.has_key && (bannerKind === "key" || !bannerKind)) setBanner("");
});

$("clear-room").addEventListener("click", async () => {
  await fetch("/api/room", { method: "DELETE" });
  state.events = [];
  resetLog();
  refresh();
});

$("composer").addEventListener("submit", async (ev) => {
  ev.preventDefault();
  const text = $("input").value.trim();
  if (!text) return;
  const res = await fetch("/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text }),
  });
  if (res.ok) {
    $("input").value = "";
    if (bannerKind === "busy") setBanner("");
    return;
  }
  const data = await res.json().catch(() => ({ detail: res.statusText }));
  const detail = data.detail || "send failed";
  if (res.status === 409) setBanner(detail, "busy");
  else setBanner(detail, "error");
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

listen();
refresh();
