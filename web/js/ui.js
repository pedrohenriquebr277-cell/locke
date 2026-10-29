(function () {
  "use strict";

  const ICON_X = '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" aria-hidden="true"><path d="M4 4l8 8M12 4l-8 8"/></svg>';

  // Renderiza uma lista de chips. onRemove ausente => somente leitura.
  function renderChips(ul, items, onRemove) {
    ul.replaceChildren();
    items.forEach((item) => {
      const li = document.createElement("li");
      li.className = "chip" + (onRemove ? "" : " readonly");
      const span = document.createElement("span");
      span.textContent = item;
      li.appendChild(span);
      if (onRemove) {
        const btn = document.createElement("button");
        btn.type = "button";
        btn.className = "chip-remove";
        btn.setAttribute("aria-label", "Remover " + item);
        btn.innerHTML = ICON_X;
        btn.addEventListener("click", () => onRemove(item));
        li.appendChild(btn);
      }
      ul.appendChild(li);
    });
  }

  // Modal de confirmação com foco preso. Resolve true (Iniciar) ou false (Voltar).
  function confirmStart(rows) {
    return new Promise((resolve) => {
      const previous = document.activeElement;
      const root = document.getElementById("modal-root");
      const overlay = document.createElement("div");
      overlay.className = "overlay";
      overlay.innerHTML =
        '<div class="card modal" role="dialog" aria-modal="true" aria-labelledby="m-title" aria-describedby="m-warn">' +
        '<h2 id="m-title">Pronto para começar?</h2><dl class="summary"></dl>' +
        '<p id="m-warn" class="warning">Depois de iniciar, não é possível cancelar.</p>' +
        '<div class="modal-actions"><button type="button" class="btn btn-secondary" data-act="back">Voltar</button>' +
        '<button type="button" class="btn btn-primary" data-act="go">Iniciar</button></div></div>';
      const dl = overlay.querySelector("dl");
      rows.forEach(([k, v]) => {
        const d = document.createElement("div");
        const dt = document.createElement("dt"); dt.textContent = k;
        const dd = document.createElement("dd"); dd.textContent = v;
        d.append(dt, dd);
        dl.appendChild(d);
      });

      function close(result) {
        document.removeEventListener("keydown", onKey, true);
        overlay.remove();
        if (previous && previous.focus) previous.focus();
        resolve(result);
      }
      function onKey(e) {
        if (e.key === "Escape") { e.preventDefault(); close(false); }
        if (e.key === "Tab") {
          const f = overlay.querySelectorAll("button");
          const first = f[0], last = f[f.length - 1];
          if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
          else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
        }
      }
      overlay.addEventListener("click", (e) => {
        if (e.target === overlay) close(false);
        const act = e.target.closest("[data-act]");
        if (act) close(act.dataset.act === "go");
      });
      document.addEventListener("keydown", onKey, true);
      root.appendChild(overlay);
      overlay.querySelector('[data-act="back"]').focus();
    });
  }

  window.UI = { renderChips, confirmStart };
})();
