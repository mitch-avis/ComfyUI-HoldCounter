import { app } from "../../scripts/app.js";
import { ComfyWidgets } from "../../scripts/widgets.js";

// Display the current "index" value emitted by the HoldCounter Python node
// inside the node body, similar to how the built-in ShowText node works.
app.registerExtension({
    name: "HoldCounter.Display",

    async beforeRegisterNodeDef(nodeType, nodeData, _app) {
        if (nodeData.name !== "HoldCounter") return;

        const onExecuted = nodeType.prototype.onExecuted;
        nodeType.prototype.onExecuted = function (message) {
            onExecuted?.apply(this, arguments);

            const text = message?.text?.[0];
            if (text === undefined) return;

            // Find or create a read-only multiline widget to show the value.
            let widget = this.widgets?.find((w) => w.name === "current_index");
            if (!widget) {
                widget = ComfyWidgets["STRING"](
                    this,
                    "current_index",
                    ["STRING", { multiline: false }],
                    app,
                ).widget;
                widget.inputEl.readOnly = true;
                widget.inputEl.style.opacity = 0.75;
            }
            widget.value = String(text);
            this.setSize?.(this.computeSize());
            app.graph.setDirtyCanvas(true, false);
        };
    },
});
