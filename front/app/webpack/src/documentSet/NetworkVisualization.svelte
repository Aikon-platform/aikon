<script>
    import { onMount, onDestroy } from 'svelte';
    import { createNetwork } from './network.js';

    export let networkData;
    export let metadata;
    export let type = "regions";

    let networkInstance;
    let container;

    $: if (networkData && container) {
        networkInstance = renderVisualization();
    }

    function renderVisualization() {
        if (type === "images") {
            // $: if ($imageNetwork && container) {}
            return createImageNetwork(container, networkData);
        } else if (type === "documents") {
            // $: if ($documentNetwork && container) {}
            // return createDocumentNetwork(container, networkData);
        }
    }

    function createDocumentNetwork(div, networkData) {
        function updateSelection(selectionOrder, selectionDiv) {
            // const imagesContainer = selectionDiv.append("div");
            // imagesContainer.selectAll("*").remove();
            //
            // if (selectionOrder.length === 0) return;
            //
            // const {regions, rows} = buildAlignedImageMatrix(selectionOrder, regionImages, data);
            //
            // const imageOccurrences = new Map();
            // rows.forEach(rowData => {
            //     Object.values(rowData).forEach(imgData => {
            //         const count = imageOccurrences.get(imgData.img) || 0;
            //         imageOccurrences.set(imgData.img, count + 1);
            //     });
            // });
            //
            // const imageColorMap = new Map();
            // const getImageColor = (imgUrl) => {
            //     if (imageOccurrences.get(imgUrl) === 1) {
            //         return "white";
            //     }
            //     if (!imageColorMap.has(imgUrl)) {
            //         imageColorMap.set(imgUrl, generateDistinctColor(imgUrl));
            //     }
            //     return imageColorMap.get(imgUrl);
            // };
            //
            // const table = imagesContainer.append("table")
            //     .attr("class", "table is-bordered is-fullwidth");
            //
            // const thead = table.append("thead");
            // const headerRow = thead.append("tr");
            //
            // regions.forEach(regionId => {
            //     headerRow.append("th")
            //         .attr("class", "has-text-centered has-text-white")
            //         .style("background", colorScale(regionId))
            //         .text(`Region ${regionId}`);
            // });
            //
            // const tbody = table.append("tbody");
            //
            // rows.forEach(rowData => {
            //     const row = tbody.append("tr");
            //
            //     regions.forEach(regionId => {
            //         const cell = row.append("td")
            //             .attr("class", "has-text-centered")
            //             .style("vertical-align", "top")
            //             .style("background", rowData[regionId] ? getImageColor(rowData[regionId].img) : "white");
            //
            //         if (rowData[regionId]) {
            //             const imgUrl = rowData[regionId].img;
            //
            //             cell.append("img")
            //                 .attr("src", imgUrl)
            //                 .style("width", "200px")
            //                 .style("height", "auto")
            //                 .style("display", "block")
            //                 .style("margin", "0 auto");
            //
            //             cell.append("div")
            //                 .attr("class", "has-text-grey-dark mt-2")
            //                 .style("font-size", "12px")
            //                 .text(`Page ${rowData[regionId].page}`);
            //         }
            //     });
            // });
        }
        return createNetwork(div, networkData.nodes, networkData.links, updateSelection);
    }

    function createImageNetwork(div, networkData) {
        function updateSelection(selectedData, selectionDiv) {
            // TODO make update selection interact with store + use svelte component to render selected images
            const imagesContainer = selectionDiv.append("div").attr("class", "images-container");
            const cards = imagesContainer.selectAll(".card")
                .data(selectedData, d => d.id);

            cards.exit().remove();

            const cardsEnter = cards.enter()
                .append("div")
                .attr("class", "card");

            cardsEnter.append("img")
                .attr("src", d => d.id);

            cardsEnter.append("div")
                .attr("class", "card-info")
                .html(d => `<strong>Region:</strong> ${d.regionId}<br><strong>Page:</strong> ${d.page}`);
        }

        return createNetwork(div, networkData.nodes, networkData.links, updateSelection);
    }

    onDestroy(() => {
        networkInstance?.destroy();
    });
</script>

<div>
    <h2 class="title is-3 has-text-link">
        {type === "regions" ? "Images network" : "Witness network"}
    </h2>

    <div bind:this={container} class="visualization-container"></div>
</div>

<style>
    .visualization-container {
        min-height: 600px;
    }
</style>
