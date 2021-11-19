<template>
    <div style="border: solid 1px white; width:100%; height:400px">
    </div>
</template>

<script>
import go from 'gojs'

export default {
    name: "Hdag",
    props: ["modelData", "selectedNode"],
    watch: {
        modelData(val) { this.updateModel(val); },
        selectedNode(newV) {
            const node = this.diagram.findNodeForKey(newV)
            this.diagram.select(node)

        },
    },  // accept model data as a parameter
    mounted() {
        const $ = go.GraphObject.make;
        const self = this;
        const myDiagram =
        $(go.Diagram, this.$el,
            {
            initialContentAlignment: go.Spot.Center,
            layout: $(go.TreeLayout, { angle: 90, arrangement: go.TreeLayout.ArrangementVertical }),
            "undoManager.isEnabled": false,
            isReadOnly: true,
            // Model ChangedEvents get passed up to component users
            "ModelChanged"(e) { self.$emit("model-changed", e); },
            "ChangedSelection"(e) { self.$emit("changed-selection", e); }
            });

        myDiagram.nodeTemplate =
        $(go.Node, "Auto",
            $(go.Shape,
            {
                fill: "white", strokeWidth: 2,
                stroke: "#6699ff",
                portId: "", fromLinkable: true, toLinkable: true, cursor: "pointer"
            },
            new go.Binding("fill", "color"), new go.Binding("stroke", "stroke")),
            $(go.TextBlock,
            { margin: 8, editable: true },
            new go.Binding("text").makeTwoWay())
        );

        myDiagram.linkTemplate =
        $(go.Link,
            { relinkableFrom: true, relinkableTo: true },
            $(go.Shape),
            $(go.Shape, { toArrow: "OpenTriangle" })
        );

        this.diagram = myDiagram;
        this.updateModel(this.modelData);
    },
    methods: {
        model() { return this.diagram.model; },
        updateModel(val) {
        // No GoJS transaction permitted when replacing Diagram.model.
        if (val instanceof go.Model) {
            this.diagram.model = val;
        } else {
            const m = new go.GraphLinksModel()
            if (val) {
            for (const p in val) {
                m[p] = val[p];
            }
            }
            this.diagram.model = m;
        }
        },
        updateDiagramFromData() {
            this.diagram.startTransaction();
            // This is very general but very inefficient.
            // It would be better to modify the diagramData data by calling
            // Model.setDataProperty or Model.addNodeData, et al.
            this.diagram.updateAllRelationshipsFromData();
            this.diagram.updateAllTargetBindings();
            this.diagram.initialContentAlignment = go.Spot.Center;
            this.diagram.commitTransaction("updated");
        }
      }
}
</script>