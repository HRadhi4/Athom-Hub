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
.tabs{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:6px;padding:5px;border-radius:18px;background:var(--card);border:1px solid var(--line);margin-bottom:16px}
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
.rb.sent{box-shadow:0 0 0 2px var(--acc),var(--glow)}
.rb small{color:var(--tx2);font-size:12px;font-weight:400}
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
    else body = this.vBroadlink();

    this.shadowRoot.innerHTML = `<style>${CSS}</style>
      <div class="wrap">
        <div class="top">
          ${this._narrow ? `<button class="iconbtn" data-a="menu" aria-label="Menu"><ha-icon icon="mdi:menu"></ha-icon></button>` : ""}
          <div style="min-width:0"><h1>Athom Hub</h1><div class="sum">${esc(sum)}</div></div>
        </div>
        <div class="tabs">
          ${[["remotes", "Remotes"], ["devices", "Devices"], ["broadlink", "From Broadlink"]]
            .map(([k, t]) => `<button class="tab ${this.s.tab === k ? "on" : ""}" data-a="tab" data-k="${k}">${t}</button>`).join("")}
        </div>
        ${body}
      </div>
      ${this.s.sheet ? `<div class="shade" data-a="shade"><div class="sheet">${this.vSheet()}</div></div>` : ""}
      ${this.s.toast ? `<div class="toast ${this.s.toast.bad ? "bad" : ""}">${esc(this.s.toast.text)}</div>` : ""}`;
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
          <div class="t" style="font-weight:600;overflow-wrap:anywhere">${esc(b.name)}</div>
          <div class="note" style="margin:2px 0 8px">${KIND_WORD[b.kind] || ""} · ${b.pulses} pulses${b.source === "broadlink" ? " · from Broadlink" : ""}</div>
          <div class="row">
            <button class="pill" data-a="renameBtn" data-id="${b.id}">Rename</button>
            <button class="pill" data-a="relearn" data-id="${b.id}">Learn again</button>
            ${i ? `<button class="iconbtn" data-a="up" data-id="${b.id}" aria-label="Move up"><ha-icon icon="mdi:arrow-up"></ha-icon></button>` : ""}
            <button class="iconbtn" data-a="delBtn" data-id="${b.id}" aria-label="Delete" style="color:var(--bad)"><ha-icon icon="mdi:delete-outline"></ha-icon></button>
          </div></div>`
      : `<button class="rb" data-a="press" data-id="${b.id}"><ha-icon icon="${b.kind === "rf" ? "mdi:radio-tower" : "mdi:remote"}"></ha-icon>${esc(b.name)}</button>`).join("");
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
      </div>
      ${r.buttons.length
        ? `<div class="${edit ? "list" : "btns"}">${buttons}</div>`
        : `<div class="card empty"><h2>No buttons yet</h2><p>Tap “Add a button”, then press the button on your real remote, pointed at the Athom.</p></div>`}
      <div class="row" style="margin-top:14px"><button class="pill main" data-a="learn"><ha-icon icon="mdi:plus"></ha-icon>Add a button</button></div>
      <p class="note">Each button is also a normal Home Assistant button, so you can use it on dashboards and in automations.</p>`;
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
    return `<p class="note" style="margin-top:0">Remotes a Broadlink learned through Home Assistant. Copy one, then press each button once to check it.</p>
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
        <label>Infrared buttons send from</label>${sel("ir")}
        <label>Radio buttons send from</label>${sel("rf")}
        <div class="row between" style="margin-top:18px">
          ${r ? `<button class="pill danger" data-a="delRemote">Delete remote</button>` : "<span></span>"}
          <div class="row">${close}<button class="pill main" data-a="saveRemote">Save</button></div>
        </div>`;
    }
    if (sh.type === "rename") {
      return `<h2>Rename button</h2><label for="bname">Name</label><input id="bname" value="${esc(sh.name)}" maxlength="60">
        <div class="row" style="margin-top:18px;justify-content:flex-end">${close}<button class="pill main" data-a="saveName">Save</button></div>`;
    }
    if (sh.type === "confirm") {
      return `<h2>${esc(sh.title)}</h2><p>${esc(sh.text)}</p>
        <div class="row" style="margin-top:18px;justify-content:flex-end">${close}<button class="pill main danger" style="background:var(--bad)" data-a="confirmYes">${esc(sh.yes)}</button></div>`;
    }
    if (sh.type === "learn") return this.vLearn(sh);
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
    const tf = root.getElementById("tfrom");
    if (tf) tf.addEventListener("change", () => { this.s.test.from = tf.value; });
  }

  val(id) { const el = this.shadowRoot.getElementById(id); return el ? el.value : undefined; }

  async act(a, ds) {
    const s = this.s;
    switch (a) {
      case "menu": this.dispatchEvent(new Event("hass-toggle-menu", { bubbles: true, composed: true })); return;
      case "reload": s.err = ""; this.render(); this.load(); return;
      case "tab": s.tab = ds.k; s.remote = null; s.edit = false; this.render(); return;
      case "open": s.remote = ds.id; s.edit = false; this.render(); return;
      case "back": s.remote = null; s.edit = false; this.render(); return;
      case "edit": s.edit = !s.edit; this.render(); return;
      case "toggle": s.open[ds.id] = !s.open[ds.id]; this.render(); return;
      case "shade": case "close": this.stopLearn(); s.sheet = null; this.render(); return;
      case "newRemote": s.sheet = { type: "newRemote" }; this.render(); return;
      case "remoteSettings": s.sheet = { type: "remoteSettings" }; this.render(); return;
      case "pickKind": s.sheet.name = this.val("rname"); s.sheet.kind = ds.k; this.render(); return;
      case "saveRemote": {
        const sh = s.sheet;
        const msg = { name: (this.val("rname") || "").trim() || KINDS[sh.kind || this.remote()?.kind || "tv"][0], kind: sh.kind || this.remote()?.kind || "tv" };
        for (const k of ["ir", "rf"]) { const v = this.val(`em_${k}`); if (v !== undefined) msg[`emitter_${k}`] = v; }
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
        if (el) el.classList.add("sent");
        await this.run(() => this.ws("press", { remote_id: s.remote, button_id: ds.id }));
        setTimeout(() => el && el.classList.remove("sent"), 400);
        return;
      }
      case "renameBtn": { const b = this.remote().buttons.find((x) => x.id === ds.id); s.sheet = { type: "rename", id: ds.id, name: b.name }; this.render(); return; }
      case "saveName": {
        const name = (this.val("bname") || "").trim(); if (!name) return;
        const r = await this.run(() => this.ws("button_save", { remote_id: s.remote, button_id: s.sheet.id, name }), "Renamed");
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

  disconnectedCallback() { this.stopLearn(); }
}

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
