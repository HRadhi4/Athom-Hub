// Athom Hub page. A plain web component: no build step, no outside files.
// Rules it follows: text is never cut off, a short summary comes first and the
// details open on tap, and it follows Home Assistant's light or dark mode.

const KINDS = {
  tv: ["TV", "mdi:television"],
  ac: ["Air conditioner", "mdi:air-conditioner"],
  fan: ["Fan", "mdi:fan"],
  curtain: ["Curtain or blind", "mdi:curtains"],
  light: ["Light", "mdi:lightbulb-outline"],
  audio: ["Audio", "mdi:speaker"],
  other: ["Other", "mdi:remote"],
};
const KIND_WORD = { ir: "Infrared", rf: "Radio 433 MHz" };

const esc = (v) =>
  String(v ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

const CSS = `
:host{--bg:#0B0D17;--card:#151827;--card2:#1C2033;--line:rgba(139,108,255,.18);--tx:#EEF0FA;--tx2:#A3A8C3;
  --acc:#8B6CFF;--acc2:#4C8DFF;--ok:#3DD68C;--bad:#FF5C7A;--warn:#FFB84D;--glow:0 8px 28px rgba(139,108,255,.22);
  display:block;min-height:100vh;background:var(--bg);color:var(--tx);font-family:var(--paper-font-body1_-_font-family,Roboto,system-ui,sans-serif);
  -webkit-font-smoothing:antialiased}
:host([light]){--bg:#F3F4FA;--card:#FFFFFF;--card2:#ECEEF8;--line:rgba(91,70,200,.16);--tx:#171A2C;--tx2:#5B6080;--glow:0 6px 20px rgba(91,70,200,.12)}
*{box-sizing:border-box}
.wrap{max-width:1040px;margin:0 auto;padding:16px 16px 96px}
.top{display:flex;align-items:center;gap:12px;margin:4px 0 14px}
.top h1{font-size:24px;font-weight:600;margin:0;line-height:1.25}
.top .sum{color:var(--tx2);font-size:14px;line-height:1.4;margin-top:2px}
.iconbtn{flex:none;width:44px;height:44px;border-radius:14px;border:1px solid var(--line);background:var(--card);color:var(--tx);
  display:flex;align-items:center;justify-content:center;cursor:pointer}
.tabs{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:6px;padding:5px;border-radius:18px;background:var(--card);border:1px solid var(--line);margin-bottom:16px}
.tab{min-height:44px;border:0;border-radius:14px;background:transparent;color:var(--tx2);font:inherit;font-size:14px;font-weight:500;cursor:pointer;
  padding:8px 6px;line-height:1.25;white-space:normal;overflow-wrap:anywhere}
.tab.on{background:linear-gradient(135deg,var(--acc),var(--acc2));color:#fff;box-shadow:var(--glow)}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(160px,1fr));gap:12px}
.card{background:var(--card);border:1px solid var(--line);border-radius:22px;padding:16px;min-width:0}
.tile{min-height:132px;display:flex;flex-direction:column;justify-content:space-between;gap:10px;cursor:pointer;text-align:left;
  font:inherit;color:inherit;border:1px solid var(--line);border-radius:22px;padding:16px;background:linear-gradient(160deg,var(--card2),var(--card))}
.tile:hover{box-shadow:var(--glow)}
.tile .ic{width:44px;height:44px;border-radius:14px;display:flex;align-items:center;justify-content:center;
  background:linear-gradient(135deg,rgba(139,108,255,.28),rgba(76,141,255,.22));color:var(--acc)}
.tile .nm{font-size:16px;font-weight:600;line-height:1.3;overflow-wrap:anywhere}
.tile .sb{font-size:13px;color:var(--tx2);line-height:1.35;overflow-wrap:anywhere}
.tile.add{border-style:dashed;background:transparent;align-items:flex-start}
.btns{display:grid;grid-template-columns:repeat(auto-fill,minmax(130px,1fr));gap:10px}
.rb{min-height:84px;border-radius:20px;border:1px solid var(--line);background:linear-gradient(160deg,var(--card2),var(--card));color:var(--tx);
  font:inherit;font-size:15px;font-weight:500;line-height:1.3;padding:12px;cursor:pointer;display:flex;flex-direction:column;align-items:center;
  justify-content:center;gap:6px;text-align:center;overflow-wrap:anywhere}
.rb:active{transform:scale(.97)}
.rb{position:relative}
.rb ha-icon{--mdc-icon-size:34px;color:var(--bc,var(--acc))}
.rb .lb{font-size:14px;line-height:1.3}
.rb.ok{box-shadow:0 0 0 3px var(--ok),0 0 26px rgba(61,214,140,.45)}
.rb.fail{box-shadow:0 0 0 3px var(--bad);animation:shake .35s}
.rb .badge{position:absolute;top:8px;right:8px;width:24px;height:24px;border-radius:50%;display:flex;align-items:center;justify-content:center;color:#fff}
.rb .badge ha-icon{--mdc-icon-size:16px;color:#fff}
.rb.ok .badge{background:var(--ok)}.rb.fail .badge{background:var(--bad)}
@keyframes shake{0%,100%{transform:translateX(0)}25%{transform:translateX(-6px)}75%{transform:translateX(6px)}}
.pick{display:grid;grid-template-columns:repeat(auto-fill,minmax(52px,1fr));gap:8px}
.pick button{min-height:52px;border-radius:14px;border:1px solid var(--line);background:var(--card2);color:var(--tx);cursor:pointer;font:inherit;font-size:12px;line-height:1.2;padding:4px}
.pick button.on{outline:2px solid var(--acc)}
.sw{width:100%;min-height:44px;border-radius:14px;cursor:pointer;border:1px solid var(--line);font:inherit;font-size:13px;color:#fff}
.row{display:flex;align-items:center;gap:10px;flex-wrap:wrap}
.row.between{justify-content:space-between}
.pill{min-height:44px;border-radius:14px;border:1px solid var(--line);background:var(--card2);color:var(--tx);font:inherit;font-size:14px;
  font-weight:500;padding:10px 16px;cursor:pointer;display:inline-flex;align-items:center;gap:8px;line-height:1.25;text-align:left}
.pill.main{background:linear-gradient(135deg,var(--acc),var(--acc2));color:#fff;border:0;box-shadow:var(--glow)}
.pill.danger{color:var(--bad)}
.pill[disabled]{opacity:.5;cursor:default}
h2{font-size:18px;margin:0;line-height:1.3;font-weight:600;overflow-wrap:anywhere}
h3{font-size:15px;margin:0 0 6px;font-weight:600;line-height:1.3}
p,.note{color:var(--tx2);font-size:14px;line-height:1.5;margin:6px 0}
.dot{display:inline-block;width:9px;height:9px;border-radius:50%;background:var(--tx2);margin-right:6px;vertical-align:middle;flex:none}
.dot.ok{background:var(--ok)}.dot.bad{background:var(--bad)}
.list{display:flex;flex-direction:column;gap:10px}
.item{display:flex;gap:12px;align-items:flex-start;cursor:pointer}
.item .grow{flex:1;min-width:0}
.item .t{font-size:16px;font-weight:600;line-height:1.3;overflow-wrap:anywhere}
.item .s{font-size:13px;color:var(--tx2);line-height:1.4;margin-top:2px;overflow-wrap:anywhere}
.chev{color:var(--tx2);flex:none;transition:none}
.details{margin-top:12px;padding-top:12px;border-top:1px solid var(--line)}
.kv{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:6px 12px;font-size:14px;line-height:1.4}
.kv div:nth-child(odd){color:var(--tx2)}
.kv div{overflow-wrap:anywhere}
.chips{display:flex;flex-wrap:wrap;gap:6px;margin-top:8px}
.chip{font-size:12px;line-height:1.3;padding:5px 10px;border-radius:999px;background:var(--card2);color:var(--tx2);border:1px solid var(--line)}
label{display:block;font-size:13px;color:var(--tx2);margin:12px 0 6px}
input,select{width:100%;min-height:46px;border-radius:14px;border:1px solid var(--line);background:var(--card2);color:var(--tx);font:inherit;font-size:15px;padding:10px 12px}
.choice{display:grid;grid-template-columns:repeat(auto-fill,minmax(120px,1fr));gap:8px}
.choice button{min-height:56px}
.choice .on{outline:2px solid var(--acc)}
.shade{position:fixed;inset:0;background:rgba(5,6,12,.6);display:flex;align-items:flex-end;justify-content:center;z-index:10;padding:0}
.sheet{width:100%;max-width:560px;max-height:92vh;overflow:auto;background:var(--card);border:1px solid var(--line);border-radius:26px 26px 0 0;padding:20px 18px 26px}
@media(min-width:700px){.shade{align-items:center}.sheet{border-radius:26px}}
.big{font-size:44px;font-weight:600;text-align:center;margin:10px 0;line-height:1.2}
.center{text-align:center}
.pulse{width:96px;height:96px;margin:10px auto;border-radius:50%;display:flex;align-items:center;justify-content:center;color:#fff;
  background:radial-gradient(circle,var(--acc),var(--acc2));box-shadow:0 0 0 0 rgba(139,108,255,.5);animation:p 1.6s infinite}
@keyframes p{0%{box-shadow:0 0 0 0 rgba(139,108,255,.45)}70%{box-shadow:0 0 0 22px rgba(139,108,255,0)}100%{box-shadow:0 0 0 0 rgba(139,108,255,0)}}
.toast{position:fixed;left:50%;bottom:24px;transform:translateX(-50%);background:var(--card2);color:var(--tx);border:1px solid var(--line);
  border-radius:16px;padding:12px 18px;font-size:14px;line-height:1.4;max-width:min(92vw,520px);box-shadow:var(--glow);z-index:20}
.toast.bad{border-color:var(--bad)}
.ok{color:var(--ok)}.bad{color:var(--bad)}
.empty{text-align:center;padding:28px 12px}
.sec{margin:22px 0 10px;font-size:13px;letter-spacing:.04em;text-transform:uppercase;color:var(--tx2)}
.hidden{display:none}
.logrow{display:flex;gap:12px;align-items:flex-start;padding:12px 0;border-top:1px solid var(--line)}
.logrow:first-child{border-top:0}
.logrow .ic2{flex:none;width:36px;height:36px;border-radius:12px;display:flex;align-items:center;justify-content:center;background:var(--card2)}
.logrow .grow{flex:1;min-width:0}
.logrow .t{font-size:15px;font-weight:500;line-height:1.35;overflow-wrap:anywhere}
.logrow .s{font-size:12px;color:var(--tx2);line-height:1.4;margin-top:2px;overflow-wrap:anywhere}
.logrow .tm{flex:none;font-size:12px;color:var(--tx2);font-variant-numeric:tabular-nums}
.sheet.wide{max-width:760px}
.ctl{display:flex;align-items:center;gap:12px;padding:12px 0;border-top:1px solid var(--line)}
.ctl:first-child{border-top:0}
.ctl .grow{flex:1;min-width:0}
.ctl .t{font-size:15px;font-weight:500;line-height:1.35;overflow-wrap:anywhere}
.ctl .s{font-size:12px;color:var(--tx2);line-height:1.4;margin-top:2px;overflow-wrap:anywhere}
.ctl select,.ctl input{width:auto;min-width:120px;max-width:200px;flex:none}
.ctl.col{flex-direction:column;align-items:stretch;gap:8px}.ctl.col select{max-width:none;width:100%}
.tog{flex:none;width:56px;height:32px;border-radius:999px;border:0;background:var(--card2);position:relative;cursor:pointer;box-shadow:inset 0 0 0 1px var(--line)}
.tog::after{content:"";position:absolute;top:4px;left:4px;width:24px;height:24px;border-radius:50%;background:var(--tx2);transition:left .15s}
.tog.on{background:linear-gradient(135deg,var(--acc),var(--acc2))}.tog.on::after{left:28px;background:#fff}
.stats{display:grid;grid-template-columns:repeat(auto-fill,minmax(120px,1fr));gap:8px;margin:12px 0}
.stat{background:var(--card2);border-radius:16px;padding:10px 12px;min-width:0}
.stat .v{font-size:18px;font-weight:600;line-height:1.3;overflow-wrap:anywhere}.stat .k{font-size:12px;color:var(--tx2);line-height:1.3}
.map{width:100%;height:auto;display:block;touch-action:none;background:var(--card2);border-radius:18px;border:1px solid var(--line)}
.zchips{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:8px;margin:10px 0}
.zchip{min-height:48px;border-radius:14px;border:1px solid var(--line);background:var(--card2);color:var(--tx);font:inherit;font-size:14px;cursor:pointer;line-height:1.25;padding:6px}
.zchip.on{outline:2px solid var(--zc,var(--acc))}
.zchip .sw2{display:inline-block;width:10px;height:10px;border-radius:3px;background:var(--zc);margin-right:6px}
.nums{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px}
.nums label{margin:4px 0}
details summary{cursor:pointer;color:var(--tx2);font-size:14px;padding:10px 0;list-style-position:inside}
`;

class AthomHubPanel extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this.s = { tab: "remotes", data: null, err: "", open: {}, remote: null, edit: false, sheet: null, bl: null, test: {} };
  }

  set hass(hass) {
    const first = !this._hass;
    this._hass = hass;
    const light = !(hass.themes && hass.themes.darkMode);
    this.toggleAttribute("light", light);
    if (!first && this.s.sheet?.type === "device") this.live();
    if (first) {
      this.render();
      this.load();
    }
  }
  get hass() { return this._hass; }
  set narrow(v) { this._narrow = v; if (this._hass) this.render(); }
  set panel(v) { this._panel = v; }

  ws(type, extra = {}) { return this._hass.connection.sendMessagePromise({ type: `athom_hub/${type}`, ...extra }); }

  async load() {
    try {
      this.s.data = await this.ws("overview");
      this.s.err = "";
    } catch (e) {
      this.s.err = e.message || "Athom Hub did not answer.";
    }
    if (this.s.remote && !this.remote()) this.s.remote = null;
    this.render();
  }

  remote() { return (this.s.data?.remotes || []).find((r) => r.id === this.s.remote); }
  ports(role, kind) { return (this.s.data?.ports || []).filter((p) => p.role === role && (!kind || p.kind === kind)); }
  portName(id) { const p = (this.s.data?.ports || []).find((x) => x.entity_id === id); return p ? `${p.device_name}${p.area ? " · " + p.area : ""}` : "Not chosen"; }

  toast(text, bad = false) {
    clearTimeout(this._tt);
    this.s.toast = { text, bad };
    this.render();
    this._tt = setTimeout(() => { this.s.toast = null; this.render(); }, bad ? 6000 : 2200);
  }

  async run(fn, okText) {
    try {
      const r = await fn();
      if (okText) this.toast(typeof okText === "function" ? okText(r) : okText);
      return r;
    } catch (e) {
      this.toast(e.message || "Something went wrong.", true);
      return undefined;
    }
  }

  // ---------------------------------------------------------------- drawing

  render() {
    if (!this._hass) return;
    const d = this.s.data;
    const remotes = d?.remotes || [];
    const nButtons = remotes.reduce((n, r) => n + r.buttons.length, 0);
    const athom = (d?.devices || []).filter((x) => x.athom);
    const athomOn = athom.filter((x) => x.online).length;
    const sum = d
      ? `${remotes.length} ${remotes.length === 1 ? "remote" : "remotes"} · ${nButtons} ${nButtons === 1 ? "button" : "buttons"} · ${athom.length ? `${athomOn} of ${athom.length} Athom online` : "no Athom found"}`
      : this.s.err ? "" : "Loading…";
    let body = "";
    if (this.s.err) body = `<div class="card empty"><h2>Athom Hub is not ready</h2><p>${esc(this.s.err)}</p><button class="pill main" data-a="reload">Try again</button></div>`;
    else if (!d) body = `<div class="card empty"><p>Loading…</p></div>`;
    else if (this.s.tab === "remotes") body = this.s.remote && this.remote() ? this.vRemote(this.remote()) : this.vRemotes(remotes);
    else if (this.s.tab === "devices") body = this.vDevices(d);
    else if (this.s.tab === "log") body = this.vLog();
    else body = this.vBroadlink();

    const oldSheet = this.shadowRoot.querySelector(".sheet");
    const keepScroll = oldSheet ? oldSheet.scrollTop : 0;
    this.shadowRoot.innerHTML = `<style>${CSS}</style>
      <div class="wrap">
        <div class="top">
          ${this._narrow ? `<button class="iconbtn" data-a="menu" aria-label="Menu"><ha-icon icon="mdi:menu"></ha-icon></button>` : ""}
          <div style="min-width:0"><h1>Athom Hub</h1><div class="sum">${esc(sum)}</div></div>
        </div>
        <div class="tabs">
          ${[["remotes", "Remotes"], ["devices", "Devices"], ["broadlink", "From Broadlink"], ["log", "Activity"]]
            .map(([k, t]) => `<button class="tab ${this.s.tab === k ? "on" : ""}" data-a="tab" data-k="${k}">${t}</button>`).join("")}
        </div>
        ${body}
      </div>
      ${this.s.sheet ? `<div class="shade" data-a="shade"><div class="sheet ${this.s.sheet.type === "device" ? "wide" : ""}">${this.vSheet()}</div></div>` : ""}
      ${this.s.toast ? `<div class="toast ${this.s.toast.bad ? "bad" : ""}">${esc(this.s.toast.text)}</div>` : ""}`;
    const newSheet = this.shadowRoot.querySelector(".sheet");
    if (newSheet && keepScroll) newSheet.scrollTop = keepScroll;
    this.wire();
  }

  vRemotes(remotes) {
    const tiles = remotes.map((r) => {
      const [kname, icon] = KINDS[r.kind] || KINDS.other;
      return `<button class="tile" data-a="open" data-id="${r.id}">
        <span class="ic"><ha-icon icon="${icon}"></ha-icon></span>
        <span><div class="nm">${esc(r.name)}</div><div class="sb">${r.buttons.length} ${r.buttons.length === 1 ? "button" : "buttons"} · ${esc(kname)}</div></span>
      </button>`;
    }).join("");
    const noSender = !this.ports("send").length;
    return `
      ${noSender ? `<div class="card" style="margin-bottom:12px"><h3>No remote sender found</h3><p>Add your Athom RF/IR Remote to Home Assistant first (it appears by itself as an ESPHome device), then come back.</p></div>` : ""}
      <div class="grid">
        ${tiles}
        <button class="tile add" data-a="newRemote">
          <span class="ic"><ha-icon icon="mdi:plus"></ha-icon></span>
          <span><div class="nm">New remote</div><div class="sb">Learn its buttons one by one</div></span>
        </button>
      </div>
      ${remotes.length ? "" : `<p class="note" style="margin-top:14px">Tip: if a Broadlink already knows your remotes, open “From Broadlink” to copy them in one tap.</p>`}
      <div class="sec">Backup</div>
      <div class="row">
        <button class="pill" data-a="backup"><ha-icon icon="mdi:download"></ha-icon>Save a backup file</button>
        <button class="pill" data-a="restore"><ha-icon icon="mdi:upload"></ha-icon>Bring back a backup</button>
        <input type="file" accept="application/json,.json" class="hidden" id="restoreFile">
      </div>`;
  }

  vRemote(r) {
    const edit = this.s.edit;
    const [kname, icon] = KINDS[r.kind] || KINDS.other;
    const buttons = r.buttons.map((b, i) => edit
      ? `<div class="card" style="padding:12px">
          <div class="row" style="flex-wrap:nowrap"><ha-icon icon="${esc(b.icon)}" style="color:${esc(b.colour || "var(--acc)")};flex:none"></ha-icon><div class="t" style="font-weight:600;overflow-wrap:anywhere;min-width:0">${esc(b.name)}</div></div>
          <div class="note" style="margin:2px 0 8px">${b.role ? esc((this.s.data.role_names || {})[b.role]) + " · " : ""}${KIND_WORD[b.kind] || ""} · ${b.pulses} pulses${b.source === "broadlink" ? " · from Broadlink" : ""}</div>
          <div class="row">
            <button class="pill" data-a="renameBtn" data-id="${b.id}">Name and picture</button>
            <button class="pill" data-a="relearn" data-id="${b.id}">Learn again</button>
            ${i ? `<button class="iconbtn" data-a="up" data-id="${b.id}" aria-label="Move up"><ha-icon icon="mdi:arrow-up"></ha-icon></button>` : ""}
            <button class="iconbtn" data-a="delBtn" data-id="${b.id}" aria-label="Delete" style="color:var(--bad)"><ha-icon icon="mdi:delete-outline"></ha-icon></button>
          </div></div>`
      : `<button class="rb" data-a="press" data-id="${b.id}" ${b.colour ? `style="--bc:${esc(b.colour)}"` : ""}><span class="badge"></span><ha-icon icon="${esc(b.icon)}"></ha-icon><span class="lb">${esc(b.name)}</span></button>`).join("");
    const kinds = [...new Set(r.buttons.map((b) => b.kind))];
    const from = (kinds.length ? kinds : ["ir"]).map((k) => `${KIND_WORD[k]}: ${esc(this.portName(r[`emitter_${k}`]))}`).join(" · ");
    return `
      <div class="row between" style="margin-bottom:12px">
        <button class="pill" data-a="back"><ha-icon icon="mdi:arrow-left"></ha-icon>All remotes</button>
        <div class="row">
          <button class="pill ${edit ? "main" : ""}" data-a="edit">${edit ? "Done" : "Edit"}</button>
          <button class="iconbtn" data-a="remoteSettings" aria-label="Remote settings"><ha-icon icon="mdi:cog-outline"></ha-icon></button>
        </div>
      </div>
      <div class="card" style="margin-bottom:12px">
        <div class="item" style="cursor:default">
          <span class="tile" style="min-height:0;padding:0;border:0;background:none;cursor:default"><span class="ic"><ha-icon icon="${icon}"></ha-icon></span></span>
          <div class="grow"><h2>${esc(r.name)}</h2><div class="s">${esc(kname)} · sends from ${from}</div></div>
        </div>
        ${r.table ? `<p class="note" style="margin-bottom:0">Full air conditioner code set: ${esc(r.table.maker)} ${esc((r.table.models || []).join(", "))} · ${r.table.codes} codes (${esc(r.table.source || "")}). Every change sends the whole setting, and presses of the real remote near an Athom are followed.</p>` : ""}
        ${this.vMainEntity(r)}
      </div>
      ${r.buttons.length
        ? `<div class="${edit ? "list" : "btns"}">${buttons}</div>`
        : `<div class="card empty"><h2>No buttons yet</h2><p>Tap “Add a button”, then press the button on your real remote, pointed at the Athom.</p></div>`}
      <div class="row" style="margin-top:14px"><button class="pill main" data-a="learn"><ha-icon icon="mdi:plus"></ha-icon>Add a button</button></div>
      <p class="note">Each button is also a normal Home Assistant button, so you can use it on dashboards and in automations.</p>`;
  }

  vMainEntity(r) {
    const what = { climate: "a thermostat", cover: "a curtain control", media_player: "a TV and media control", fan: "a fan", light: "a light" };
    const need = { ac: "Power", curtain: "Open and Close", tv: "Power", audio: "Power", fan: "Power", light: "Power" };
    if (r.entity) {
      return `<div class="row" style="margin-top:12px"><button class="pill" data-a="moreInfo" data-id="${esc(r.entity)}"><ha-icon icon="mdi:home-assistant"></ha-icon><span>Works in Home Assistant as ${what[r.platform]}<br><small style="color:var(--tx2)">${esc(r.entity)}</small></span></button></div>`;
    }
    if (need[r.kind]) return `<p class="note" style="margin-bottom:0">To use it as ${what[{ ac: "climate", curtain: "cover", tv: "media_player", audio: "media_player", fan: "fan", light: "light" }[r.kind]]} in Home Assistant, it needs a ${need[r.kind]} button. Tap Edit, then “Name and picture” on that button.</p>`;
    return "";
  }

  vDevices(d) {
    const devs = d.devices || [];
    const cards = devs.map((x) => {
      const open = this.s.open[x.id];
      const sum = [x.area, x.online ? "Online" : "Offline", x.ports.length ? `${x.ports.length} remote ${x.ports.length === 1 ? "part" : "parts"}` : ""].filter(Boolean).join(" · ");
      return `<div class="card">
        <div class="item" data-a="toggle" data-id="${x.id}">
          <span class="dot ${x.online ? "ok" : "bad"}" style="margin-top:7px"></span>
          <div class="grow"><div class="t">${esc(x.name)}</div><div class="s">${esc(sum)}</div></div>
          <ha-icon class="chev" icon="${open ? "mdi:chevron-up" : "mdi:chevron-down"}"></ha-icon>
        </div>
        ${open ? `<div class="details">
          <div class="kv">
            ${x.maker ? `<div>Made by</div><div>${esc(x.maker)}</div>` : ""}
            ${x.model ? `<div>Model</div><div>${esc(x.model)}</div>` : ""}
            ${x.firmware ? `<div>Software</div><div>${esc(x.firmware)}</div>` : ""}
            ${x.wifi ? `<div>Wi-Fi signal</div><div>${esc(x.wifi)} %</div>` : ""}
            ${x.facts.map((f) => `<div>${esc(f.name)}</div><div>${esc(f.state)}</div>`).join("")}
          </div>
          ${x.more_facts ? `<p class="note">And ${x.more_facts} more on its device page in Settings.</p>` : ""}
          ${x.ports.length ? `<div class="chips">${x.ports.map((p) => `<span class="chip">${p.role === "send" ? "Sends" : "Hears"} ${KIND_WORD[p.kind]}</span>`).join("")}</div>` : ""}
          <div class="row" style="margin-top:12px"><button class="pill main" data-a="devOpen" data-id="${x.id}"><ha-icon icon="mdi:tune-variant"></ha-icon>Settings and controls</button></div>
        </div>` : ""}
      </div>`;
    }).join("");
    return `${this.vTest()}
      <div class="sec">Devices</div>
      <div class="list">${cards || `<div class="card empty"><p>No Athom devices were found in Home Assistant.</p></div>`}</div>`;
  }

  vTest() {
    const t = this.s.test;
    const kinds = ["ir", "rf"].filter((k) => this.ports("receive", k).length && (this.ports("send", k).length || this.s.data.broadlinks.length));
    if (!kinds.length) return "";
    const kind = kinds.includes(t.kind) ? t.kind : kinds[0];
    const senders = [...this.ports("send", kind).map((p) => [p.entity_id, p.device_name]), ...this.s.data.broadlinks.map((b) => [b.entity_id, b.name])];
    const sender = senders.some(([id]) => id === t.from) ? t.from : senders[0]?.[0];
    const receivers = this.ports("receive", kind);
    const res = t.result;
    return `<div class="card">
      <div class="item" data-a="toggle" data-id="__test">
        <ha-icon icon="mdi:shield-check-outline" style="color:var(--acc);margin-top:2px"></ha-icon>
        <div class="grow"><div class="t">Check that it works</div><div class="s">${res ? (res.heard ? "Last check: heard it ✓" : "Last check: not heard") : "A safe test with a made-up code. Your TV, AC and curtains will not react."}</div></div>
        <ha-icon class="chev" icon="${this.s.open.__test ? "mdi:chevron-up" : "mdi:chevron-down"}"></ha-icon>
      </div>
      ${this.s.open.__test ? `<div class="details">
        <label>What to test</label>
        <div class="choice">${kinds.map((k) => `<button class="pill ${k === kind ? "on" : ""}" data-a="testKind" data-k="${k}">${KIND_WORD[k]}</button>`).join("")}</div>
        <label for="tfrom">Send from</label>
        <select id="tfrom">${senders.map(([id, n]) => `<option value="${esc(id)}" ${id === sender ? "selected" : ""}>${esc(n)}</option>`).join("")}</select>
        <label for="tto">Listen with</label>
        <select id="tto">${receivers.map((p) => `<option value="${esc(p.entity_id)}">${esc(p.device_name)}</option>`).join("")}</select>
        <p class="note">Sending from a Broadlink also checks that codes copied from it come out right.</p>
        <div class="row"><button class="pill main" data-a="runTest" ${t.busy ? "disabled" : ""}>${t.busy ? "Testing…" : "Run the test"}</button></div>
        ${res ? `<p class="${res.heard ? "ok" : "bad"}" style="font-weight:500">${res.heard ? "It worked: the receiver heard the test code." : `The receiver did not hear the test code (it heard ${res.captures} other ${res.captures === 1 ? "signal" : "signals"}). Put the two devices closer together and try again.`}</p>` : ""}
      </div>` : ""}
    </div>`;
  }

  vBroadlink() {
    const bl = this.s.bl;
    if (!bl) { this.loadBroadlink(); return `<div class="card empty"><p>Looking for Broadlink remotes…</p></div>`; }
    const items = bl.map((r, i) => {
      const key = `bl${i}`;
      const open = this.s.open[key];
      const good = r.buttons.filter((b) => b.ok).length;
      const sum = `${esc(r.source_name)} · ${good} ${good === 1 ? "button" : "buttons"}${r.kinds.length ? " · " + r.kinds.map((k) => KIND_WORD[k]).join(" and ") : ""}`;
      return `<div class="card">
        <div class="item" data-a="toggle" data-id="${key}">
          <ha-icon icon="${(KINDS[guessKind(r.device)] || KINDS.other)[1]}" style="color:var(--acc);margin-top:2px"></ha-icon>
          <div class="grow"><div class="t">${esc(niceName(r.device))}</div><div class="s">${sum}</div></div>
          <ha-icon class="chev" icon="${open ? "mdi:chevron-up" : "mdi:chevron-down"}"></ha-icon>
        </div>
        ${open ? `<div class="details">
          <div class="chips">${r.buttons.map((b) => `<span class="chip" ${b.ok ? "" : 'style="color:var(--bad)"'}>${esc(b.name)}${b.ok ? "" : " (cannot be read)"}</span>`).join("")}</div>
          <div class="row" style="margin-top:12px"><button class="pill main" data-a="copy" data-i="${i}" ${good ? "" : "disabled"}><ha-icon icon="mdi:content-copy"></ha-icon>Copy to Athom Hub</button></div>
        </div>` : ""}
      </div>`;
    }).join("");
    return `${this.vAcSets()}
      <div class="sec">Remotes learned by a Broadlink</div>
      <p class="note" style="margin-top:0">Remotes a Broadlink learned through Home Assistant. Copy one, then press each button once to check it.</p>
      <div class="list">${items || `<div class="card empty"><h2>Nothing to copy</h2><p>No remotes learned by a Broadlink were found in Home Assistant.</p></div>`}</div>
      <div class="card" style="margin-top:14px"><h3>Good to know</h3>
        <p>Remotes learned only in the Broadlink phone app are not in Home Assistant, so they cannot be copied. Learn those buttons again here.</p>
        <p>Garage doors and remotes with “rolling codes” change their code every press. No device can copy them.</p>
        <p>The Broadlink keeps working. Nothing is removed from it.</p></div>`;
  }

  vSheet() {
    const sh = this.s.sheet;
    const close = `<button class="pill" data-a="close">Cancel</button>`;
    if (sh.type === "newRemote" || sh.type === "remoteSettings") {
      const r = sh.type === "remoteSettings" ? this.remote() : null;
      const kind = sh.kind || r?.kind || "tv";
      const sel = (k) => {
        const list = this.ports("send", k);
        const cur = r ? r[`emitter_${k}`] : this.s.data.defaults[k];
        if (!list.length) return `<p class="note">No ${KIND_WORD[k].toLowerCase()} sender found.</p>`;
        return `<select id="em_${k}">${list.map((p) => `<option value="${esc(p.entity_id)}" ${p.entity_id === cur ? "selected" : ""}>${esc(p.device_name)}${p.area ? " · " + esc(p.area) : ""}</option>`).join("")}</select>`;
      };
      return `<h2>${r ? "Remote settings" : "New remote"}</h2>
        <label for="rname">Name</label><input id="rname" value="${esc(sh.name ?? r?.name ?? "")}" placeholder="For example: Living room TV" maxlength="60">
        <label>What does it control?</label>
        <div class="choice">${Object.entries(KINDS).map(([k, [n, ic]]) => `<button class="pill ${k === kind ? "on" : ""}" data-a="pickKind" data-k="${k}"><ha-icon icon="${ic}"></ha-icon>${n}</button>`).join("")}</div>
        ${kind === "ac" ? `<label for="tsens">Room temperature from</label><select id="tsens"><option value="">No sensor</option>${Object.values(this._hass.states).filter((x) => x.attributes.device_class === "temperature" && x.entity_id.startsWith("sensor.")).sort((a, b) => (a.attributes.friendly_name || "").localeCompare(b.attributes.friendly_name || "")).map((x) => `<option value="${esc(x.entity_id)}" ${r?.temp_sensor === x.entity_id ? "selected" : ""}>${esc(x.attributes.friendly_name || x.entity_id)}</option>`).join("")}</select><p class="note">Shown on thermostat cards as the room temperature.</p>` : ""}
        <label>Infrared buttons send from</label>${sel("ir")}
        <label>Radio buttons send from</label>${sel("rf")}
        <div class="row between" style="margin-top:18px">
          ${r ? `<button class="pill danger" data-a="delRemote">Delete remote</button>` : "<span></span>"}
          <div class="row">${close}<button class="pill main" data-a="saveRemote">Save</button></div>
        </div>`;
    }
    if (sh.type === "rename") {
      const choices = this.s.data.icon_choices || [];
      const cols = this.s.data.colours || {};
      const rem = this.remote();
      const kr = (this.s.data.kind_roles || {})[rem?.kind || "other"] || [];
      const rn = this.s.data.role_names || {};
      const btn = rem?.buttons.find((x) => x.id === sh.id);
      const roleSel = kr.length ? `<label for="brole">What this button does</label>
        <select id="brole">
          <option value="" ${!sh.role ? "selected" : ""}>Let Athom Hub guess${btn?.role && !btn.role_set ? ` (now: ${esc(rn[btn.role])})` : ""}</option>
          ${kr.map((k) => `<option value="${k}" ${sh.role === k ? "selected" : ""}>${esc(rn[k])}</option>`).join("")}
          <option value="none" ${sh.role === "none" ? "selected" : ""}>Nothing special (a plain button)</option>
        </select>
        <p class="note">This is how the ${esc(KINDS[rem.kind][0].toLowerCase())} control in Home Assistant uses this button.</p>` : "";
      return `<h2>Name and picture</h2><label for="bname">Name</label><input id="bname" value="${esc(sh.name)}" maxlength="60">${roleSel}
        <label>Picture</label>
        <div class="pick">
          <button class="${sh.icon ? "" : "on"}" data-a="pickIcon" data-k="">Auto</button>
          ${choices.map((ic) => `<button class="${sh.icon === ic ? "on" : ""}" data-a="pickIcon" data-k="${ic}" aria-label="${ic.slice(4)}"><ha-icon icon="${ic}"></ha-icon></button>`).join("")}
        </div>
        <label>Colour</label>
        <div class="choice">
          <button class="sw ${!sh.colour ? "on" : ""}" style="background:var(--card2);color:var(--tx)" data-a="pickColour" data-k="">Auto</button>
          ${Object.entries(cols).map(([k, c]) => `<button class="sw ${sh.colour === k ? "on" : ""}" style="background:${c}" data-a="pickColour" data-k="${k}" aria-label="${k}"></button>`).join("")}
          <button class="sw ${sh.colour === "none" ? "on" : ""}" style="background:var(--acc)" data-a="pickColour" data-k="none" aria-label="plain"></button>
        </div>
        <div class="row" style="margin-top:18px;justify-content:flex-end">${close}<button class="pill main" data-a="saveName">Save</button></div>`;
    }
    if (sh.type === "confirm") {
      return `<h2>${esc(sh.title)}</h2><p>${esc(sh.text)}</p>
        <div class="row" style="margin-top:18px;justify-content:flex-end">${close}<button class="pill main danger" style="background:var(--bad)" data-a="confirmYes">${esc(sh.yes)}</button></div>`;
    }
    if (sh.type === "learn") return this.vLearn(sh);
    if (sh.type === "device") return this.vDevice(sh);
    if (sh.type === "acCopy") return this.vAcCopy(sh);
    if (sh.type === "acFind") return this.vAcFind(sh);
    return "";
  }

  vLearn(sh) {
    const kinds = ["ir", "rf"].filter((k) => this.ports("receive", k).length);
    if (!kinds.length) return `<h2>No receiver found</h2><p>Learning needs the Athom RF/IR Remote (or another device that can hear remotes) in Home Assistant.</p><div class="row" style="justify-content:flex-end"><button class="pill" data-a="close">Close</button></div>`;
    if (sh.step === "pick") {
      return `<h2>${sh.buttonId ? "Learn the button again" : "Add a button"}</h2>
        <p>Which kind of remote is it?</p>
        <div class="choice">
          ${kinds.includes("ir") ? `<button class="pill" data-a="learnKind" data-k="ir"><ha-icon icon="mdi:remote"></ha-icon><span>Infrared<br><small style="color:var(--tx2)">TV, AC, fan, audio — you point it</small></span></button>` : ""}
          ${kinds.includes("rf") ? `<button class="pill" data-a="learnKind" data-k="rf"><ha-icon icon="mdi:radio-tower"></ha-icon><span>Radio 433 MHz<br><small style="color:var(--tx2)">curtains, sockets — works through walls</small></span></button>` : ""}
        </div>
        <div class="row" style="margin-top:18px;justify-content:flex-end">${`<button class="pill" data-a="close">Cancel</button>`}</div>`;
    }
    if (sh.step === "listen") {
      return `<div class="center"><h2>Press the button now</h2>
        <div class="pulse"><ha-icon icon="${sh.kind === "rf" ? "mdi:radio-tower" : "mdi:remote"}"></ha-icon></div>
        <div class="big">${sh.left}</div>
        <p>${sh.kind === "rf" ? "Hold the remote close to the Athom and keep the button pressed for about two seconds." : "Point your remote at the Athom from about 30 cm and press the button once."}</p>
        ${sh.count ? `<p class="note">Hearing something… (${sh.count})</p>` : ""}
        <button class="pill" data-a="close">Stop</button></div>`;
    }
    if (sh.step === "timeout") {
      return `<h2>Nothing clear was heard</h2>
        <p>${sh.kind === "rf" ? "Hold the remote right next to the Athom and keep the button pressed longer. If it still fails, this remote may use rolling codes, which cannot be copied." : "Come closer, point straight at the Athom, and press once. Bright sunlight can get in the way."}</p>
        <div class="row" style="justify-content:flex-end;margin-top:14px"><button class="pill" data-a="close">Cancel</button><button class="pill main" data-a="learnKind" data-k="${sh.kind}">Try again</button></div>`;
    }
    if (sh.step === "got") {
      const r = this.remote();
      return `<h2>Got it ✓</h2>
        <p>${KIND_WORD[sh.kind]} · ${sh.pulses} pulses. Try it on the real device before saving.</p>
        <div class="row"><button class="pill" data-a="testLearned" ${r && r[`emitter_${sh.kind}`] ? "" : "disabled"}><ha-icon icon="mdi:play"></ha-icon>Try it</button>
          <button class="pill" data-a="learnKind" data-k="${sh.kind}">Learn again</button></div>
        ${r && !r[`emitter_${sh.kind}`] ? `<p class="note">Choose where ${KIND_WORD[sh.kind].toLowerCase()} buttons send from in the remote settings to try it.</p>` : ""}
        ${sh.buttonId ? "" : `<label for="lname">Name</label><input id="lname" value="${esc(sh.name || "")}" placeholder="For example: Power" maxlength="60">`}
        <div class="row" style="justify-content:flex-end;margin-top:18px"><button class="pill" data-a="close">Cancel</button><button class="pill main" data-a="saveLearned">Save button</button></div>`;
    }
    return "";
  }

  // ---------------------------------------------------------------- actions

  wire() {
    const root = this.shadowRoot;
    root.querySelectorAll("[data-a]").forEach((el) => {
      el.addEventListener("click", (ev) => {
        if (el.dataset.a === "shade" && ev.target !== el) return;
        ev.stopPropagation();
        this.act(el.dataset.a, el.dataset, ev);
      });
    });
    const file = root.getElementById("restoreFile");
    if (file) file.addEventListener("change", () => this.restore(file.files[0]));
    root.querySelectorAll("[data-ch]").forEach((el) => el.addEventListener("change", () => this.actDevice("change", el.dataset, el)));
    if (this.s.sheet?.type === "device") this.wireMap();
    const tf = root.getElementById("tfrom");
    if (tf) tf.addEventListener("change", () => { this.s.test.from = tf.value; });
  }

  val(id) { const el = this.shadowRoot.getElementById(id); return el ? el.value : undefined; }

  async act(a, ds) {
    const s = this.s;
    switch (a) {
      case "menu": this.dispatchEvent(new Event("hass-toggle-menu", { bubbles: true, composed: true })); return;
      case "reload": s.err = ""; this.render(); this.load(); return;
      case "tab": s.tab = ds.k; s.remote = null; s.edit = false; this.render(); if (ds.k === "log") this.startLog(); return;
      case "logFilter": s.logFilter = ds.k; this.render(); return;
      case "logClear": await this.run(() => this.ws("log_clear")); s.log = []; this.render(); return;
      case "open": s.remote = ds.id; s.edit = false; this.render(); return;
      case "back": s.remote = null; s.edit = false; this.render(); return;
      case "edit": s.edit = !s.edit; this.render(); return;
      case "toggle": s.open[ds.id] = !s.open[ds.id]; this.render(); return;
      case "shade": case "close": this.stopLearn(); this.stopFind(); s.sheet = null; this.render(); return;
      case "newRemote": s.sheet = { type: "newRemote" }; this.render(); return;
      case "remoteSettings": s.sheet = { type: "remoteSettings" }; this.render(); return;
      case "pickKind": s.sheet.name = this.val("rname"); s.sheet.kind = ds.k; this.render(); return;
      case "moreInfo": this.dispatchEvent(new CustomEvent("hass-more-info", { detail: { entityId: ds.id }, bubbles: true, composed: true })); return;
      case "saveRemote": {
        const sh = s.sheet;
        const msg = { name: (this.val("rname") || "").trim() || KINDS[sh.kind || this.remote()?.kind || "tv"][0], kind: sh.kind || this.remote()?.kind || "tv" };
        for (const k of ["ir", "rf"]) { const v = this.val(`em_${k}`); if (v !== undefined) msg[`emitter_${k}`] = v; }
        if (this.val("tsens") !== undefined) msg.temp_sensor = this.val("tsens") || null;
        if (sh.type === "remoteSettings") msg.remote_id = s.remote;
        const r = await this.run(() => this.ws("remote_save", msg), "Saved");
        if (r) { s.sheet = null; s.remote = r.remote_id; await this.load(); }
        return;
      }
      case "delRemote":
        s.sheet = { type: "confirm", title: "Delete this remote?", text: "Its buttons are removed from Home Assistant too. The real remote is not affected.", yes: "Delete", then: async () => {
          await this.run(() => this.ws("remote_delete", { remote_id: s.remote }), "Remote deleted"); s.remote = null; await this.load();
        } };
        this.render(); return;
      case "confirmYes": { const f = s.sheet.then; s.sheet = null; this.render(); await f(); return; }
      case "press": {
        const el = this.shadowRoot.querySelector(`[data-a="press"][data-id="${ds.id}"]`);
        if (!el) return;
        el.classList.remove("ok", "fail");
        let good = true;
        try { await this.ws("press", { remote_id: s.remote, button_id: ds.id }); } catch (e) { good = false; this.toast(e.message || "It did not send.", true); }
        el.classList.add(good ? "ok" : "fail");
        el.querySelector(".badge").innerHTML = `<ha-icon icon="${good ? "mdi:check" : "mdi:close"}"></ha-icon>`;
        try { navigator.vibrate && navigator.vibrate(good ? 35 : [70, 50, 70]); } catch { /* not on this device */ }
        clearTimeout(el._t);
        el._t = setTimeout(() => { el.classList.remove("ok", "fail"); el.querySelector(".badge").innerHTML = ""; }, good ? 900 : 1600);
        return;
      }
      case "renameBtn": { const b = this.remote().buttons.find((x) => x.id === ds.id); s.sheet = { type: "rename", id: ds.id, name: b.name, icon: b.icon_set || "", colour: b.colour_set || "", role: b.role_set || "" }; this.render(); return; }
      case "pickIcon": s.sheet.name = this.val("bname"); s.sheet.role = this.val("brole") ?? s.sheet.role; s.sheet.icon = ds.k; this.render(); return;
      case "pickColour": s.sheet.name = this.val("bname"); s.sheet.role = this.val("brole") ?? s.sheet.role; s.sheet.colour = ds.k; this.render(); return;
      case "saveName": {
        const name = (this.val("bname") || "").trim(); if (!name) return;
        const r = await this.run(() => this.ws("button_save", { remote_id: s.remote, button_id: s.sheet.id, name, icon: s.sheet.icon || null, colour: s.sheet.colour || null, ...(this.val("brole") !== undefined ? { role: this.val("brole") || null } : {}) }), "Saved");
        if (r) { s.sheet = null; await this.load(); }
        return;
      }
      case "delBtn": {
        const b = this.remote().buttons.find((x) => x.id === ds.id);
        s.sheet = { type: "confirm", title: `Delete “${b.name}”?`, text: "You can learn it again any time.", yes: "Delete", then: async () => {
          await this.run(() => this.ws("button_delete", { remote_id: s.remote, button_id: ds.id }), "Button deleted"); await this.load();
        } };
        this.render(); return;
      }
      case "up": {
        const ids = this.remote().buttons.map((b) => b.id); const i = ids.indexOf(ds.id);
        [ids[i - 1], ids[i]] = [ids[i], ids[i - 1]];
        await this.run(() => this.ws("button_order", { remote_id: s.remote, order: ids })); await this.load(); return;
      }
      case "learn": s.sheet = { type: "learn", step: "pick" }; this.render(); return;
      case "relearn": s.sheet = { type: "learn", step: "pick", buttonId: ds.id }; this.render(); return;
      case "learnKind": this.startLearn(ds.k); return;
      case "testLearned": {
        const r = this.remote();
        await this.run(() => this.ws("test", { token: s.sheet.token, emitter: r[`emitter_${s.sheet.kind}`] }), "Sent. Did the device react?");
        return;
      }
      case "saveLearned": {
        const sh = s.sheet;
        const msg = { remote_id: s.remote, token: sh.token };
        if (sh.buttonId) msg.button_id = sh.buttonId; else msg.name = (this.val("lname") || "").trim() || "Button";
        const r = await this.run(() => this.ws("button_save", msg), (x) => `Saved “${x.name}”`);
        if (r) { s.sheet = null; await this.load(); }
        return;
      }
      case "testKind": s.test.kind = ds.k; s.test.result = null; this.render(); return;
      case "runTest": {
        const kind = s.test.kind && this.ports("receive", s.test.kind).length ? s.test.kind : ["ir", "rf"].find((k) => this.ports("receive", k).length);
        const emitter = this.val("tfrom"); const receiver = this.val("tto");
        s.test.busy = true; s.test.result = null; this.render();
        s.test.result = await this.run(() => this.ws("self_test", { emitter, receiver, kind })) || null;
        s.test.busy = false; this.render(); return;
      }
      case "copy": {
        const r = s.bl[+ds.i];
        const res = await this.run(() => this.ws("broadlink_copy", { source: r.source, device: r.device, name: niceName(r.device), kind: guessKind(r.device) }),
          (x) => `Copied ${x.copied} ${x.copied === 1 ? "button" : "buttons"}${x.skipped.length ? ` (${x.skipped.length} could not be read)` : ""}`);
        if (res) { await this.load(); s.tab = "remotes"; s.remote = res.remote_id; this.render(); }
        return;
      }
      case "backup": {
        const data = await this.run(() => this.ws("backup")); if (!data) return;
        const url = URL.createObjectURL(new Blob([JSON.stringify(data, null, 1)], { type: "application/json" }));
        const link = document.createElement("a"); link.href = url; link.download = `athom-hub-backup-${new Date().toISOString().slice(0, 10)}.json`;
        document.body.appendChild(link); link.click(); link.remove(); setTimeout(() => URL.revokeObjectURL(url), 2000);
        return;
      }
      case "restore": this.shadowRoot.getElementById("restoreFile").click(); return;
      default:
        if (this.actDevice) await this.actDevice(a, ds);
    }
  }

  async restore(file) {
    if (!file) return;
    let data;
    try { data = JSON.parse(await file.text()); } catch { this.toast("That file is not an Athom Hub backup.", true); return; }
    if (!Array.isArray(data?.remotes)) { this.toast("That file is not an Athom Hub backup.", true); return; }
    await this.run(() => this.ws("restore", { remotes: data.remotes }), (r) => `Brought back ${r.remotes} ${r.remotes === 1 ? "remote" : "remotes"}`);
    await this.load();
  }

  async loadBroadlink() {
    if (this._blLoading) return;
    this._blLoading = true;
    const r = await this.run(() => this.ws("broadlink"));
    this.s.bl = r ? r.remotes : [];
    this._blLoading = false;
    this.render();
  }

  async startLearn(kind) {
    this.stopLearn();
    const s = this.s;
    const receiver = this.ports("receive", kind)[0]?.entity_id;
    const keep = { buttonId: s.sheet?.buttonId, name: this.val("lname") };
    s.sheet = { type: "learn", step: "listen", kind, left: 20, count: 0, ...keep };
    this.render();
    this._timer = setInterval(() => {
      if (s.sheet?.step !== "listen") return;
      s.sheet.left = Math.max(0, s.sheet.left - 1);
      const big = this.shadowRoot.querySelector(".big"); if (big) big.textContent = s.sheet.left;
    }, 1000);
    try {
      this._unsub = await this._hass.connection.subscribeMessage((ev) => {
        if (!s.sheet || s.sheet.type !== "learn") return;
        if (ev.state === "listening") { s.sheet.left = ev.seconds; }
        else if (ev.state === "heard") { s.sheet.count = ev.count; this.render(); }
        else if (ev.state === "done") { this.stopLearn(); s.sheet = { type: "learn", step: "got", kind, token: ev.token, pulses: ev.pulses, ...keep }; this.render(); }
        else if (ev.state === "timeout") { this.stopLearn(); s.sheet = { type: "learn", step: "timeout", kind, ...keep }; this.render(); }
      }, { type: "athom_hub/learn", receiver, kind });
    } catch (e) {
      this.stopLearn(); s.sheet = null; this.toast(e.message || "Could not start listening.", true);
    }
  }

  stopLearn() {
    clearInterval(this._timer); this._timer = null;
    if (this._unsub) { try { this._unsub(); } catch { /* already closed */ } this._unsub = null; }
  }

  disconnectedCallback() { this.stopLearn(); if (this._logUnsub) { try { this._logUnsub(); } catch { /* closed */ } this._logUnsub = null; } }

  async startLog() {
    if (this._logUnsub) return;
    const r = await this.run(() => this.ws("log"));
    this.s.log = r ? r.log : [];
    this.render();
    try {
      this._logUnsub = await this._hass.connection.subscribeMessage((entry) => {
        this.s.log = [...(this.s.log || []), entry].slice(-200);
        if (this.s.tab === "log" && !this.s.sheet) this.render();
      }, { type: "athom_hub/log_subscribe" });
    } catch { /* the list still shows what happened before */ }
  }

  vLog() {
    if (!this.s.log) { this.startLog(); return `<div class="card empty"><p>Loading…</p></div>`; }
    const f = this.s.logFilter || "all";
    const rows = [...this.s.log].reverse().filter((e) => f === "all" || (f === "sent" ? e.dir === "sent" : f === "heard" ? e.dir === "heard" : !e.ok));
    const fmt = (t) => new Date(t * 1000).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
    const item = (e) => {
      const sent = e.dir === "sent";
      const col = !e.ok ? "var(--bad)" : sent ? "var(--ok)" : e.known ? "var(--acc)" : "var(--tx2)";
      const icon = !e.ok ? "mdi:alert-circle-outline" : sent ? "mdi:arrow-up-bold-circle-outline" : "mdi:arrow-down-bold-circle-outline";
      const line = sent ? `${e.ok ? "Sent" : "Could not send"} from ${esc(e.via)}` : `Heard by ${esc(e.via)}${e.known ? "" : ` · ${e.pulses} pulses`}`;
      return `<div class="logrow"><span class="ic2" style="color:${col}"><ha-icon icon="${icon}"></ha-icon></span>
        <div class="grow"><div class="t">${esc(e.what)}</div><div class="s">${line} · ${esc(KIND_WORD[e.kind] || "")}</div>${e.why ? `<div class="s bad">${esc(e.why)}</div>` : ""}</div>
        <span class="tm">${fmt(e.time)}</span></div>`;
    };
    return `<div class="choice" style="grid-template-columns:repeat(4,minmax(0,1fr));margin-bottom:12px">
        ${[["all", "All"], ["sent", "Sent"], ["heard", "Heard"], ["bad", "Problems"]].map(([k, t]) => `<button class="pill ${f === k ? "on" : ""}" data-a="logFilter" data-k="${k}">${t}</button>`).join("")}
      </div>
      <div class="card" style="padding:4px 16px">${rows.length ? rows.map(item).join("") : `<div class="empty"><p>Nothing yet. Press a button here or on a real remote near the Athom.</p></div>`}</div>
      <div class="row between" style="margin-top:10px"><p class="note">Newest first. Kept until Home Assistant restarts.</p><button class="pill" data-a="logClear">Clear</button></div>`;
  }
}


// ------------------------------------------------------------------ device controls
const ZONE_COLOURS = ["#8B6CFF", "#4C8DFF", "#3DD68C"];
const FRIENDLY = [
  // [end of entity id, plain name, plain help, advanced?, dangerous?]
  ["timeout", "Stay “present” after someone leaves", "Seconds to wait before saying the room is empty.", false, false],
  ["zone_type", "What the zones do", "", false, false],
  ["multi_target_tracking", "Track up to 3 people", "Off: only the nearest person is followed.", false, false],
  ["bluetooth", "Bluetooth", "Only needed for the radar maker's phone app.", false, false],
  ["status_led", "Status light", "The small light on the sensor.", false, false],
  ["restart_esp", "Restart the sensor", "Takes about 20 seconds.", true, false],
  ["ld2450_restart", "Restart the radar", "", true, false],
  ["baud_rate", "Radar link speed", "Leave this at 256000. Changing it can cut the radar off until a reset.", true, true],
  ["ld2450_factory_reset", "Reset the radar to factory settings", "Zones and settings on the radar are wiped.", true, true],
  ["restart_with_factory_default_settings", "Restart with factory settings", "All settings go back to how they came.", true, true],
  ["safe_mode", "Restart in safe mode", "Only for repairs.", true, true],
  ["factory_reset", "Factory reset", "All settings go back to how they came.", true, true],
];
const ZONE_TYPE_WORDS = { Disabled: "Zones off", Detection: "Only see people inside the zones", Filter: "Ignore people inside the zones" };
const CONTROL_DOMAINS = ["switch", "light", "number", "select", "button", "text", "fan", "cover"];

Object.assign(AthomHubPanel.prototype, {
  devEntities(devId) {
    return Object.values(this._hass.entities || {}).filter((e) => e.device_id === devId);
  },

  findEnt(devId, suffix) {
    return this.devEntities(devId).find((e) => e.entity_id.endsWith("_" + suffix) || e.entity_id.split(".")[1] === suffix)?.entity_id;
  },

  friendly(entityId) {
    const hit = FRIENDLY.find(([end]) => entityId.endsWith("_" + end) || entityId.split(".")[1] === end);
    return hit ? { name: hit[1], help: hit[2], advanced: hit[3], danger: hit[4] } : null;
  },

  label(e) {
    const f = this.friendly(e.entity_id);
    if (f) return f.name;
    const st = this._hass.states[e.entity_id];
    const dev = this._hass.devices[e.device_id];
    let n = e.name || st?.attributes.friendly_name || e.entity_id;
    const dn = dev && (dev.name_by_user || dev.name);
    if (dn && n.startsWith(dn + " ")) n = n.slice(dn.length + 1);
    return n.replace(/[-_]/g, " ");
  },

  isRadar(devId) { return !!this.findEnt(devId, "zone_1_x1") && !!this.findEnt(devId, "target_1_x"); },

  num(id) { const v = parseFloat(this._hass.states[id]?.state); return Number.isFinite(v) ? v : null; },

  zoneOf(devId, n) {
    const g = (k) => this.num(this.findEnt(devId, `zone_${n}_${k}`));
    const z = { x1: g("x1"), y1: g("y1"), x2: g("x2"), y2: g("y2") };
    return z;
  },

  zoneEmpty(z) { return !z || (!z.x1 && !z.x2 && !z.y1 && !z.y2); },

  targets(devId) {
    const out = [];
    for (let n = 1; n <= 3; n++) {
      const x = this.num(this.findEnt(devId, `target_${n}_x`)), y = this.num(this.findEnt(devId, `target_${n}_y`));
      if (x === null || y === null || (x === 0 && y === 0)) continue;
      out.push({ n, x, y: Math.abs(y) });
    }
    return out;
  },

  vDevice(sh) {
    const dev = this._hass.devices[sh.id];
    if (!dev) return `<h2>Device not found</h2><div class="row" style="justify-content:flex-end"><button class="pill" data-a="close">Close</button></div>`;
    const name = dev.name_by_user || dev.name;
    const ents = this.devEntities(sh.id);
    const radar = this.isRadar(sh.id);
    const hideZoneNums = (id) => radar && /_zone_\d_[xy]\d$/.test(id);
    const controls = ents.filter((e) => CONTROL_DOMAINS.includes(e.entity_id.split(".")[0]) && !hideZoneNums(e.entity_id));
    const main = controls.filter((e) => !(this.friendly(e.entity_id)?.advanced) && !(e.entity_id.startsWith("button.")));
    const adv = controls.filter((e) => !main.includes(e));
    const hidden = (sh.disabled || []).filter((e) => !hideZoneNums(e.entity_id));
    return `<div class="row between"><h2>${esc(name)}</h2><button class="pill" data-a="close">Close</button></div>
      ${this.vLiveStats(sh.id)}
      ${radar ? this.vZones(sh) : ""}
      ${main.length ? `<div class="sec">Settings</div><div class="card" style="padding:4px 16px">${main.map((e) => this.vControl(e)).join("")}</div>` : ""}
      ${hidden.length ? `<div class="sec">Hidden in Home Assistant</div><div class="card" style="padding:4px 16px">${hidden.map((e) => `<div class="ctl"><div class="grow"><div class="t">${esc(this.friendly(e.entity_id)?.name || (e.original_name || e.name || e.entity_id).replace(/[-_]/g, " "))}</div><div class="s">Turned off in Home Assistant. Turn it on to use it here (takes a few seconds).</div></div><button class="pill" data-a="enableEnt" data-id="${esc(e.entity_id)}">Turn on</button></div>`).join("")}</div>` : ""}
      ${adv.length ? `<details ${sh.adv ? "open" : ""} data-adv><summary>Advanced: restart and reset</summary><div class="card" style="padding:4px 16px">${adv.map((e) => this.vControl(e)).join("")}</div></details>` : ""}`;
  },

  vLiveStats(devId) {
    const ents = this.devEntities(devId);
    const pick = (re) => ents.find((e) => re.test(e.entity_id));
    const rows = [];
    const pres = pick(/^binary_sensor\..*_presence$/);
    if (pres) rows.push(["Someone there", this._hass.states[pres.entity_id]?.state === "on" ? "Yes" : "No"]);
    const cnt = pick(/^sensor\..*_presence_target_count$/);
    if (cnt) rows.push(["People seen", String(Math.round(this.num(cnt.entity_id) ?? 0))]);
    const pir = pick(/^binary_sensor\..*_pir_sensor$/);
    if (pir) rows.push(["Movement", this._hass.states[pir.entity_id]?.state === "on" ? "Yes" : "No"]);
    const lux = pick(/^sensor\..*_light_sensor$/);
    if (lux) rows.push(["Light", `${this._hass.states[lux.entity_id]?.state ?? "–"} lx`]);
    const wifi = pick(/wifi_signal_percent$/);
    if (wifi) rows.push(["Wi-Fi", `${Math.round(this.num(wifi.entity_id) ?? 0)} %`]);
    if (!rows.length) return "";
    return `<div class="stats" id="livestats">${rows.map(([k, v]) => `<div class="stat"><div class="v">${esc(v)}</div><div class="k">${esc(k)}</div></div>`).join("")}</div>`;
  },

  vControl(e) {
    const id = e.entity_id, dom = id.split(".")[0];
    const st = this._hass.states[id];
    const f = this.friendly(id);
    const name = this.label(e);
    const off = !st || st.state === "unavailable";
    const help = f?.help ? `<div class="s">${esc(f.help)}</div>` : "";
    let ctl = "";
    if (off) ctl = `<span class="note">Offline</span>`;
    else if (dom === "switch" || dom === "light" || dom === "fan") ctl = `<button class="tog ${st.state === "on" ? "on" : ""}" data-a="ctlToggle" data-id="${esc(id)}" aria-label="${esc(name)}"></button>`;
    else if (dom === "select") {
      const words = id.endsWith("zone_type") ? ZONE_TYPE_WORDS : {};
      ctl = `<select data-ch="select" data-id="${esc(id)}">${(st.attributes.options || []).map((o) => `<option value="${esc(o)}" ${o === st.state ? "selected" : ""}>${esc(words[o] || o)}</option>`).join("")}</select>`;
    } else if (dom === "number") {
      const a = st.attributes;
      ctl = `<span class="row" style="flex-wrap:nowrap;gap:6px"><input type="number" data-ch="number" data-id="${esc(id)}" value="${esc(st.state)}" min="${a.min}" max="${a.max}" step="${a.step || 1}" style="min-width:90px;max-width:120px"><span class="note" style="margin:0">${esc(a.unit_of_measurement || "")}</span></span>`;
    } else if (dom === "text") ctl = `<input type="text" data-ch="text" data-id="${esc(id)}" value="${esc(st.state)}">`;
    else if (dom === "button") ctl = `<button class="pill ${f?.danger ? "danger" : ""}" data-a="ctlPress" data-id="${esc(id)}">${f?.danger ? "Do it…" : "Press"}</button>`;
    else if (dom === "cover") ctl = `<span class="row"><button class="pill" data-a="ctlCover" data-k="open" data-id="${esc(id)}">Open</button><button class="pill" data-a="ctlCover" data-k="close" data-id="${esc(id)}">Close</button></span>`;
    return `<div class="ctl ${dom === "select" && !off ? "col" : ""}"><div class="grow"><div class="t">${esc(name)}</div>${help}</div>${ctl}</div>`;
  },

  // ---------------- zones map
  vZones(sh) {
    const z = sh.zone || 1;
    const typeId = this.findEnt(sh.id, "zone_type");
    const type = this._hass.states[typeId]?.state;
    const draft = sh.draft?.[z];
    const saved = this.zoneOf(sh.id, z);
    const cur = draft || saved;
    const m = (v) => (v === null || v === undefined ? "" : (v / 1000).toFixed(2));
    const counts = [1, 2, 3].map((n) => Math.round(this.num(this.findEnt(sh.id, `zone_${n}_all_target_count`)) ?? 0));
    return `<div class="sec">Room map and zones</div>
      <div class="card">
        <p style="margin-top:0">The sensor is at the top, looking down into the room. Dots are people it sees right now. ${type === "Disabled" ? "<b>Zones are off.</b> Choose what zones do below to use them." : ""}</p>
        <div class="zchips">${[1, 2, 3].map((n) => { const e = this.zoneEmpty(sh.draft?.[n] || this.zoneOf(sh.id, n)); return `<button class="zchip ${n === z ? "on" : ""}" style="--zc:${ZONE_COLOURS[n - 1]}" data-a="zonePick" data-k="${n}"><span class="sw2"></span>Zone ${n}<br><small style="color:var(--tx2)">${e ? "not drawn" : `<span id="zc${n}">${counts[n - 1]}</span> inside`}</small></button>`; }).join("")}</div>
        ${this.vMap(sh)}
        <p class="note">Drag on the map to draw zone ${z}. Drag inside it to move it, or drag a corner to resize it.</p>
        <div class="row">
          <button class="pill main" data-a="zoneSave" ${draft ? "" : "disabled"}>Save zone ${z}</button>
          ${draft ? `<button class="pill" data-a="zoneUndo">Undo</button>` : ""}
          <button class="pill danger" data-a="zoneClear" ${this.zoneEmpty(cur) ? "disabled" : ""}>Remove zone ${z}</button>
        </div>
        <details ${sh.exact ? "open" : ""} data-exact><summary>Exact numbers (metres)</summary>
          <div class="nums">
            ${[["x1", "Left edge"], ["x2", "Right edge"], ["y1", "Near edge"], ["y2", "Far edge"]].map(([k, t]) => `<div><label>${t}</label><input type="number" step="0.05" data-ch="zoneNum" data-k="${k}" value="${m(cur[k])}"></div>`).join("")}
          </div>
          <p class="note">Left and right are as seen from the sensor. 0 is straight ahead.</p>
        </details>
      </div>`;
  },

  vMap(sh) {
    const R = 6000, s60 = Math.sin(Math.PI / 3), c60 = Math.cos(Math.PI / 3);
    let grid = "";
    for (let d = 1000; d <= 7000; d += 1000) grid += `<line x1="-5000" y1="${d}" x2="5000" y2="${d}" stroke="currentColor" stroke-opacity=".08" stroke-width="20"/><text x="-4900" y="${d - 60}" font-size="220" fill="currentColor" fill-opacity=".45">${d / 1000} m</text>`;
    for (let x = -4000; x <= 4000; x += 1000) grid += `<line x1="${x}" y1="0" x2="${x}" y2="7600" stroke="currentColor" stroke-opacity=".05" stroke-width="20"/>`;
    const fan = `<path d="M0 0 L${R * s60} ${R * c60} A${R} ${R} 0 0 1 ${-R * s60} ${R * c60} Z" fill="url(#fov)" stroke="#8B6CFF" stroke-opacity=".35" stroke-width="25"/>`;
    const zones = [1, 2, 3].map((n) => {
      const z = sh.draft?.[n] || this.zoneOf(sh.id, n);
      if (this.zoneEmpty(z)) return "";
      const x = Math.min(z.x1, z.x2), y = Math.min(z.y1, z.y2), w = Math.abs(z.x2 - z.x1), h = Math.abs(z.y2 - z.y1);
      const on = n === (sh.zone || 1);
      return `<g id="zone${n}"><rect x="${x}" y="${y}" width="${w}" height="${h}" rx="80" fill="${ZONE_COLOURS[n - 1]}" fill-opacity="${on ? 0.28 : 0.12}" stroke="${ZONE_COLOURS[n - 1]}" stroke-width="${on ? 50 : 25}" ${on ? "" : 'stroke-dasharray="120 80"'}/>
        <text x="${x + 120}" y="${y + 300}" font-size="260" font-weight="700" fill="${ZONE_COLOURS[n - 1]}">${n}</text>
        ${on ? [[x, y], [x + w, y], [x, y + h], [x + w, y + h]].map(([cx, cy]) => `<circle cx="${cx}" cy="${cy}" r="110" fill="#fff" stroke="${ZONE_COLOURS[n - 1]}" stroke-width="40"/>`).join("") : ""}</g>`;
    }).join("");
    return `<svg class="map" id="map" viewBox="-5000 -400 10000 8100" style="color:var(--tx)">
      <defs><radialGradient id="fov" cx="0.5" cy="0" r="1"><stop offset="0" stop-color="#8B6CFF" stop-opacity=".22"/><stop offset="1" stop-color="#4C8DFF" stop-opacity=".04"/></radialGradient></defs>
      ${grid}${fan}<g id="zones">${zones}</g>
      <rect x="-450" y="-330" width="900" height="260" rx="90" fill="#8B6CFF"/><text x="0" y="-140" font-size="170" text-anchor="middle" fill="#fff" font-weight="700">SENSOR</text>
      <g id="tg">${this.targetDots(sh.id)}</g>
    </svg>`;
  },

  targetDots(devId) {
    return this.targets(devId).map((t) => `<circle cx="${t.x}" cy="${t.y}" r="330" fill="#FFB84D" fill-opacity=".25"/><circle cx="${t.x}" cy="${t.y}" r="160" fill="#FFB84D" stroke="#fff" stroke-width="40"/>`).join("");
  },

  wireMap() {
    const svg = this.shadowRoot.getElementById("map");
    if (!svg) return;
    const sh = this.s.sheet;
    const pt = (ev) => { const p = svg.createSVGPoint(); p.x = ev.clientX; p.y = ev.clientY; const q = p.matrixTransform(svg.getScreenCTM().inverse()); return { x: q.x, y: q.y }; };
    const snap = (v) => Math.round(v / 50) * 50;
    const clamp = (z) => ({ x1: Math.max(-4860, Math.min(4860, z.x1)), x2: Math.max(-4860, Math.min(4860, z.x2)), y1: Math.max(0, Math.min(7560, z.y1)), y2: Math.max(0, Math.min(7560, z.y2)) });
    let drag = null;
    svg.addEventListener("pointerdown", (ev) => {
      const n = sh.zone || 1;
      const p = pt(ev);
      const z0 = sh.draft?.[n] || this.zoneOf(sh.id, n);
      const box = this.zoneEmpty(z0) ? null : { x1: Math.min(z0.x1, z0.x2), x2: Math.max(z0.x1, z0.x2), y1: Math.min(z0.y1, z0.y2), y2: Math.max(z0.y1, z0.y2) };
      const near = (a, b) => Math.abs(a - b) < 350;
      if (box) {
        const cx = near(p.x, box.x1) ? "x1" : near(p.x, box.x2) ? "x2" : null;
        const cy = near(p.y, box.y1) ? "y1" : near(p.y, box.y2) ? "y2" : null;
        if (cx && cy) drag = { mode: "corner", cx, cy, box };
        else if (p.x > box.x1 && p.x < box.x2 && p.y > box.y1 && p.y < box.y2) drag = { mode: "move", from: p, box };
      }
      if (!drag) drag = { mode: "draw", from: { x: snap(p.x), y: snap(Math.max(0, p.y)) } };
      this._dragging = true;
      svg.setPointerCapture(ev.pointerId);
      ev.preventDefault();
    });
    svg.addEventListener("pointermove", (ev) => {
      if (!drag) return;
      const n = sh.zone || 1, p = pt(ev);
      let z;
      if (drag.mode === "draw") z = { x1: drag.from.x, y1: drag.from.y, x2: snap(p.x), y2: snap(Math.max(0, p.y)) };
      else if (drag.mode === "move") { const dx = snap(p.x - drag.from.x), dy = snap(p.y - drag.from.y); z = { x1: drag.box.x1 + dx, x2: drag.box.x2 + dx, y1: drag.box.y1 + dy, y2: drag.box.y2 + dy }; }
      else { z = { ...drag.box }; z[drag.cx] = snap(p.x); z[drag.cy] = snap(Math.max(0, p.y)); }
      z = clamp(z);
      sh.draft = { ...(sh.draft || {}), [n]: z };
      const g = this.shadowRoot.getElementById("zones");
      if (g) g.innerHTML = this.vMap(sh).match(/<g id="zones">([\s\S]*?)<\/g>\s*<rect x="-450"/)[1];
    });
    const end = () => {
      if (!drag) return;
      drag = null; this._dragging = false;
      const n = sh.zone || 1, z = sh.draft?.[n];
      if (z) {
        const fixed = { x1: Math.min(z.x1, z.x2), x2: Math.max(z.x1, z.x2), y1: Math.min(z.y1, z.y2), y2: Math.max(z.y1, z.y2) };
        if (fixed.x2 - fixed.x1 < 200 || fixed.y2 - fixed.y1 < 200) delete sh.draft[n]; else sh.draft[n] = fixed;
      }
      this.render();
    };
    svg.addEventListener("pointerup", end);
    svg.addEventListener("pointercancel", end);
    this.shadowRoot.querySelectorAll("details[data-adv],details[data-exact]").forEach((d) => d.addEventListener("toggle", () => {
      if (d.hasAttribute("data-adv")) sh.adv = d.open; else sh.exact = d.open;
    }));
  },

  live() {
    const sh = this.s.sheet;
    if (!sh || sh.type !== "device") return;
    const root = this.shadowRoot;
    const tg = root.getElementById("tg");
    if (tg) tg.innerHTML = this.targetDots(sh.id);
    [1, 2, 3].forEach((n) => { const el = root.getElementById(`zc${n}`); if (el) el.textContent = Math.round(this.num(this.findEnt(sh.id, `zone_${n}_all_target_count`)) ?? 0); });
    const ls = root.getElementById("livestats");
    if (ls) ls.outerHTML = this.vLiveStats(sh.id);
    // Settings changed somewhere else: redraw, unless the person is typing or dragging.
    const sig = this.devEntities(sh.id).filter((e) => e.entity_category === "config").map((e) => this._hass.states[e.entity_id]?.state).join("|");
    if (sig !== this._sig) {
      const busy = this._dragging || (root.activeElement && /INPUT|SELECT/.test(root.activeElement.tagName));
      if (!busy) { this._sig = sig; this.render(); }
    }
  },

  async callSvc(domain, service, data, okText) {
    try { await this._hass.callService(domain, service, data); if (okText) this.toast(okText); return true; }
    catch (e) { this.toast(e.message || "That did not work.", true); return false; }
  },

  async actDevice(a, ds, el) {
    const s = this.s, sh = s.sheet;
    switch (a) {
      case "devOpen": {
        s.sheet = { type: "device", id: ds.id, zone: 1, draft: {} };
        this._sig = "";
        this.render();
        try {
          const reg = await this._hass.callWS({ type: "config/entity_registry/list" });
          if (s.sheet?.id === ds.id) { s.sheet.disabled = reg.filter((e) => e.device_id === ds.id && e.disabled_by && e.disabled_by !== "config_entry" && CONTROL_DOMAINS.includes(e.entity_id.split(".")[0])); this.render(); }
        } catch { /* only shown to admins anyway */ }
        return;
      }
      case "enableEnt": {
        try { await this._hass.callWS({ type: "config/entity_registry/update", entity_id: ds.id, disabled_by: null }); this.toast("Turned on. It appears here in a few seconds."); }
        catch (e) { this.toast(e.message || "Could not turn it on.", true); return; }
        sh.disabled = (sh.disabled || []).filter((e) => e.entity_id !== ds.id);
        setTimeout(() => this.render(), 12000);
        this.render();
        return;
      }
      case "ctlToggle": {
        const dom = ds.id.split(".")[0], on = this._hass.states[ds.id]?.state === "on";
        await this.callSvc(dom, on ? "turn_off" : "turn_on", { entity_id: ds.id });
        return;
      }
      case "ctlCover": await this.callSvc("cover", ds.k === "open" ? "open_cover" : "close_cover", { entity_id: ds.id }); return;
      case "ctlPress": {
        const f = this.friendly(ds.id);
        if (f?.danger) {
          s.sheet = { type: "confirm", title: `${f.name}?`, text: f.help || "Are you sure?", yes: "Yes, do it", then: async () => {
            await this.callSvc("button", "press", { entity_id: ds.id }, "Done"); s.sheet = { ...sh }; this.render();
          } };
          this.render(); return;
        }
        await this.callSvc("button", "press", { entity_id: ds.id }, "Done");
        return;
      }
      case "change": {
        if (ds.ch === "zoneNum") {
          const n = sh.zone || 1, v = parseFloat(el.value);
          if (!Number.isFinite(v)) return;
          const z = { ...(sh.draft?.[n] || this.zoneOf(sh.id, n)) };
          z[ds.k] = Math.round(v * 1000);
          sh.draft = { ...(sh.draft || {}), [n]: z };
          this.render(); return;
        }
        if (ds.ch === "select") {
          const f = this.friendly(ds.id);
          if (f?.danger) {
            const value = el.value;
            s.sheet = { type: "confirm", title: `Change ${f.name.toLowerCase()}?`, text: f.help, yes: "Change it", then: async () => {
              await this.callSvc("select", "select_option", { entity_id: ds.id, option: value }, "Saved"); s.sheet = { ...sh }; this.render();
            } };
            this.render(); return;
          }
          await this.callSvc("select", "select_option", { entity_id: ds.id, option: el.value }, "Saved"); return;
        }
        if (ds.ch === "number") { const v = parseFloat(el.value); if (Number.isFinite(v)) await this.callSvc("number", "set_value", { entity_id: ds.id, value: v }, "Saved"); return; }
        if (ds.ch === "text") { await this.callSvc("text", "set_value", { entity_id: ds.id, value: el.value }, "Saved"); return; }
        return;
      }
      case "zonePick": sh.zone = +ds.k; this.render(); return;
      case "acCopyOpen": {
        const c = s.sir.configured[+ds.i];
        const existing = (s.data.remotes || []).find((r) => r.kind === "ac" && r.name.toLowerCase().includes((c.name.match(/bed|living/i) || [""])[0].toLowerCase()) && /bed|living/i.test(c.name));
        s.sheet = { type: "acCopy", code: c.code, maker: c.maker, models: c.models, name: c.name, emitter: c.emitter, temp_sensor: this._hass.states[c.temp_sensor] ? c.temp_sensor : "", remote_id: existing?.id };
        this.render(); return;
      }
      case "acFindOpen": s.sheet = { type: "acFind", step: "brand" }; this.render(); return;
      case "acFindListen": if (sh.step === "brand") sh.brand = this.val("acbrand") || ""; await this.acListen(); return;
      case "acFindAll": sh.brand = ""; await this.acSearch(sh.token); return;
      case "acUseFound": {
        const f = sh.found.find((x) => x.code === +ds.k);
        s.sheet = { type: "acCopy", code: f.code, maker: f.maker, models: f.models, name: "Air conditioner", emitter: this.irSenders()[0]?.entity_id };
        this.render(); return;
      }
      case "acCopyDo": {
        const to = this.val("acto") || null;
        const r = await this.run(() => this.ws("smartir_copy", { code: sh.code, name: (this.val("acname") || "").trim() || "Air conditioner", remote_id: to, emitter: this.val("acfrom") || null, temp_sensor: this.val("actemp") || null }),
          (x) => `Done: ${x.codes} codes. It now works as a thermostat.`);
        if (r) { s.sheet = null; await this.load(); s.tab = "remotes"; s.remote = r.remote_id; this.render(); }
        return;
      }
      case "zoneUndo": delete sh.draft[sh.zone || 1]; this.render(); return;
      case "zoneSave": case "zoneClear": {
        const n = sh.zone || 1;
        const z = a === "zoneClear" ? { x1: 0, y1: 0, x2: 0, y2: 0 } : sh.draft?.[n];
        if (!z) return;
        let ok = true;
        for (const k of ["x1", "y1", "x2", "y2"]) {
          const id = this.findEnt(sh.id, `zone_${n}_${k}`);
          if (id) ok = (await this.callSvc("number", "set_value", { entity_id: id, value: Math.round(z[k]) })) && ok;
        }
        if (ok) { delete sh.draft[n]; this.toast(a === "zoneClear" ? `Zone ${n} removed` : `Zone ${n} saved`); }
        const typeId = this.findEnt(sh.id, "zone_type");
        if (ok && a === "zoneSave" && this._hass.states[typeId]?.state === "Disabled") this.toast(`Zone ${n} saved. Zones are off: set “What the zones do” to use it.`);
        this.render(); return;
      }
      default:
    }
  },
});


Object.assign(AthomHubPanel.prototype, {
  vAcSets() {
    const sir = this.s.sir;
    if (!sir) { this.loadSir(); return `<div class="sec">Air conditioner code sets</div><div class="card"><p>Looking for code sets…</p></div>`; }
    const conf = sir.configured.map((c, i) => `<div class="ctl"><ha-icon icon="mdi:air-conditioner" style="color:var(--acc);flex:none"></ha-icon>
        <div class="grow"><div class="t">${esc(c.name)}</div><div class="s">${esc(c.maker || "")} ${esc((c.models || []).join(", "))} · code file ${c.code}${c.error ? ` · <span class="bad">${esc(c.error)}</span>` : ""}</div></div>
        <button class="pill" data-a="acCopyOpen" data-i="${i}" ${c.error ? "disabled" : ""}>Copy</button></div>`).join("");
    return `<div class="sec">Air conditioner code sets</div>
      <div class="card">
        <p style="margin-top:0">A code set has the code for every setting of an AC (mode, fan and temperature), from SmartIR's shared library. It turns an AC into a full thermostat, and lets Athom Hub follow the real remote.</p>
        ${conf ? `<h3>Already set up in SmartIR</h3><div>${conf}</div>` : ""}
        <div class="row" style="margin-top:10px"><button class="pill main" data-a="acFindOpen"><ha-icon icon="mdi:magnify"></ha-icon>Find my AC's code set</button></div>
        ${sir.index_error ? `<p class="note bad">${esc(sir.index_error)}</p>` : `<p class="note">${sir.files} code files from ${sir.brands.length} brands.</p>`}
      </div>`;
  },

  async loadSir() {
    if (this._sirLoading) return;
    this._sirLoading = true;
    const r = await this.run(() => this.ws("smartir"));
    this.s.sir = r || { configured: [], brands: [], files: 0, index_error: "Could not load." };
    this._sirLoading = false;
    this.render();
  },

  irSenders() { return this.ports("send", "ir"); },

  vAcCopy(sh) {
    const acs = (this.s.data.remotes || []).filter((r) => r.kind === "ac");
    const temps = Object.values(this._hass.states).filter((x) => x.attributes.device_class === "temperature" && x.entity_id.startsWith("sensor."))
      .sort((a, b) => (a.attributes.friendly_name || "").localeCompare(b.attributes.friendly_name || ""));
    return `<h2>Use code set ${sh.code}</h2>
      <p>${esc(sh.maker || "")} ${esc((sh.models || []).join(", "))}</p>
      <label for="acto">Put it on</label>
      <select id="acto"><option value="">A new remote</option>${acs.map((r) => `<option value="${r.id}" ${sh.remote_id === r.id ? "selected" : ""}>${esc(r.name)} (keeps its buttons)</option>`).join("")}</select>
      <label for="acname">Name (for a new remote)</label><input id="acname" value="${esc(sh.name || "")}" maxlength="60">
      <label for="acfrom">Sends from</label>
      <select id="acfrom">${this.irSenders().map((p) => `<option value="${esc(p.entity_id)}" ${p.entity_id === sh.emitter ? "selected" : ""}>${esc(p.device_name)}${p.area ? " · " + esc(p.area) : ""}</option>`).join("")}</select>
      <p class="note">Choose the device that can see this AC.</p>
      <label for="actemp">Room temperature from</label>
      <select id="actemp"><option value="">No sensor</option>${temps.map((x) => `<option value="${esc(x.entity_id)}" ${x.entity_id === sh.temp_sensor ? "selected" : ""}>${esc(x.attributes.friendly_name || x.entity_id)}</option>`).join("")}</select>
      <div class="row" style="justify-content:flex-end;margin-top:18px"><button class="pill" data-a="close">Cancel</button><button class="pill main" data-a="acCopyDo">Use it</button></div>`;
  },

  vAcFind(sh) {
    const brands = this.s.sir?.brands || [];
    if (sh.step === "brand") {
      return `<h2>Find my AC's code set</h2>
        <p>Athom Hub listens to your real AC remote, then looks for that exact code in SmartIR's library.</p>
        <label for="acbrand">Brand of the AC</label>
        <select id="acbrand"><option value="">I don't know (search everything, takes a few minutes)</option>${brands.map((b) => `<option value="${esc(b)}" ${b === sh.brand ? "selected" : ""}>${esc(b)}</option>`).join("")}</select>
        <p class="note">Many brands are made by another company. If your brand is not listed, choose “I don't know”.</p>
        <div class="row" style="justify-content:flex-end;margin-top:18px"><button class="pill" data-a="close">Cancel</button><button class="pill main" data-a="acFindListen">Next</button></div>`;
    }
    if (sh.step === "listen") {
      return `<div class="center"><h2>Press your AC remote now</h2>
        <div class="pulse"><ha-icon icon="mdi:remote"></ha-icon></div>
        <p>Point the AC remote at the Athom from about 30 cm and press <b>Power</b> once. Any button works; the AC may switch on or off.</p>
        ${sh.count ? `<p class="note">Hearing something… (${sh.count})</p>` : ""}
        <button class="pill" data-a="close">Stop</button></div>`;
    }
    if (sh.step === "timeout") {
      return `<h2>Nothing clear was heard</h2><p>Come closer and point straight at the Athom.</p>
        <div class="row" style="justify-content:flex-end"><button class="pill" data-a="close">Cancel</button><button class="pill main" data-a="acFindListen">Try again</button></div>`;
    }
    if (sh.step === "search") {
      const pc = sh.total ? Math.round((100 * sh.done) / sh.total) : 0;
      return `<div class="center"><h2>Searching the library…</h2><div class="big">${pc}%</div>
        <p class="note">${sh.done || 0} of ${sh.total || "…"} code files${sh.brand ? ` from ${esc(sh.brand)}` : ""}.</p></div>`;
    }
    if (sh.step === "found") {
      if (!sh.found.length) {
        return `<h2>No code set has that code</h2>
          <p>${sh.brand ? `None of the ${esc(sh.brand)} files matched. Try “I don't know” to search every brand.` : "Your AC is not in SmartIR's library. You can still learn its buttons one by one in a new remote (power, cool, temperature up and down)."}</p>
          <div class="row" style="justify-content:flex-end"><button class="pill" data-a="close">Close</button>${sh.brand ? `<button class="pill main" data-a="acFindAll">Search every brand</button>` : ""}</div>`;
      }
      return `<h2>Found ${sh.found.length === 1 ? "it" : sh.found.length + " matches"} ✓</h2>
        <p>Your remote sent: <b>${esc(sh.found[0].setting)}</b>.</p>
        <div class="card" style="padding:4px 16px">${sh.found.map((f) => `<div class="ctl"><div class="grow"><div class="t">Code set ${f.code} · ${esc(f.maker)}</div><div class="s">${esc((f.models || []).join(", "))} · ${f.codes} codes</div></div><button class="pill main" data-a="acUseFound" data-k="${f.code}">Use</button></div>`).join("")}</div>
        <div class="row" style="justify-content:flex-end;margin-top:14px"><button class="pill" data-a="close">Close</button></div>`;
    }
    if (sh.step === "error") return `<h2>That did not work</h2><p>${esc(sh.why)}</p><div class="row" style="justify-content:flex-end"><button class="pill" data-a="close">Close</button></div>`;
    return "";
  },

  stopFind() {
    if (this._findUnsub) { try { this._findUnsub(); } catch { /* closed */ } this._findUnsub = null; }
  },

  async acListen() {
    const s = this.s, sh = s.sheet;
    const receiver = this.ports("receive", "ir")[0]?.entity_id;
    if (!receiver) { s.sheet = { ...sh, step: "error", why: "No infrared receiver was found." }; this.render(); return; }
    this.stopLearn();
    sh.step = "listen"; sh.count = 0; this.render();
    try {
      this._unsub = await this._hass.connection.subscribeMessage((ev) => {
        if (s.sheet !== sh) return;
        if (ev.state === "heard") { sh.count = ev.count; this.render(); }
        else if (ev.state === "timeout") { this.stopLearn(); sh.step = "timeout"; this.render(); }
        else if (ev.state === "done") { this.stopLearn(); this.acSearch(ev.token); }
      }, { type: "athom_hub/learn", receiver, kind: "ir" });
    } catch (e) { sh.step = "error"; sh.why = e.message || "Could not listen."; this.render(); }
  },

  async acSearch(token) {
    const s = this.s, sh = s.sheet;
    sh.token = token; sh.step = "search"; sh.done = 0; sh.total = 0; this.render();
    this.stopFind();
    try {
      this._findUnsub = await this._hass.connection.subscribeMessage((ev) => {
        if (s.sheet !== sh) return;
        if (ev.state === "searching") { sh.done = ev.done; sh.total = ev.total; const big = this.shadowRoot.querySelector(".big"); if (big && ev.done % 3) { big.textContent = Math.round((100 * ev.done) / ev.total) + "%"; } else this.render(); }
        else if (ev.state === "done") { this.stopFind(); sh.step = "found"; sh.found = ev.found; this.render(); }
        else if (ev.state === "error") { this.stopFind(); sh.step = "error"; sh.why = ev.why; this.render(); }
      }, { type: "athom_hub/smartir_find", token, brand: sh.brand || null });
    } catch (e) { sh.step = "error"; sh.why = e.message || "The search could not start."; this.render(); }
  },
});

function niceName(device) {
  const t = String(device || "").replace(/[_-]+/g, " ").trim();
  return t ? t.charAt(0).toUpperCase() + t.slice(1) : "Remote";
}

function guessKind(name) {
  const t = String(name || "").toLowerCase().replace(/[_-]+/g, " ");
  const has = (w) => new RegExp(`(^|[^a-z])${w}([^a-z]|$)`).test(t);
  if (["tv", "television", "screen", "projector"].some(has)) return "tv";
  if (["ac", "air", "aircon", "hvac", "climate"].some(has)) return "ac";
  if (has("fan")) return "fan";
  if (["curtain", "blind", "shade", "shutter", "roller"].some(has)) return "curtain";
  if (["light", "lamp", "led"].some(has)) return "light";
  if (["audio", "speaker", "sound", "amp", "hifi"].some(has)) return "audio";
  return "other";
}

if (!customElements.get("athom-hub-panel")) customElements.define("athom-hub-panel", AthomHubPanel);
