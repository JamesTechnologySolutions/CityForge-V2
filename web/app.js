/**
 * Cityforge 2 - thin JavaScript UI controller.
 *
 * This module only owns the modern web UI chrome (toolbar, panels, toasts,
 * tooltips, layer toggles).  All simulation state lives in Python; this
 * script talks to it through the pywebview JS bridge or custom events.
 */
(function () {
  "use strict";

  const api = window.pywebview && window.pywebview.api ? window.pywebview.api : null;

  const state = {
    tool: "road",
    layer: null,
    speed: 1,
    tax: 9,
    disasters: true,
    sound: true,
  };

  const tools = [
    ["Build", ["road"]],
    ["Zones", ["res", "com", "ind"]],
    ["Services", ["power", "solar", "water", "park", "school", "clinic", "hospital", "police", "fire"]],
    ["Tools", ["bull"]],
  ];

  function $(id) { return document.getElementById(id); }

  function renderTools() {
    const box = $("tools");
    box.innerHTML = "";
    for (const group of tools) {
      const h = document.createElement("h4");
      h.textContent = group[0];
      box.appendChild(h);
      for (const kind of group[1]) {
        const button = document.createElement("button");
        button.dataset.tool = kind;
        const colors = { road: "#46515c", res: "#58b86f", com: "#4f93e0", ind: "#e0a93f", bull: "#b4503f" };
        button.innerHTML = `<i class="sw" style="background:${colors[kind] || "#999"}"></i><span></span><span></span>`;
        button.addEventListener("click", () => setTool(kind));
        box.appendChild(button);
      }
    }
  }

  function setTool(kind) {
    state.tool = kind;
    for (const button of document.querySelectorAll("#tools button")) {
      button.classList.toggle("on", button.dataset.tool === kind);
    }
    if (api) { api.set_tool(kind); }
  }

  function setLayer(layer) {
    state.layer = layer;
    for (const button of document.querySelectorAll("#layers button")) {
      button.classList.toggle("on", button.dataset.layer === String(layer));
    }
    if (api) { api.set_layer(layer); }
  }

  function setSpeed(speed) {
    state.speed = speed;
    for (const button of document.querySelectorAll(".sp")) {
      button.classList.toggle("on", Number(button.dataset.s) === speed);
    }
    if (api) { api.set_speed(speed); }
  }

  function syncFromApi() {
    const data = api ? api.get_state() : null;
    if (!data) { return; }
    state.tax = data.tax || 9;
    state.speed = data.speed || 1;
    $("tax").value = state.tax;
    $("taxv").textContent = `${state.tax}%`;
    $("money").textContent = `$${Math.round(data.money || 0)}`;
    $("date").textContent = `${data.date || ""} Y${data.year || 1}`;
    $("pop").textContent = Math.round(data.pop || 0).toLocaleString();
    $("jobs").textContent = Math.round(data.jobs || 0);
    $("happy").textContent = `${Math.round(data.happy || 0)}%`;
    $("rank").textContent = data.rank_name || "Hamlet";
    const bar = (id, value) => { const el = $(id); if (el) { el.style.width = `${((value || 0) + 1) * 50}%`; } };
    bar("d_r", data.dem && data.dem.r);
    bar("d_c", data.dem && data.dem.c);
    bar("d_i", data.dem && data.dem.i);
  }

  function init() {
    renderTools();
    for (const button of document.querySelectorAll("#layers button")) {
      button.addEventListener("click", () => setLayer(button.dataset.layer === "null" ? null : button.dataset.layer));
    }
    for (const button of document.querySelectorAll(".sp")) {
      button.addEventListener("click", () => setSpeed(Number(button.dataset.s)));
    }
    const tax = $("tax");
    tax.addEventListener("input", () => { state.tax = Number(tax.value); $("taxv").textContent = `${tax.value}%`; if (api) { api.set_tax(tax.value); } });
    const cname = $("cname");
    cname.addEventListener("input", () => { if (api) { api.set_name(cname.value); } });
    for (const id of ["save", "load", "new"]) {
      $(id).addEventListener("click", () => { if (api) { api["on_" + id](); } });
    }
    const dis = $("dis");
    dis.addEventListener("change", () => { state.disasters = dis.checked; if (api) { api.set_disasters(dis.checked); } });
    const snd = $("snd");
    snd.addEventListener("change", () => { state.sound = snd.checked; if (api) { api.set_sound(snd.checked); } });
    const boom = $("boom");
    boom.addEventListener("click", () => { if (api) { api.trigger_disaster(); } });
    window.setInterval(syncFromApi, 250);
  }

  window.CityforgeWeb = { setTool, setLayer, setSpeed, getState: () => ({ ...state }), syncFromApi };
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
