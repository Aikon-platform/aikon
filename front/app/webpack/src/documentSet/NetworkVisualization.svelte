<script>
    import * as d3 from 'd3';
    import { createDocumentSetStore } from './documentSetStore.js';
    import {onMount} from 'svelte';

    const store = createDocumentSetStore();
    const { imageNetwork, error } = store;

    let mounted = false;
    onMount(async () => {
        await store.fetchPairs;
        mounted = true;
    });

    export let data = null;
    export let corpus = null;
    export let type = "regions";
    const BASE_URL = "https://iscd.huma-num.fr/";

    let container;
    let networkDiv;

    function renderVisualization() {
        if (type === "regions") {
            // $: if ($imageNetwork && networkDiv) {}
            createImageNetwork(networkDiv, $imageNetwork);
        } else if (type === "documents") {
            createDocumentNetwork(container, data, corpus);
        }
    }

    function createSimulationHandlers(simulation, link, node, label) {
        simulation.on("tick", () => {
            link
                .attr("x1", d => d.source.x)
                .attr("y1", d => d.source.y)
                .attr("x2", d => d.target.x)
                .attr("y2", d => d.target.y);

            node
                .attr("cx", d => d.x)
                .attr("cy", d => d.y);

            label
                .attr("x", d => d.x)
                .attr("y", d => d.y);
        });

        function dragstarted(event) {
            if (!event.active) simulation.alphaTarget(0.3).restart();
            event.subject.fx = event.subject.x;
            event.subject.fy = event.subject.y;
        }

        function dragged(event) {
            event.subject.fx = event.x;
            event.subject.fy = event.y;
        }

        function dragended(event) {
            if (!event.active) simulation.alphaTarget(0);
            event.subject.fx = null;
            event.subject.fy = null;
        }

        return {dragstarted, dragged, dragended};
    }

    function generateDistinctColor(str) {
        let hash = 0;
        for (let i = 0; i < str.length; i++) {
            hash = str.charCodeAt(i) + ((hash << 5) - hash);
            hash = hash & hash;
        }

        const goldenRatio = 0.618033988749895;
        const hue = ((hash * goldenRatio) % 1) * 360;
        const saturation = 65 + (hash % 20);
        const lightness = 80 + (hash % 10);

        return `hsl(${Math.floor(hue)}, ${saturation}%, ${lightness}%)`;
    }

    function buildAlignedImageMatrix(selectionOrder, regionImages, data) {
        const regions = [...selectionOrder];

        const getRegionImagesMap = (regionId) => {
            const map = new Map();
            regionImages.get(regionId).forEach(imgData => {
                map.set(imgData.img, {page: imgData.page, img: imgData.img});
            });
            return map;
        };

        const regionImagesMap = new Map(regions.map(r => [r, getRegionImagesMap(r)]));
        const rows = [];
        const globalProcessed = new Map(regions.map(r => [r, new Set()]));

        const findConnectedImages = (regionId, img, targetRegion) => {
            const connected = [];
            data.forEach(pair => {
                const [r1, r2] = [pair.regions_id_1, pair.regions_id_2];
                const [i1, i2] = [pair.img_1, pair.img_2];

                if ((r1 === regionId && i1 === img && r2 === targetRegion) ||
                    (r2 === regionId && i2 === img && r1 === targetRegion)) {
                    const targetImg = r1 === targetRegion ? i1 : i2;
                    if (regionImagesMap.get(targetRegion).has(targetImg)) {
                        connected.push(regionImagesMap.get(targetRegion).get(targetImg));
                    }
                }
            });
            return connected;
        };

        const buildRowFromSeed = (seedRegion, seedImg) => {
            const visited = new Map([[seedRegion, seedImg.img]]);
            const queue = [{region: seedRegion, img: seedImg, path: {[seedRegion]: seedImg}}];
            const completedPaths = [];

            while (queue.length > 0) {
                const {region, img, path} = queue.shift();
                const currentIndex = regions.indexOf(region);

                if (currentIndex === regions.length - 1) {
                    completedPaths.push(path);
                    continue;
                }

                const nextRegion = regions[currentIndex + 1];
                const connected = findConnectedImages(region, img.img, nextRegion);

                if (connected.length > 0) {
                    connected.forEach(nextImg => {
                        queue.push({
                            region: nextRegion,
                            img: nextImg,
                            path: {...path, [nextRegion]: nextImg}
                        });
                    });
                } else if (Object.keys(path).length > 0) {
                    completedPaths.push(path);
                }
            }

            return completedPaths;
        };

        regions.forEach(regionId => {
            const images = Array.from(regionImagesMap.get(regionId).values())
                .sort((a, b) => a.page - b.page);

            images.forEach(imgData => {
                if (globalProcessed.get(regionId).has(imgData.img)) return;

                const paths = buildRowFromSeed(regionId, imgData);

                if (paths.length > 0) {
                    paths.forEach(path => {
                        Object.entries(path).forEach(([r, img]) => {
                            globalProcessed.get(Number(r)).add(img.img);
                        });
                        rows.push(path);
                    });
                } else {
                    globalProcessed.get(regionId).add(imgData.img);
                    rows.push({[regionId]: imgData});
                }
            });
        });

        return {regions, rows};
    }


    function createDocumentNetwork(div, data, corpus) {
        const width = 954;
        const height = 600;

        const regionConnections = new Map();
        const regionImages = new Map();

        data.forEach(d => {
            const r1 = d.regions_id_1;
            const r2 = d.regions_id_2;

            if (!regionImages.has(r1)) regionImages.set(r1, []);
            if (!regionImages.has(r2)) regionImages.set(r2, []);

            regionImages.get(r1).push({img: d.img_1, page: d.page_1, pair: d});
            regionImages.get(r2).push({img: d.img_2, page: d.page_2, pair: d});

            const key = r1 < r2 ? `${r1}-${r2}` : `${r2}-${r1}`;
            regionConnections.set(key, (regionConnections.get(key) || 0) + 1);
        });

        const nodes = Array.from(regionImages.keys()).map(id => ({id}));
        const links = [];

        regionConnections.forEach((count, key) => {
            const [source, target] = key.split('-').map(Number);
            links.push({source, target, count});
        });

        const regionCount = Object.values(corpus).reduce((count, wit) =>
            count + Object.keys(wit).length, 0
        );
        const colorScale = d3.scaleOrdinal(generateColors(regionCount));
        const linkWidthScale = d3.scaleLinear()
            .domain([1, d3.max(links, d => d.count)])
            .range([1, 10]);

        const linkStrengthScale = d3.scaleLinear()
            .domain([1, d3.max(links, d => d.count)])
            .range([0.3, 1]);

        const linkDistanceScale = d3.scaleLinear()
            .domain([1, d3.max(links, d => d.count)])
            .range([200, 50]);

        const simulation = d3.forceSimulation(nodes)
            .force("link", d3.forceLink(links).id(d => d.id)
                .distance(d => linkDistanceScale(d.count))
                .strength(d => linkStrengthScale(d.count))
            )
            .force("charge", d3.forceManyBody().strength(-800))
            .force("center", d3.forceCenter(width / 2, height / 2))
            .force("collision", d3.forceCollide().radius(40));

        const container = d3.select(div);

        const clickMode = "<span class='icon px-4'><i class='fas fa-hand-pointer'></i></span> Switch to click mode";
        const selectMode = "<span class='icon px-4'><i class='fas fa-crop-alt'></i></span> Switch to selection mode";

        const toggleButton = container.append("button")
            .attr("class", "toggle-button button is-small is-link")
            .html(selectMode);

        const svg = container.append("svg")
            .attr("class", "network-svg")
            .attr("width", width)
            .attr("height", height)
            .attr("viewBox", [0, 0, width, height]);

        const g = svg.append("g");

        const selectionManager = createSelectionManager({
            svg,
            g,
            nodes: nodes,
            onSelectionChange: (selected, order) => {
                node.classed("selected", d => selected.has(d.id));
                updateSelection(order);
            }
        });

        toggleButton.on("click", function () {
            const active = selectionManager.toggleSelectionMode();
            d3.select(this)
                .html(active ? clickMode : selectMode)
                .classed("active", active);
        });

        svg.call(d3.zoom()
            .scaleExtent([0.1, 10])
            .filter(() => !selectionManager.isSelectionMode())
            .on("zoom", ({transform}) => g.attr("transform", transform)));

        const link = g.append("g")
            .selectAll("line")
            .data(links)
            .join("line")
            .attr("class", "link")
            .attr("stroke-width", d => linkWidthScale(d.count));

        const node = g.append("g")
            .selectAll("circle")
            .data(nodes)
            .join("circle")
            .attr("class", "node")
            .attr("r", 32)
            .attr("fill", d => colorScale(d.id));

        // const label = g.append("g")
        //     .selectAll("text")
        //     .data(nodes)
        //     .join("text")
        //     .text(d => d.id)
        //     .attr("class", "node-label")
        //     .attr("font-size", "12px")
        //     .attr("text-anchor", "middle")
        //     .attr("dy", "0.35em")
        //     .attr("fill", "white")
        //     .attr("pointer-events", "none");

        const selectionDiv = container.append("div")
            .attr("class", "selection-panel");

        selectionDiv.append("h3")
            .attr("class", "title is-5")
            .text("Selected Witnesses");

        const imagesContainer = selectionDiv.append("div");

        function updateSelection(selectionOrder) {
            imagesContainer.selectAll("*").remove();

            if (selectionOrder.length === 0) return;

            const {regions, rows} = buildAlignedImageMatrix(selectionOrder, regionImages, data);

            const imageOccurrences = new Map();
            rows.forEach(rowData => {
                Object.values(rowData).forEach(imgData => {
                    const count = imageOccurrences.get(imgData.img) || 0;
                    imageOccurrences.set(imgData.img, count + 1);
                });
            });

            const imageColorMap = new Map();
            const getImageColor = (imgUrl) => {
                if (imageOccurrences.get(imgUrl) === 1) {
                    return "white";
                }
                if (!imageColorMap.has(imgUrl)) {
                    imageColorMap.set(imgUrl, generateDistinctColor(imgUrl));
                }
                return imageColorMap.get(imgUrl);
            };

            const table = imagesContainer.append("table")
                .attr("class", "table is-bordered is-fullwidth");

            const thead = table.append("thead");
            const headerRow = thead.append("tr");

            regions.forEach(regionId => {
                headerRow.append("th")
                    .attr("class", "has-text-centered has-text-white")
                    .style("background", colorScale(regionId))
                    .text(`Region ${regionId}`);
            });

            const tbody = table.append("tbody");

            rows.forEach(rowData => {
                const row = tbody.append("tr");

                regions.forEach(regionId => {
                    const cell = row.append("td")
                        .attr("class", "has-text-centered")
                        .style("vertical-align", "top")
                        .style("background", rowData[regionId] ? getImageColor(rowData[regionId].img) : "white");

                    if (rowData[regionId]) {
                        const imgUrl = rowData[regionId].img;

                        cell.append("img")
                            .attr("src", imgUrl)
                            .style("width", "200px")
                            .style("height", "auto")
                            .style("display", "block")
                            .style("margin", "0 auto");

                        cell.append("div")
                            .attr("class", "has-text-grey-dark mt-2")
                            .style("font-size", "12px")
                            .text(`Page ${rowData[regionId].page}`);
                    }
                });
            });
        }

        const {dragstarted, dragged, dragended} = createSimulationHandlers(simulation, link, node, label);

        selectionManager.setupNodeClick(node);
        selectionManager.setupDrag(node, {
            start: dragstarted,
            drag: dragged,
            end: dragended
        });
    }

    function createSelectionManager(options) {
        const {
            svg,
            g,
            nodes,
            onSelectionChange,
            getNodePosition = d => ({x: d.x, y: d.y}),
            getNodeId = d => d.id
        } = options;

        const selectedNodes = new Set();
        const selectionOrder = [];
        let selectionMode = false;
        let selectionRect = null;
        let selectionStart = null;

        function toggleSelectionMode() {
            selectionMode = !selectionMode;
            svg.style("cursor", selectionMode ? "crosshair" : "default");
            return selectionMode;
        }

        function toggleNode(nodeId) {
            if (selectedNodes.has(nodeId)) {
                selectedNodes.delete(nodeId);
                const index = selectionOrder.indexOf(nodeId);
                if (index > -1) selectionOrder.splice(index, 1);
            } else {
                selectedNodes.add(nodeId);
                selectionOrder.push(nodeId);
            }
            onSelectionChange(selectedNodes, selectionOrder);
        }

        function clearSelection() {
            selectedNodes.clear();
            selectionOrder.length = 0;
            onSelectionChange(selectedNodes, selectionOrder);
        }

        svg
            .on("mousedown", function (event) {
                if (!selectionMode) return;
                event.preventDefault();

                const [x, y] = d3.pointer(event, g.node());
                selectionStart = {x, y};

                selectionRect = g.append("rect")
                    .attr("class", "selection-rect")
                    .attr("x", x)
                    .attr("y", y)
                    .attr("width", 0)
                    .attr("height", 0);
            })
            .on("mousemove", function (event) {
                if (!selectionMode || !selectionRect) return;

                const [x, y] = d3.pointer(event, g.node());
                const width = x - selectionStart.x;
                const height = y - selectionStart.y;

                selectionRect
                    .attr("x", width < 0 ? x : selectionStart.x)
                    .attr("y", height < 0 ? y : selectionStart.y)
                    .attr("width", Math.abs(width))
                    .attr("height", Math.abs(height));
            })
            .on("mouseup", function (event) {
                if (!selectionMode || !selectionRect) return;

                const [x, y] = d3.pointer(event, g.node());
                const x1 = Math.min(selectionStart.x, x);
                const y1 = Math.min(selectionStart.y, y);
                const x2 = Math.max(selectionStart.x, x);
                const y2 = Math.max(selectionStart.y, y);

                selectedNodes.clear();
                selectionOrder.length = 0;

                const newNodes = [];
                nodes.forEach(d => {
                    const pos = getNodePosition(d);
                    if (pos.x >= x1 && pos.x <= x2 && pos.y >= y1 && pos.y <= y2) {
                        newNodes.push(getNodeId(d));
                    }
                });

                newNodes.sort((a, b) => a - b);
                newNodes.forEach(id => {
                    selectedNodes.add(id);
                    selectionOrder.push(id);
                });

                onSelectionChange(selectedNodes, selectionOrder);

                selectionRect.remove();
                selectionRect = null;
                selectionStart = null;
            });

        return {
            toggleSelectionMode,
            toggleNode,
            clearSelection,
            isSelectionMode: () => selectionMode,
            getSelectedNodes: () => selectedNodes,
            getSelectionOrder: () => selectionOrder,
            setupNodeClick: (nodeSelection) => {
                nodeSelection.on("click", function (event, d) {
                    event.stopPropagation();
                    toggleNode(getNodeId(d));
                });
            },
            setupDrag: (nodeSelection, dragFunctions) => {
                nodeSelection.call(
                    d3.drag()
                        .filter(() => !selectionMode)
                        .on("start", dragFunctions.start)
                        .on("drag", dragFunctions.drag)
                        .on("end", dragFunctions.end)
                );
            }
        };
    }

    function createLegend(containerId, nodesArray, colorScale) {
        const container = d3.select(`#${containerId}`);
        container.html('');

        const regionIds = [...new Set(nodesArray.map(d => d.regionId))].sort((a, b) => a - b);

        const legend = container.append('div')
            .attr('class', 'box');

        legend.append('h3')
            .attr('class', 'title is-6')
            .text('Region Extractions');

        const list = legend.append('div')
            .attr('class', 'legend-list');

        regionIds.forEach(regionId => {
            const metadata = $regionMetadata.get(regionId);
            if (!metadata) return;

            const item = list.append('div')
                .attr('class', 'legend-item');

            item.append('span')
                .attr('class', 'legend-color')
                .style('background-color', colorScale(regionId));

            item.append('span')
                .attr('class', 'legend-label')
                .html(`<a href="${BASE_URL}vhs/witness/${metadata.witnessId}/regions/${regionId}" target="_blank">${metadata.witTitle}</a>`);
        });
    }

    function generateColors(count) {
        const baseHues = [171, 217, 229, 271, 348, 340, 24, 48, 141, 204];
        const colors = [];
        const saturations = [70, 85, 60];
        const lightnesses = [50, 65, 40];

        for (let i = 0; i < count; i++) {
            const hueIndex = i % baseHues.length;
            const satIndex = Math.floor(i / baseHues.length) % saturations.length;
            const lightIndex = Math.floor(i / (baseHues.length * saturations.length)) % lightnesses.length;

            const hue = baseHues[hueIndex];
            const saturation = saturations[satIndex];
            const lightness = lightnesses[lightIndex];

            colors.push(`hsl(${hue}, ${saturation}%, ${lightness}%)`);
        }

        return colors;
    }

    function createImageNetwork(div, networkData) {
        function updateSelection(selectedData, selectionDiv) {
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

        createNetwork(div, networkData.nodes, networkData.links, updateSelection);
    }
</script>

<div>
    <h2 class="title is-3 has-text-link">
        {type === "regions" ? "Images network" : "Witness network"}
    </h2>

    <div bind:this={container} class="visualization-container">
        {#if !data}
            <progress class="progress is-link" max="100">Loading...</progress>
        {/if}
    </div>
</div>

<style>
    .visualization-container {
        min-height: 600px;
    }
</style>
