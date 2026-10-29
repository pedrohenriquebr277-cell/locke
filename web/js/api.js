// Wrapper sobre window.pywebview.api: toda chamada devolve um dict, nunca lança.
(function () {
  "use strict";

  const FAIL = { ok: false, error: "service_unavailable" };

  function ready() {
    if (window.pywebview && window.pywebview.api) return Promise.resolve();
    return new Promise((resolve) => window.addEventListener("pywebviewready", resolve, { once: true }));
  }

  async function call(name, ...args) {
    try {
      await ready();
      const res = await window.pywebview.api[name](...args);
      return res && typeof res === "object" ? res : FAIL;
    } catch (e) {
      return FAIL;
    }
  }

  window.Backend = {
    appInfo: () => call("app_info"),
    getState: () => call("get_state"),
    getConfig: () => call("get_config"),
    saveConfig: (sites, apps) => call("save_config", sites, apps),
    startBlock: (seconds) => call("start_block", seconds),
    pickExecutable: () => call("pick_executable"),
    ackCompleted: () => call("ack_completed"),
    minimize: () => call("win_minimize"),
    toggleMaximize: () => call("win_toggle_maximize"),
    toggleFullscreen: () => call("win_toggle_fullscreen"),
    close: () => call("win_close"),
  };
})();
