import { app } from "../../scripts/app.js";
import { ComfyWidgets } from "../../scripts/widgets.js";

// Frontend extension for the HoldCounter Python node:
//   * adds a momentary "reset" button that increments the hidden `reset_trigger` widget so the
//     Python side knows to rewind this node's counter,
//   * hides the `reset_trigger` integer widget so users only see the button,
//   * shows the most recent emitted index in the node body via a read-only single-row textarea
//     that we update from `onExecuted`.
//
// Why a multiline STRING widget styled as a single line? Because LiteGraph's canvas-drawn "text"
// widget stops painting its value when `disabled = true` (you only see the label). The multiline
// STRING widget creates a real DOM <textarea> via `ComfyWidgets["STRING"]`, which always renders
// regardless of disabled state — the same trick used by ShowText / pysssss-style display nodes.

const TRIGGER = "reset_trigger";
const DISPLAY = "current_index";
const RESET = "reset";

function findWidget(node, name) {
    return node.widgets ? node.widgets.find((w) => w.name === name) : undefined;
}

function hideTriggerWidget(node) {
    const w = findWidget(node, TRIGGER);
    if (!w || w._hcHidden) return;
    w._hcHidden = true;
    w.type = "hidden";
    w.computeSize = () => [0, -4];
    if (w.inputEl) w.inputEl.style.display = "none";
}

function ensureResetButton(node) {
    if (findWidget(node, RESET)) return;
    node.addWidget("button", RESET, null, () => {
        const trigger = findWidget(node, TRIGGER);
        if (!trigger) return;
        trigger.value = (((trigger.value | 0) + 1) & 0x7fffffff) || 1;
        node.setDirtyCanvas(true, true);
    });
}

function styleAsReadOnlyOneLiner(widget) {
    const el = widget?.inputEl;
    if (!el) return;
    el.readOnly = true;
    el.style.opacity = "0.75";
    el.style.cursor = "default";
    // Single-row look: kill scrollbars and lock height to one line.
    el.style.overflow = "hidden";
    el.rows = 1;
    el.style.resize = "none";
}

function ensureDisplayWidget(node) {
    let widget = findWidget(node, DISPLAY);
    if (widget) {
        styleAsReadOnlyOneLiner(widget);
        return widget;
    }

    // Multiline STRING widget gives us a real <textarea> DOM element that always renders,
    // unlike a canvas-drawn "text" widget which hides its value when disabled.
    const created = ComfyWidgets["STRING"](
        node,
        DISPLAY,
        ["STRING", { multiline: true, default: "" }],
        app,
    );
    widget = created?.widget ?? findWidget(node, DISPLAY);
    if (!widget) return null;

    widget.value = "";
    // Don't persist the live display value into the saved workflow.
    widget.serializeValue = () => "";
    styleAsReadOnlyOneLiner(widget);
    // The DOM element is created asynchronously on some builds — re-apply once next frame.
    requestAnimationFrame(() => styleAsReadOnlyOneLiner(widget));
    return widget;
}

function updateDisplay(node, value) {
    const widget = ensureDisplayWidget(node);
    if (!widget) return;
    const text = String(value);
    widget.value = text;
    if (widget.inputEl) widget.inputEl.value = text;
    app.graph.setDirtyCanvas(true, true);
}

app.registerExtension({
    name: "HoldCounter.UI",

    async beforeRegisterNodeDef(nodeType, nodeData, _app) {
        if (nodeData.name !== "HoldCounter") return;

        const onNodeCreated = nodeType.prototype.onNodeCreated;
        nodeType.prototype.onNodeCreated = function () {
            onNodeCreated?.apply(this, arguments);
            hideTriggerWidget(this);
            ensureResetButton(this);
            ensureDisplayWidget(this);
            this.setSize?.(this.computeSize());
        };

        // Workflow load: widgets are restored from JSON before this fires, so re-apply hiding /
        // button / display widget once the node exists.
        const onConfigure = nodeType.prototype.onConfigure;
        nodeType.prototype.onConfigure = function (_info) {
            onConfigure?.apply(this, arguments);
            hideTriggerWidget(this);
            ensureResetButton(this);
            ensureDisplayWidget(this);
        };

        const onExecuted = nodeType.prototype.onExecuted;
        nodeType.prototype.onExecuted = function (message) {
            onExecuted?.apply(this, arguments);
            const text = message?.text?.[0];
            if (text === undefined || text === null) return;
            updateDisplay(this, text);
        };
    },
});
