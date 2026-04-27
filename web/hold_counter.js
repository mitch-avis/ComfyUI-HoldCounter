import { app } from "../../scripts/app.js";
import { ComfyWidgets } from "../../scripts/widgets.js";

// Frontend extension for the HoldCounter Python node:
//   * displays the current `index` value in the node body each run,
//   * provides a momentary "Reset" button that increments the hidden `reset_trigger` widget so the
//     Python side knows to rewind the per-node counter,
//   * hides the `reset_trigger` widget from the UI so users only see the button.
app.registerExtension({
    name: "HoldCounter.UI",

    async beforeRegisterNodeDef(nodeType, nodeData, _app) {
        if (nodeData.name !== "HoldCounter") return;

        const DISPLAY = "current_index";
        const TRIGGER = "reset_trigger";

        function styleReadOnly(widget) {
            const el = widget?.inputEl;
            if (!el) return;
            el.readOnly = true;
            el.style.opacity = "0.75";
        }

        function ensureDisplayWidget(node) {
            let widget = node.widgets?.find((w) => w.name === DISPLAY);
            if (widget) return widget;

            const created = ComfyWidgets["STRING"](
                node,
                DISPLAY,
                ["STRING", { multiline: false }],
                app,
            );
            widget = created?.widget ?? node.widgets?.find((w) => w.name === DISPLAY);
            if (!widget) return null;

            widget.value = "";
            widget.serializeValue = () => "";
            styleReadOnly(widget);
            requestAnimationFrame(() => styleReadOnly(widget));
            return widget;
        }

        function hideWidget(widget) {
            if (!widget || widget._hcHidden) return;
            widget._hcHidden = true;
            widget.type = "hidden";
            widget.computeSize = () => [0, -4];
            // Hide any DOM element backing it (none for INT, but defensive for future widget
            // types).
            if (widget.inputEl) widget.inputEl.style.display = "none";
        }

        function addResetButton(node) {
            if (node.widgets?.find((w) => w.name === "reset")) return;
            node.addWidget("button", "reset", null, () => {
                const trigger = node.widgets?.find((w) => w.name === TRIGGER);
                if (!trigger) return;
                trigger.value = ((trigger.value | 0) + 1) & 0x7fffffff;
                node.setDirtyCanvas(true, true);
            });
        }

        const onNodeCreated = nodeType.prototype.onNodeCreated;
        nodeType.prototype.onNodeCreated = function () {
            onNodeCreated?.apply(this, arguments);

            // Hide the integer trigger widget that pairs with the reset button.
            hideWidget(this.widgets?.find((w) => w.name === TRIGGER));

            addResetButton(this);
            const display = ensureDisplayWidget(this);
            if (display) this.setSize?.(this.computeSize());
        };

        // Workflow load path: widgets exist already, so re-apply hiding/button on configure.
        const onConfigure = nodeType.prototype.onConfigure;
        nodeType.prototype.onConfigure = function (info) {
            onConfigure?.apply(this, arguments);
            hideWidget(this.widgets?.find((w) => w.name === TRIGGER));
            addResetButton(this);
            ensureDisplayWidget(this);
        };

        const onExecuted = nodeType.prototype.onExecuted;
        nodeType.prototype.onExecuted = function (message) {
            onExecuted?.apply(this, arguments);

            const text = message?.text?.[0];
            if (text === undefined) return;

            const widget = ensureDisplayWidget(this);
            if (!widget) return;

            const value = String(text);
            widget.value = value;
            if (widget.inputEl) widget.inputEl.value = value;
            app.graph.setDirtyCanvas(true, true);
        };
    },
});
