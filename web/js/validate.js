(function (root) {
  "use strict";

  const MAX_SECONDS = 8 * 3600;
  const LABEL = /^(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?)$/;

  // Normaliza uma entrada de site para um domínio puro. Retorna {ok, value|error}.
  function normalizeDomain(input) {
    let s = String(input || "").trim().toLowerCase();
    if (!s) return { ok: false, error: "Digite um endereço, como exemplo.com." };
    s = s.replace(/^[a-z][a-z0-9+.-]*:\/\//, "");   // protocolo
    s = s.split(/[/?#]/)[0];                          // caminho, query, hash
    s = s.replace(/^.*@/, "");                        // usuário:senha@
    s = s.replace(/:\d+$/, "");                       // porta
    s = s.replace(/^www\./, "").replace(/\.$/, "");
    const labels = s.split(".");
    const tld = labels[labels.length - 1];
    if (labels.length < 2 || !labels.every((l) => LABEL.test(l)) || !/^([a-z]{2,}|xn--[a-z0-9-]+)$/.test(tld) || s.length > 253) {
      return { ok: false, error: "Esse endereço não parece válido. Tente algo como exemplo.com." };
    }
    return { ok: true, value: s };
  }

  // Normaliza o nome de um executável (sem caminho). Retorna {ok, value|error}.
  function normalizeExe(input) {
    let s = String(input || "").trim().replace(/^["']|["']$/g, "");
    if (!s) return { ok: false, error: "Digite o nome do programa, como discord.exe." };
    s = s.split(/[\\/]/).pop().trim();
    if (!/\.exe$/i.test(s)) {
      if (s.includes(".")) return { ok: false, error: "Só consigo bloquear arquivos .exe." };
      s += ".exe";
    }
    if (/[<>:"|?*\x00-\x1f]/.test(s) || s.length < 5 || s.length > 128) {
      return { ok: false, error: "Esse nome de programa não parece válido." };
    }
    return { ok: true, value: s.toLowerCase() };
  }

  function hasItem(list, value) {
    return list.some((x) => x.toLowerCase() === value.toLowerCase());
  }

  // Duração em segundos a partir de horas/minutos (strings ou números).
  function customSeconds(hours, minutes) {
    const h = hours === "" || hours == null ? 0 : Number(hours);
    const m = minutes === "" || minutes == null ? 0 : Number(minutes);
    if (!Number.isFinite(h) || !Number.isFinite(m) || h < 0 || m < 0) return NaN;
    return Math.round(h * 3600 + m * 60);
  }

  // {ok, seconds} | {ok:false, error}
  function checkDuration(seconds) {
    if (!Number.isFinite(seconds) || seconds <= 0) return { ok: false, error: "" };
    if (seconds > MAX_SECONDS) {
      return { ok: false, error: "O limite é de 8 horas. Faça uma pausa no meio do caminho — você merece." };
    }
    return { ok: true, seconds: seconds };
  }

  function formatClock(totalSeconds) {
    const t = Math.max(0, Math.ceil(totalSeconds));
    const p = (n) => String(n).padStart(2, "0");
    return p(Math.floor(t / 3600)) + ":" + p(Math.floor((t % 3600) / 60)) + ":" + p(t % 60);
  }

  function formatDuration(seconds) {
    const h = Math.floor(seconds / 3600);
    const m = Math.round((seconds % 3600) / 60);
    if (!h) return m === 1 ? "1 minuto" : m + " minutos";
    if (!m) return h === 1 ? "1 hora" : h + " horas";
    return h + " h " + m + " min";
  }

  function formatTimeOfDay(epochMs) {
    return new Date(epochMs).toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" });
  }

  const api = {
    MAX_SECONDS, normalizeDomain, normalizeExe, hasItem, customSeconds,
    checkDuration, formatClock, formatDuration, formatTimeOfDay,
  };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  else root.Validate = api;
})(typeof window !== "undefined" ? window : globalThis);
