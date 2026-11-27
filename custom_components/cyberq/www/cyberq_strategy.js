// CyberQ dashboard strategy: one view per CyberQ device.
//
// Served and loaded by the cyberq integration (see strategy.py); no
// Lovelace resource is needed.
//
// Dashboard config:  strategy: {type: custom:cyberq}
// Single view:       strategy: {type: custom:cyberq, device_id: <id>}
//
// Entities are grouped by device_id and matched on the stable part of
// their unique_id ("<device name>_<key>"), so renaming an entity_id
// does not break the view.
//
// With Mushroom installed, the cook and each probe get one template
// card colored by distance from the setpoint (see BANDS); without it
// they fall back to plain entities cards.
//
// The graph uses apexcharts-card if installed, else mini-graph-card,
// else the core history graph. Probes unplugged when the view is built
// are left out of the custom graphs.
//
// The cook and probe names and the settings are on a Settings card that
// folds to its title (cyberq-collapsible-card, defined below).

const CYBERQ_KEYS = [
    "pit_probe", "food1_probe", "food2_probe", "food3_probe",
    "pit_status", "probe1_status", "probe2_status", "probe3_status",
    "cook_name", "probe1_name", "probe2_name", "probe3_name",
    "fan_speed", "cook_ramp", "alarm_beeps", "timeout_action",
];

async function cyberqDevices(hass) {
    const [entities, devices, areas] = await Promise.all([
        hass.callWS({ type: "config/entity_registry/list" }),
        hass.callWS({ type: "config/device_registry/list" }),
        hass.callWS({ type: "config/area_registry/list" }),
    ]);
    const byId = new Map(devices.map((d) => [d.id, d]));
    const areaName = new Map(areas.map((a) => [a.area_id, a.name]));
    const result = new Map();

    for (const entity of entities) {
        if (entity.platform !== "cyberq" || !entity.device_id) continue;
        if (entity.disabled_by) continue;

        const device = byId.get(entity.device_id);
        let entry = result.get(entity.device_id);
        if (!entry) {
            const name = (device && (device.name_by_user || device.name))
                || entity.device_id;
            const area = device && device.area_id
                ? areaName.get(device.area_id) : null;
            entry = {
                device_id: entity.device_id,
                name: area ? `${name} (${area})` : name,
                entities: {},
            };
            result.set(entity.device_id, entry);
        }

        const uid = String(entity.unique_id);
        const prefix = device && device.name ? `${device.name}_` : null;
        const key = prefix && uid.startsWith(prefix)
            ? uid.slice(prefix.length)
            : uid.slice(uid.indexOf("_") + 1);
        if (CYBERQ_KEYS.includes(key)) {
            entry.entities[key] = entity.entity_id;
        }
    }

    return Array.from(result.values())
        .sort((a, b) => a.name.localeCompare(b.name));
}

// Temperature bands relative to the setpoint, in °F:
// blue below -far, amber below -near, green within ±near, red above +near.
const BANDS = {
    pit: { far: 25, near: 5 },
    food: { far: 20, near: 5 },
};

// Probe status values meaning no probe is plugged in.
const PROBE_OFF = ["error", "unavailable", "unknown"];

// Graph line colors: pit, its setpoint, then probes 1-3.
const COLORS = {
    pit: "#e65100",
    probes: ["#1e88e5", "#43a047", "#8e24aa"],
};

// Custom cards load as separate resources, possibly after this one.
async function haveCard(tag) {
    if (customElements.get(tag)) return true;
    return Promise.race([
        customElements.whenDefined(tag).then(() => true),
        new Promise((resolve) => setTimeout(() => resolve(false), 2000)),
    ]);
}

function tempUnit(hass) {
    const unit = hass.config && hass.config.unit_system
        && hass.config.unit_system.temperature;
    return unit || "°";
}

// One card for the cook or a probe: assigned name, label and status,
// current temperature against the setpoint, icon colored by how close
// they are (see BANDS), and a setpoint control. Clicking the card opens
// the thermostat dialog; clicking the icon or holding the card edits
// the name.
function groupCard(opts) {
    const { climate, nameEntity, statusEntity, label, icon, band, unit } =
        opts;
    const scale = unit === "°C" ? 5 / 9 : 1;
    const far = Math.round(band.far * scale * 10) / 10;
    const near = Math.round(band.near * scale * 10) / 10;
    const vars = "{% set c = state_attr(entity, 'current_temperature') %}"
        + "{% set t = state_attr(entity, 'temperature') %}";
    const status = statusEntity
        ? ` · {{ state_translated('${statusEntity}') }}` : "";
    return {
        type: "custom:mushroom-template-card",
        entity: climate,
        primary: nameEntity
            ? `{{ states('${nameEntity}') or '${label}' }}` : label,
        secondary: `${label}${status}\n` + vars
            + `{% if c is not none %}{{ c }}${unit}{% else %}—{% endif %}`
            + `{% if t is not none %} → {{ t }}${unit}{% endif %}`,
        multiline_secondary: true,
        icon: icon,
        color: vars
            + "{% if c is none or t is none %}disabled"
            + "{% else %}{% set d = c | float - t | float %}"
            + `{% if d > ${near} %}red`
            + `{% elif d >= -${near} %}green`
            + `{% elif d >= -${far} %}amber`
            + "{% else %}blue{% endif %}{% endif %}",
        tap_action: { action: "more-info" },
        ...(nameEntity ? {
            icon_tap_action: { action: "more-info", entity: nameEntity },
            hold_action: { action: "more-info", entity: nameEntity },
        } : {}),
        features: [{ type: "target-temperature" }],
        features_position: "bottom",
        // A fixed height (Mushroom's own default for one feature) keeps
        // the card from stretching to the tallest card in its row, such
        // as an open Settings card.
        grid_options: { columns: 12, rows: 2 },
    };
}

function errorView(title, error) {
    console.error("CyberQ strategy:", error);
    return {
        title: title,
        cards: [{
            type: "markdown",
            content: `CyberQ strategy failed: ${error}`,
        }],
    };
}

class StrategyDashboardCyberq {
    static async generate(config, hass) {
        try {
            const devices = await cyberqDevices(hass);
            if (devices.length === 0) {
                return { title: "CyberQ", views: [errorView("CyberQ",
                    "no enabled CyberQ entities found")] };
            }
            return {
                title: "CyberQ",
                views: devices.map((device) => ({
                    title: device.name,
                    strategy: {
                        type: "custom:cyberq",
                        device_id: device.device_id,
                        name: device.name,
                        entities: device.entities,
                    },
                })),
            };
        } catch (error) {
            return { title: "CyberQ", views: [errorView("CyberQ", error)] };
        }
    }
}

class StrategyViewCyberq {
    static async generate(config, hass) {
        const title = config.name || "CyberQ";
        try {
            let e = config.entities;
            let name = config.name;
            if (!e) {
                // View used on its own: look the device up.
                const device = (await cyberqDevices(hass))
                    .find((d) => d.device_id === config.device_id);
                if (!device) {
                    throw new Error(`no CyberQ device ${config.device_id}`);
                }
                e = device.entities;
                name = name || device.name;
            }
            const [mushroom, apex, miniGraph] = await Promise.all([
                haveCard("mushroom-template-card"),
                haveCard("apexcharts-card"),
                haveCard("mini-graph-card"),
            ]);
            const temps = mushroom ? tempUnit(hass) : null;
            return {
                title: name || title,
                type: "sections",
                max_columns: 3,
                sections: [
                    CyberqView.sectionGraph(e, hass, { apex, miniGraph }),
                    CyberqView.sectionStatus(e, hass, temps,
                                             config.device_id),
                    CyberqView.sectionHint(temps, { apex, miniGraph }),
                ].filter((s) => s !== null),
            };
        } catch (error) {
            return errorView(title, error);
        }
    }
}

class CyberqView {
    // Entity rows for the keys that exist on this device.
    static rows(e, rows) {
        return rows
            .filter((row) => e[row.key])
            .map(({ key, ...row }) => ({ entity: e[key], ...row }));
    }

    // Temperature graph, best available first:
    //   apexcharts-card: axes, tooltips, dashed setpoint lines;
    //   mini-graph-card: compact lines, no time axis;
    //   core history graph.
    // The custom graphs get a fixed series list (apexcharts-card does
    // not reload history when reconfigured): probes unplugged when the
    // view is built are left out, and with apexcharts-card a probe
    // unplugged later loses its setpoint line through a transform.
    static sectionGraph(e, hass, cards) {
        let card = null;
        if (e.pit_probe && cards.apex) {
            card = CyberqView.cardGraph(e, hass, "apex");
        } else if (e.pit_probe && cards.miniGraph) {
            card = CyberqView.cardGraph(e, hass, "mini");
        }
        if (!card) return CyberqView.sectionHistoryGraph(e);
        return { type: "grid", column_span: 3, cards: [card] };
    }

    // Current and setpoint series for one climate entity, without names.
    static series(kind, entity, color, status) {
        if (kind === "apex") {
            const target = {
                entity: entity, attribute: "temperature", color: color,
                stroke_width: 1, stroke_dash: 6, curve: "stepline",
                opacity: 0.8,
            };
            if (status) {
                target.transform = `const s = hass.states['${status}'];`
                    + " return s && PROBE_OFF.includes(s.state)"
                    + " ? null : x;";
                target.transform = target.transform.replace(
                    "PROBE_OFF", JSON.stringify(PROBE_OFF));
            }
            return [
                { entity: entity, attribute: "current_temperature",
                  color: color, stroke_width: 2 },
                target,
            ];
        }
        return [
            { entity: entity, attribute: "current_temperature",
              color: color },
            { entity: entity, attribute: "temperature",
              color: color + "66", show_points: false },
        ];
    }

    // Name and plugged-in state of a probe as of now.
    static probeNow(e, hass, i) {
        const states = (hass && hass.states) || {};
        const status = states[e[`probe${i}_status`]];
        const name = states[e[`probe${i}_name`]];
        return {
            plugged: !status || !PROBE_OFF.includes(status.state),
            name: (name && name.state
                   && !PROBE_OFF.includes(name.state))
                ? name.state : `Probe ${i}`,
        };
    }

    static cardGraph(e, hass, kind) {
        const list = CyberqView.series(kind, e.pit_probe, COLORS.pit, null);
        list[0].name = "Pit";
        list[1].name = "Pit target";

        for (const i of [1, 2, 3]) {
            if (!e[`food${i}_probe`]) continue;
            const now = CyberqView.probeNow(e, hass, i);
            if (!now.plugged) continue;
            const [cur, tgt] = CyberqView.series(
                kind, e[`food${i}_probe`], COLORS.probes[i - 1],
                e[`probe${i}_status`]);
            list.push({ ...cur, name: now.name },
                      { ...tgt, name: `${now.name} target` });
        }

        if (kind === "apex") {
            return {
                type: "custom:apexcharts-card",
                graph_span: "2h",
                header: { show: false },
                all_series_config: { show: { legend_value: false } },
                yaxis: [{ decimals: 0 }],
                apex_config: {
                    chart: { height: 280 },
                    legend: { show: true, position: "top" },
                    tooltip: { x: { format: "HH:mm" } },
                },
                series: list,
                grid_options: { columns: "full" },
            };
        }
        return {
            type: "custom:mini-graph-card",
            hours_to_show: 2,
            points_per_hour: 30,
            line_width: 2,
            height: 180,
            show: {
                name: false, icon: false, state: false, fill: false,
                points: false, legend: true, labels: true,
            },
            entities: list,
            grid_options: { columns: "full" },
        };
    }

    static sectionHistoryGraph(e) {
        const entities = CyberqView.rows(e, [
            { key: "pit_probe", name: "Pit" },
            { key: "food1_probe", name: "Probe 1" },
            { key: "food2_probe", name: "Probe 2" },
            { key: "food3_probe", name: "Probe 3" },
        ]);
        if (entities.length === 0) return null;
        return {
            type: "grid",
            column_span: 3,
            cards: [{
                type: "history-graph",
                hours_to_show: 2,
                grid_options: { columns: "full" },
                min_y_axis: 33,
                entities: entities,
            }],
        };
    }

    // One Cook or Probe card: a single Mushroom card (unit set), else
    // a plain entities card.
    static cardGroup(e, unit, opts) {
        const { label, nameKey, statusKey, climateKey, icon, band } = opts;
        if (unit && e[climateKey]) {
            return groupCard({
                climate: e[climateKey], nameEntity: e[nameKey],
                statusEntity: e[statusKey], label, icon, band, unit,
            });
        }
        // Names are edited on the Settings card.
        const rows = CyberqView.rows(e, [
            { key: statusKey, name: "Status" },
            { key: climateKey, name: "Temperature" },
        ]);
        return rows.length > 0
            ? { type: "entities", title: label, entities: rows }
            : null;
    }

    // Cook, probe, fan speed and settings cards in one section, sized
    // when the view is built from the probes plugged in then:
    //   2+ probes: cook and probes fill the first row (1/3 or 1/4 each),
    //              fan speed and settings wrap below at the same width;
    //   0-1 probes: fan speed and settings join the first row.
    // A row is never split into fewer than three slots. A probe plugged
    // in later appears without resizing until the page is reloaded.
    // unit is null when Mushroom is unavailable: plain entity rows then.
    static sectionStatus(e, hass, unit, deviceId) {
        const groups = [];
        const cook = CyberqView.cardGroup(e, unit, {
            label: "Cook", nameKey: "cook_name", statusKey: "pit_status",
            climateKey: "pit_probe", icon: "mdi:grill", band: BANDS.pit,
        });
        if (cook) groups.push(cook);
        let plugged = 0;
        for (const i of [1, 2, 3]) {
            const card = CyberqView.cardProbe(i, e, unit);
            if (!card) continue;
            groups.push(card);
            if (CyberqView.probeNow(e, hass, i).plugged) plugged++;
        }
        const extra = CyberqView.cardsSettings(e, deviceId);
        const shown = (cook ? 1 : 0) + plugged
            + (plugged < 2 ? extra.length : 0);
        const width = Math.floor(36 / Math.max(3, shown));
        const sized = (card) => {
            const out = { ...card,
                          grid_options: { ...(card.grid_options || {}),
                                          columns: width } };
            if (out.card) out.card = sized(out.card);
            return out;
        };
        const cards = [...groups, ...extra].map(sized);
        if (cards.length === 0) return null;
        return { type: "grid", column_span: 3, cards: cards };
    }

    // Footer tips: the Mushroom card gestures when Mushroom is
    // installed, and which Marketplace cards would improve the view.
    static sectionHint(unit, cards) {
        const tips = [];
        if (unit) {
            tips.push("Select a card to change its setpoint. Hold a card,"
                + " or select its icon, to rename it. Names and settings"
                + " are also on the Settings card.");
        } else {
            tips.push("Install **Mushroom** from the Marketplace for one"
                + " card per cook and probe, colored by how close it is"
                + " to the setpoint.");
        }
        if (!cards.apex) {
            const now = cards.miniGraph ? "mini-graph-card" : "a basic graph";
            tips.push("Install **ApexCharts Card** from the Marketplace for"
                + " a graph with time and temperature axes and setpoint"
                + ` lines (now using ${now}).`);
        }
        const content = tips.map((tip) => `Tip: ${tip}`).join("<br>");
        return {
            type: "grid",
            column_span: 3,
            cards: [{
                type: "markdown",
                text_only: true,
                content: `<small>${content}</small>`,
                grid_options: { columns: "full" },
            }],
        };
    }

    static cardProbe(i, e, unit) {
        const card = CyberqView.cardGroup(e, unit, {
            label: `Probe ${i}`, nameKey: `probe${i}_name`,
            statusKey: `probe${i}_status`, climateKey: `food${i}_probe`,
            icon: "mdi:thermometer", band: BANDS.food,
        });
        if (!card) return null;
        const status = e[`probe${i}_status`];
        if (!status) return card;
        // The conditional card reports no size of its own, so give it the
        // inner card's; without rows it stretches to fill its grid row.
        return {
            type: "conditional",
            conditions: [{
                condition: "state",
                entity: status,
                state_not: PROBE_OFF,
            }],
            card: card,
            ...(card.grid_options ? { grid_options: card.grid_options } : {}),
        };
    }

    // Fan speed graph, and a collapsible Settings card with the cook and
    // probe names followed by the other settings.
    static cardsSettings(e, deviceId) {
        const cards = [];
        if (e.fan_speed) {
            cards.push({
                type: "sensor",
                entity: e.fan_speed,
                name: "Fan speed",
                graph: "line",
                detail: 2,
                hours_to_show: 2,
                grid_options: { rows: 3 },
            });
        }
        const names = CyberqView.rows(e, [
            { key: "cook_name", name: "Cook" },
            { key: "probe1_name", name: "Probe 1" },
            { key: "probe2_name", name: "Probe 2" },
            { key: "probe3_name", name: "Probe 3" },
        ]);
        const settings = CyberqView.rows(e, [
            { key: "cook_ramp", name: "Ramp Probe" },
            { key: "alarm_beeps", name: "Alarm Beeps" },
            { key: "timeout_action", name: "Timeout Action" },
        ]);
        const entities = [
            ...(names.length > 0
                ? [{ type: "section", label: "Names" }, ...names] : []),
            ...(names.length > 0 && settings.length > 0
                ? [{ type: "divider" }] : []),
            ...settings,
            ...(deviceId
                ? [{ type: "divider" },
                   { type: "custom:cyberq-reset-row", device_id: deviceId }]
                : []),
        ];
        if (entities.length > 0) {
            cards.push({
                type: "custom:cyberq-collapsible-card",
                title: "Settings",
                storage_key: deviceId || "default",
                card: { type: "entities", entities: entities },
            });
        }
        return cards;
    }
}

// Browser storage can be missing or throw (private windows, blocked
// site data); the card then just starts collapsed.
function readOpen(key) {
    try {
        return window.localStorage.getItem(key) === "1";
    } catch (error) {
        return false;
    }
}

function writeOpen(key, open) {
    try {
        window.localStorage.setItem(key, open ? "1" : "0");
    } catch (error) {
        // Not remembered; nothing else to do.
    }
}

// A card that folds to its title. Config: {title, storage_key, card},
// where card is any card config, built with Home Assistant's card
// helpers. Starts collapsed; the open state is remembered per
// storage_key in this browser.
class CyberqCollapsibleCard extends HTMLElement {
    setConfig(config) {
        if (!config || !config.card) {
            throw new Error("card is required");
        }
        this._config = config;
        this._key = `cyberq-collapsible-${config.storage_key || "default"}`;
        this._open = readOpen(this._key);
        this._inner = null;
        this._render();
    }

    set hass(hass) {
        this._hass = hass;
        if (this._inner) this._inner.hass = hass;
    }

    getCardSize() {
        if (!this._open) return 1;
        const inner = this._inner && this._inner.getCardSize
            ? this._inner.getCardSize() : 3;
        return 1 + (typeof inner === "number" ? inner : 3);
    }

    getGridOptions() {
        return { columns: 12, rows: "auto" };
    }

    _render() {
        if (!this.shadowRoot) this.attachShadow({ mode: "open" });
        const root = this.shadowRoot;
        root.innerHTML = `
            <style>
                .header {
                    display: flex;
                    align-items: center;
                    justify-content: space-between;
                    padding: 12px 16px;
                    cursor: pointer;
                    user-select: none;
                    font-size: var(--ha-card-header-font-size, 20px);
                    color: var(--ha-card-header-color,
                               var(--primary-text-color));
                }
                .header:focus-visible {
                    outline: 2px solid var(--primary-color);
                    outline-offset: -2px;
                }
                .body {
                    --ha-card-border-width: 0;
                    --ha-card-box-shadow: none;
                    --ha-card-background: transparent;
                    --ha-card-border-radius: 0;
                }
                .body[hidden] { display: none; }
            </style>
            <ha-card>
                <div class="header" role="button" tabindex="0"></div>
                <div class="body"></div>
            </ha-card>`;
        const header = root.querySelector(".header");
        const title = document.createElement("span");
        title.textContent = this._config.title || "";
        this._chevron = document.createElement("ha-icon");
        header.append(title, this._chevron);
        header.addEventListener("click", () => this._toggle());
        header.addEventListener("keydown", (ev) => {
            if (ev.key === "Enter" || ev.key === " ") {
                ev.preventDefault();
                this._toggle();
            }
        });
        this._header = header;
        this._body = root.querySelector(".body");
        this._update();
    }

    _toggle() {
        this._open = !this._open;
        writeOpen(this._key, this._open);
        this._update();
    }

    _update() {
        this._header.setAttribute("aria-expanded", String(this._open));
        this._chevron.setAttribute("icon", this._open
            ? "mdi:chevron-up" : "mdi:chevron-down");
        this._body.hidden = !this._open;
        if (this._open && !this._inner) this._build();
    }

    async _build() {
        const config = this._config;
        const helpers = await window.loadCardHelpers();
        if (this._config !== config || this._inner) return;
        const inner = helpers.createCardElement(config.card);
        if (this._hass) inner.hass = this._hass;
        this._inner = inner;
        this._body.append(inner);
    }
}

// Entities card row that resets the cook and probe names and turns off
// the ramp with the cyberq.reset_cook action. Config: {device_id}. The
// first press asks for confirmation on the button itself; a second
// press within five seconds resets.
class CyberqResetRow extends HTMLElement {
    setConfig(config) {
        this._config = config;
        this._armed = false;
        this._busy = false;
        this._render();
    }

    set hass(hass) {
        this._hass = hass;
    }

    _render() {
        if (!this.shadowRoot) this.attachShadow({ mode: "open" });
        this.shadowRoot.innerHTML = `
            <style>
                .row {
                    display: flex;
                    align-items: center;
                    gap: 16px;
                    min-height: 40px;
                }
                ha-icon {
                    color: var(--state-icon-color,
                               var(--paper-item-icon-color));
                    flex: none;
                    width: 40px;
                    display: flex;
                    justify-content: center;
                }
                .label { flex: 1; }
                button {
                    font: inherit;
                    border: none;
                    border-radius: 18px;
                    padding: 6px 16px;
                    cursor: pointer;
                    color: var(--primary-color);
                    background: transparent;
                }
                button.armed {
                    color: var(--text-primary-color, #fff);
                    background: var(--error-color, #db4437);
                }
                button:disabled { opacity: 0.5; cursor: default; }
            </style>
            <div class="row">
                <ha-icon icon="mdi:restore"></ha-icon>
                <span class="label">Reset names and ramp</span>
                <button type="button"></button>
            </div>`;
        this._button = this.shadowRoot.querySelector("button");
        this._button.addEventListener("click", () => this._press());
        this._update();
    }

    _update() {
        this._button.textContent = this._busy ? "Resetting…"
            : this._armed ? "Confirm"
            : this._failed ? "Failed, see browser log" : "Reset";
        this._button.classList.toggle("armed", this._armed);
        this._button.disabled = this._busy;
    }

    async _press() {
        if (!this._hass || this._busy) return;
        if (!this._armed) {
            this._armed = true;
            this._failed = false;
            this._update();
            clearTimeout(this._timer);
            this._timer = setTimeout(() => {
                this._armed = false;
                this._update();
            }, 5000);
            return;
        }
        clearTimeout(this._timer);
        this._armed = false;
        this._busy = true;
        this._update();
        try {
            await this._hass.callService(
                "cyberq", "reset_cook", { device_id: this._config.device_id });
            this._failed = false;
        } catch (error) {
            console.error("CyberQ reset failed:", error);
            this._failed = true;
        }
        if (this._failed) {
            this._timer = setTimeout(() => {
                this._failed = false;
                this._update();
            }, 5000);
        }
        this._busy = false;
        this._update();
    }
}

// Skip if another copy (e.g. an old /local resource) already loaded.
if (!customElements.get("ll-strategy-dashboard-cyberq")) {
    customElements.define("ll-strategy-dashboard-cyberq",
                          StrategyDashboardCyberq);
}
if (!customElements.get("ll-strategy-view-cyberq")) {
    customElements.define("ll-strategy-view-cyberq", StrategyViewCyberq);
}
if (!customElements.get("cyberq-reset-row")) {
    customElements.define("cyberq-reset-row", CyberqResetRow);
}
if (!customElements.get("cyberq-collapsible-card")) {
    customElements.define("cyberq-collapsible-card", CyberqCollapsibleCard);
}
