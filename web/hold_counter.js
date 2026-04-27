import { app } from "../../scripts/app.js";

// Frontend extension for the HoldCounter Python node:
//   * adds a momentary "reset" button that increments the hidden `reset_trigger` widget so the
//     Python side knows to rewind this node's counter,
//   * hides the `reset_trigger` integer widget so users only see the button,
//   * shows the most recent emitted index in the node body via a non-serialised text widget that
//     we update from `onExecuted`.
//
// The display widget uses LiteGraph's built-in "text" widget type (rather than ComfyWidgets'
// STRING wrapper) because the latter's return shape varies between ComfyUI versions and was
// silently leaving the widget at its falsy default ("false" rendered) on some builds.

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

function ensureDisplayWidget(node) {
    let widget = findWidget(node, DISPLAY);
    if (widget) return widget;

    // LiteGraph "text" widget: editable text input. Marked serialize:false so it never gets
    // saved/restored from the workflow JSON, and disabled so the user can't type into it.
    widget = node.addWidget("text", DISPLAY, "", () => {}, { serialize: false });
    widget.disabled = true;
    return widget;
}

function updateDisplay(node, value) {
    const widget = ensureDisplayWidget(node);
    if (!widget) return;
    widget.value = String(value);
    if (widget.inputEl) widget.inputEl.value = widget.value;
    node.setDirtyCanvas(true, true);
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
