import { app } from "../../scripts/app.js";
import { ComfyWidgets } from "../../scripts/widgets.js";

// Display the current "index" value emitted by the HoldCounter Python node inside the node body,
// similar to how the built-in ShowText node works.
app.registerExtension({
    name: "HoldCounter.Display",

    async beforeRegisterNodeDef(nodeType, nodeData, _app) {
        if (nodeData.name !== "HoldCounter") return;

        const WIDGET_NAME = "current_index";

        function styleReadOnly(widget) {
            const el = widget?.inputEl;
            if (!el) return;
            el.readOnly = true;
            el.style.opacity = "0.75";
        }

        function ensureWidget(node) {
            let widget = node.widgets?.find((w) => w.name === WIDGET_NAME);
            if (widget) return widget;

            const created = ComfyWidgets["STRING"](
                node,
                WIDGET_NAME,
                ["STRING", { multiline: false }],
                app,
            );
            widget = created?.widget ?? node.widgets?.find((w) => w.name === WIDGET_NAME);
            if (!widget) return null;

            widget.value = "";
            widget.serializeValue = () => "";
            // The DOM element may not exist yet on the current frontend; style it now if we can,
            // and again on the next frame as a safety net.
            styleReadOnly(widget);
            requestAnimationFrame(() => styleReadOnly(widget));
            return widget;
        }

        // Create the read-only display widget up-front, when the node is added to the graph, so it
        // already exists and is laid out before the first execution finishes.
        const onNodeCreated = nodeType.prototype.onNodeCreated;
        nodeType.prototype.onNodeCreated = function () {
            onNodeCreated?.apply(this, arguments);
            const widget = ensureWidget(this);
            if (widget) this.setSize?.(this.computeSize());
        };

        const onExecuted = nodeType.prototype.onExecuted;
        nodeType.prototype.onExecuted = function (message) {
            onExecuted?.apply(this, arguments);

            const text = message?.text?.[0];
            if (text === undefined) return;

            const widget = ensureWidget(this);
            if (!widget) return;

            const value = String(text);
            widget.value = value;
            if (widget.inputEl) widget.inputEl.value = value;
            app.graph.setDirtyCanvas(true, true);
        };
    },
});
