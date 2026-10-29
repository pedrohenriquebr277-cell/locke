(function () {
  "use strict";

  const V = window.Validate;
  const $ = (id) => document.getElementById(id);
  const VIEWS = ["loading", "error", "prepare", "active", "done"];
  const RING_C = 2 * Math.PI * 140;

  const ERRORS = {
    service_unavailable: {
      title: "Não consegui falar com o serviço do Locke",
      text: "O serviço do Windows que cuida dos bloqueios não respondeu. Verifique se ele está em execução e tente novamente. Se você já iniciou uma sessão, ela continua protegida.",
    },
    not_admin: {
      title: "Preciso de permissão de administrador",
      text: "Para bloquear sites e apps, o Locke precisa rodar como administrador. Feche o app, clique com o botão direito no ícone e escolha “Executar como administrador”.",
    },
  };

  const PRESETS = [
    { label: "25 min", s: 25 * 60 },
    { label: "50 min", s: 50 * 60 },
    { label: "1 h", s: 3600 },
    { label: "2 h", s: 2 * 3600 },
    { label: "4 h", s: 4 * 3600 },
  ];

  const SUGGEST_SITES = ["youtube.com", "instagram.com", "x.com", "facebook.com", "tiktok.com", "reddit.com", "netflix.com", "twitch.tv", "web.whatsapp.com", "9gag.com"];
  const SUGGEST_APPS = ["discord.exe", "steam.exe", "spotify.exe", "whatsapp.exe", "telegram.exe", "epicgameslauncher.exe"];

  let recentSites = [];
  let recentApps = [];
  let testMode = false;
  let sites = [];
  let apps = [];
  let selectedSeconds = null;
  let currentView = null;
  let lastState = null;
  let clockOffsetMs = 0;       // relógio do backend - relógio local, medido a cada poll
  let timer = null;
  let polling = false;

  // ---------- navegação ----------
  function show(name) {
    currentView = name;
    VIEWS.forEach((v) => { $("view-" + v).hidden = v !== name; });
    if (name !== "active") stopTimer();
  }

  function showError(code) {
    const e = ERRORS[code] || ERRORS.service_unavailable;
    $("error-title").textContent = e.title;
    $("error-text").textContent = e.text;
    show("error");
  }

  async function refresh() {
    const state = await Backend.getState();
    if (!state.ok) return showError(state.error);
    lastState = state;
    syncClock(state);
    if (state.active) return enterActive(state);
    if (state.completed) return enterDone(state);
    return enterPrepare();
  }

  function syncClock(state) {
    if (typeof state.server_now === "number") clockOffsetMs = state.server_now * 1000 - Date.now();
  }

  // ---------- tela 1 ----------
  async function enterPrepare() {
    const cfg = await Backend.getConfig();
    if (!cfg.ok) return showError(cfg.error);
    sites = cfg.sites || [];
    apps = cfg.apps || [];
    recentSites = cfg.recent_sites || [];
    recentApps = cfg.recent_apps || [];
    renderLists();
    renderPresets();
    updateStart();
    show("prepare");
  }

  function renderLists() {
    UI.renderChips($("site-list"), sites, (item) => removeItem("sites", item));
    UI.renderChips($("app-list"), apps, (item) => removeItem("apps", item));
    renderSuggest("site", sites, recentSites, SUGGEST_SITES, "sites");
    renderSuggest("app", apps, recentApps, SUGGEST_APPS, "apps");
  }

  // Mostra "Recentes" e "Sugestões" que ainda não estão na lista atual.
  function renderSuggest(prefix, current, recent, suggested, kind) {
    const taken = (x) => V.hasItem(current, x);
    const recents = recent.filter((x) => !taken(x));
    const sugg = suggested.filter((x) => !taken(x) && !V.hasItem(recent, x)).slice(0, 6);
    [["recent", recents], ["suggest", sugg]].forEach(([suffix, items]) => {
      const box = $(prefix + "-" + suffix);
      const wrap = box.querySelector(".suggest-items");
      wrap.replaceChildren();
      items.forEach((item) => {
        const b = document.createElement("button");
        b.type = "button";
        b.className = "suggest-btn";
        b.textContent = item;
        b.setAttribute("aria-label", "Adicionar " + item);
        b.addEventListener("click", () => addItem(kind, item));
        wrap.appendChild(b);
      });
      box.hidden = items.length === 0;
    });
  }

  async function persist() {
    const res = await Backend.saveConfig(sites, apps);
    if (res.ok) return true;
    if (res.error === "block_active") { refresh(); return false; }
    if (res.error === "not_admin" || res.error === "service_unavailable") { showError(res.error); return false; }
    return false;
  }

  async function removeItem(kind, item) {
    if (kind === "sites") sites = sites.filter((x) => x !== item);
    else apps = apps.filter((x) => x !== item);
    renderLists();
    updateStart();
    await persist();
  }

  function setHint(id, msg, isError) {
    const el = $(id);
    el.textContent = msg || "";
    el.classList.toggle("error", !!isError);
  }

  async function addItem(kind, raw) {
    const isSite = kind === "sites";
    const input = $(isSite ? "site-input" : "app-input");
    const hint = isSite ? "site-hint" : "app-hint";
    const list = isSite ? sites : apps;
    const res = isSite ? V.normalizeDomain(raw) : V.normalizeExe(raw);
    input.classList.toggle("invalid", !res.ok);
    if (!res.ok) return setHint(hint, res.error, true);
    if (V.hasItem(list, res.value)) {
      input.classList.add("invalid");
      return setHint(hint, isSite ? "Esse site já está na lista." : "Esse app já está na lista.", true);
    }
    list.push(res.value);
    input.value = "";
    setHint(hint, "");
    renderLists();
    updateStart();
    await persist();
  }

  function renderPresets() {
    const box = $("presets");
    const items = testMode ? [{ label: "1 min (teste)", s: 60 }, ...PRESETS] : PRESETS;
    box.replaceChildren();
    items.forEach((p) => {
      const b = document.createElement("button");
      b.type = "button";
      b.className = "preset";
      b.textContent = p.label;
      b.dataset.seconds = p.s;
      b.setAttribute("role", "radio");
      b.setAttribute("aria-checked", String(selectedSeconds === p.s));
      b.addEventListener("click", () => {
        $("dur-h").value = "";
        $("dur-m").value = "";
        setDuration(p.s);
      });
      box.appendChild(b);
    });
  }

  function setDuration(seconds) {
    selectedSeconds = seconds;
    document.querySelectorAll("#presets .preset").forEach((b) => {
      b.setAttribute("aria-checked", String(Number(b.dataset.seconds) === seconds));
    });
    const check = V.checkDuration(seconds);
    setHint("dur-hint", check.ok || seconds == null ? "" : check.error, !check.ok);
    updateStart();
  }

  function onCustomDuration() {
    const h = $("dur-h").value, m = $("dur-m").value;
    if (h === "" && m === "") return setDuration(null);
    setDuration(V.customSeconds(h, m));
  }

  function updateStart() {
    const hasItems = sites.length + apps.length > 0;
    const durOk = selectedSeconds != null && V.checkDuration(selectedSeconds).ok;
    $("start").disabled = !(hasItems && durOk);
    setHint("start-hint", !hasItems ? "Adicione ao menos um site ou app para continuar." : !durOk && selectedSeconds == null ? "Escolha uma duração." : "");
  }

  async function onStart() {
    if (!(await persist())) return;
    const ok = await UI.confirmStart([
      ["Sites", String(sites.length)],
      ["Apps", String(apps.length)],
      ["Duração", V.formatDuration(selectedSeconds)],
      ["Término previsto", "às " + V.formatTimeOfDay(Date.now() + clockOffsetMs + selectedSeconds * 1000)],
    ]);
    if (!ok) return;
    $("start").disabled = true;
    const res = await Backend.startBlock(selectedSeconds);
    if (res.ok || res.error === "block_active") return refresh();
    if (res.error === "not_admin" || res.error === "service_unavailable") return showError(res.error);
    setHint("start-hint", res.message || "Não foi possível iniciar agora. Revise as escolhas e tente de novo.", true);
    updateStart();
  }

  // ---------- tela 2 ----------
  function enterActive(state) {
    UI.renderChips($("blocked-sites"), state.blocked_sites || []);
    UI.renderChips($("blocked-apps"), state.blocked_apps || []);
    $("blocked-sites-wrap").hidden = !(state.blocked_sites || []).length;
    $("blocked-apps-wrap").hidden = !(state.blocked_apps || []).length;
    $("ends-at").textContent = "Termina às " + V.formatTimeOfDay(state.ends_at * 1000);
    $("active-banner").hidden = true;
    renderCountdown();
    show("active");
    startTimer();
  }

  function renderCountdown() {
    const s = lastState;
    if (!s || !s.active) return;
    const remaining = s.ends_at - (Date.now() + clockOffsetMs) / 1000;
    const total = s.total_seconds || 1;
    const progress = Math.min(1, Math.max(0, 1 - remaining / total));
    $("countdown").textContent = V.formatClock(remaining);
    const ring = $("ring-progress");
    ring.style.strokeDasharray = RING_C;
    ring.style.strokeDashoffset = RING_C * (1 - progress);
  }

  function startTimer() {
    stopTimer();
    timer = setInterval(tick, 1000);
  }

  function stopTimer() {
    if (timer) clearInterval(timer);
    timer = null;
  }

  async function tick() {
    if (polling) return;
    polling = true;
    try {
      const state = await Backend.getState();
      if (currentView !== "active") return;
      if (!state.ok) {
        $("active-banner").textContent = "Sem resposta do serviço. Tentando de novo… a sessão continua protegida.";
        $("active-banner").hidden = false;
        renderCountdown();
        return;
      }
      $("active-banner").hidden = true;
      lastState = state;
      syncClock(state);
      if (!state.active) return state.completed ? enterDone(state) : enterPrepare();
      renderCountdown();
    } finally {
      polling = false;
    }
  }

  // ---------- tela 3 ----------
  function enterDone(state) {
    const dl = $("done-summary");
    dl.replaceChildren();
    const rows = [["Duração", V.formatDuration(state.total_seconds || 0)]];
    if (typeof state.apps_terminated === "number") {
      rows.push(["Apps encerrados", String(state.apps_terminated)]);
    }
    rows.forEach(([k, v]) => {
      const d = document.createElement("div");
      const dt = document.createElement("dt"); dt.textContent = k;
      const dd = document.createElement("dd"); dd.textContent = v;
      d.append(dt, dd);
      dl.appendChild(d);
    });
    show("done");
  }

  async function onNewSession() {
    const res = await Backend.ackCompleted();
    if (!res.ok) return showError(res.error);
    selectedSeconds = testMode ? 60 : null;
    refresh();
  }

  // ---------- inicialização ----------
  async function toggleFullscreen() {
    const res = await Backend.toggleFullscreen();
    if (res.ok) document.body.classList.toggle("is-fullscreen", !!res.fullscreen);
  }

  function bind() {
    $("site-form").addEventListener("submit", (e) => { e.preventDefault(); addItem("sites", $("site-input").value); });
    $("app-form").addEventListener("submit", (e) => { e.preventDefault(); addItem("apps", $("app-input").value); });
    $("site-input").addEventListener("input", () => { $("site-input").classList.remove("invalid"); setHint("site-hint", ""); });
    $("app-input").addEventListener("input", () => { $("app-input").classList.remove("invalid"); setHint("app-hint", ""); });
    $("app-pick").addEventListener("click", async () => {
      const res = await Backend.pickExecutable();
      if (res.ok) addItem("apps", res.name);
      else if (res.error !== "cancelled") setHint("app-hint", "Não consegui abrir o seletor de arquivos.", true);
    });
    $("dur-h").addEventListener("input", onCustomDuration);
    $("dur-m").addEventListener("input", onCustomDuration);
    $("start").addEventListener("click", onStart);
    $("error-retry").addEventListener("click", () => { show("loading"); refresh(); });
    $("new-session").addEventListener("click", onNewSession);

    $("win-min").addEventListener("click", () => Backend.minimize());
    $("win-max").addEventListener("click", () => Backend.toggleMaximize());
    $("win-close").addEventListener("click", () => Backend.close());

    // Sem atalhos de recarga/devtools: recarregar não deve virar rota de fuga visual.
    document.addEventListener("keydown", (e) => {
      const k = e.key.toLowerCase();
      if (e.key === "F11") { e.preventDefault(); toggleFullscreen(); return; }
      if (e.key === "F5" || e.key === "F12" || (e.ctrlKey && (k === "r" || (e.shiftKey && k === "i")))) e.preventDefault();
    }, true);
    document.addEventListener("contextmenu", (e) => e.preventDefault());
  }

  function mountMascots() {
    const tpl = $("tpl-mascot");
    document.querySelectorAll("[data-mascot]").forEach((el) => el.appendChild(tpl.content.cloneNode(true)));
  }

  async function init() {
    bind();
    mountMascots();
    show("loading");
    const info = await Backend.appInfo();
    testMode = !!info.test_mode;
    if (testMode) selectedSeconds = 60;
    refresh();
  }

  init();
})();
