<script>
    import { createEventDispatcher } from "svelte";
    import { derived, writable } from "svelte/store";
    import { i18n } from "../../utils.js";
    import RightClick from "../../ui/RightClick.svelte";

    export let stemmaStore;
    export let documents;
    export let visiblePairs;
    export let documentNodes;
    export let mode = "image";
    export let isInStemma = false;

    const { nodeTitles, areAllInStemma, docsInStemma } = stemmaStore;
    const areInStemma = (matchedDocs) => isInStemma && $docsInStemma && areAllInStemma([$baseDocId, ...matchedDocs]);

    const dispatch = createEventDispatcher();

    const LINE_WIDTH = 5;
    const AXIS_HEIGHT = 20;
    const CLUSTER_COLORS = [
        "#9f0048",
        "#d10a0a",
        "#ff6a00",
        "#ff9100",
        "#fdd21e",
        "#bacd12",
        "#8fcd12",
        "#12cd6f",
        "#12cdb1",
        "#1285cd",
        "#1253cd",
        "#2512cd",
        "#5d12cd"
    ];
    let clusterMode = false;
    let clusterOrder = "documents";

    const baseDocId = writable(null);
    const selectedIndex = writable(null);
    let selectedClusterSig = null;

    function clusterSignature(matchedDocs) {
        return matchedDocs.size ? [...matchedDocs].sort((a, b) => a - b).join("-") : "∅";
    }

    function buildClusters(items, baseId, docNodes, titles, order) {
        const clusterMap = new Map();

        for (const item of items) {
            const sig = clusterSignature(item.matchedDocs);
            if (!clusterMap.has(sig)) {
                clusterMap.set(sig, { docIds: new Set(item.matchedDocs), count: 0 });
            }
            clusterMap.get(sig).count++;
        }

        const baseColor = "#dfdfdf";
        const sorted = [...clusterMap.values()].sort((a, b) =>
            order === "matches"
                ? b.count - a.count || b.docIds.size - a.docIds.size
                : b.docIds.size - a.docIds.size || b.count - a.count
        );
        let colorIdx = 0;
        sorted.forEach(cl => {
            if (!cl.docIds.size) {
                cl.color = baseColor;
                cl.opacity = 0.5;
            } else {
                cl.color = colorIdx < CLUSTER_COLORS.length ? CLUSTER_COLORS[colorIdx++] : "#6c6c6c";
                cl.opacity = 1;
            }
        });

        const sigToCluster = new Map();
        for (const [sig, cl] of clusterMap) sigToCluster.set(sig, cl);

        const itemColors = items.map(item => {
            const cl = sigToCluster.get(clusterSignature(item.matchedDocs));
            return { color: cl.color };
        });

        const baseName = titles[baseId] || docNodes.get(baseId)?.title || `Doc ${baseId}`;
        const legend = sorted.map(cl => {
            const names = [baseName, ...[...cl.docIds].map(id => titles[id] || docNodes.get(id)?.title || `Doc ${id}`)];
            return { color: cl.color, names, count: cl.count, docIds: cl.docIds };
        });

        return { itemColors, legend };
    }

    $: clusterData = clusterMode && $items.length ? buildClusters($items, $baseDocId, $documentNodes, $nodeTitles, clusterOrder) : null;
    $: if (!clusterMode) selectedClusterSig = null;
    $: clusterSelectedIndices = (clusterMode && selectedClusterSig)
        ? new Set($items.map((it, i) => clusterSignature(it.matchedDocs) === selectedClusterSig ? i : -1).filter(i => i >= 0))
        : null;

    $: if (documents.length && !documents.find(n => n.id === $baseDocId && n.images?.length)) {
        const validDoc = documents.find(n => n.images?.length);
        baseDocId.set(validDoc?.id || null);
        selectedIndex.set(null);
    }

    $: if (mode) {
        selectedIndex.set(null);
        selectedClusterSig = null;
    }

    const t = {
        base: { en: "Pick a base document", fr: "Sélectionner un document de base" },
        similarity: { en: "similarities", fr: "similarités" },
        noDoc: { en: "No base document selected", fr: "Aucun document de base sélectionné" },
        clusters: { en: "Document clusters", fr: "Groupes de documents"},
        clickToShow: { en: "Click to show all cluster matches", fr: "Cliquer pour afficher les correspondances du cluster" },
        addEdges: { en: "Add stemma edges", fr: "Ajouter des liens au stemma" },
        orderBy: { en: "Order by", fr: "Trier par" },
        orderByDocs: { en: "number of documents", fr: "nombre de documents" },
        orderByMatches: { en: "number of matches", fr: "nombre de correspondances" },
    };

    const documentsStore = writable([]);
    $: documentsStore.set(documents);
    const friezeData = derived(
        [documentsStore, visiblePairs, documentNodes, baseDocId],
        ([$nodes, $pairs, $docs, $baseId]) => {
            if (!$nodes.length || !$docs.size || !$baseId) return null;

            const baseDoc = $docs.get($baseId);
            if (!baseDoc?.images?.length) return null;

            const images = baseDoc.images;
            const otherDocIds = new Set($nodes.filter(n => n.id !== $baseId).map(n => n.id));

            const imageMatches = new Map();
            for (const img of images) imageMatches.set(img.id, new Set());

            if (otherDocIds.size) {
                for (const p of $pairs) {
                    const id1InBase = p.digit_1 === baseDoc.id;
                    const id2InBase = p.digit_2 === baseDoc.id;
                    if (!id1InBase && !id2InBase) continue;

                    const baseImgId = id1InBase ? p.id_1 : p.id_2;
                    const otherRegionId = id1InBase ? p.digit_2 : p.digit_1;
                    if (!otherDocIds.has(otherRegionId)) continue;

                    imageMatches.get(baseImgId)?.add(otherRegionId);
                }
            }

            const pageData = new Map();
            let maxPage = 0;

            for (const img of images) {
                const page = img.canvas;
                if (page > maxPage) maxPage = page;

                if (!pageData.has(page)) {
                    pageData.set(page, { images: [], matchedDocs: new Set() });
                }
                const pd = pageData.get(page);
                pd.images.push(img);
                for (const docId of imageMatches.get(img.id) || []) {
                    pd.matchedDocs.add(docId);
                }
            }

            const imageItems = images.map(img => ({
                id: img.id,
                page: img.canvas,
                matchedDocs: imageMatches.get(img.id) || new Set()
            }));
            imageItems.forEach(item => item.matchCount = item.matchedDocs.size);

            const pageItems = [];
            for (let p = 1; p <= maxPage; p++) {
                const pd = pageData.get(p);
                pageItems.push({
                    page: p,
                    imageCount: pd?.images.length || 0,
                    matchedDocs: pd?.matchedDocs || new Set(),
                    matchCount: pd?.matchedDocs.size || 0,
                    images: pd?.images || []
                });
            }

            const pageBoundaries = [];
            let currentPage = null, startIdx = 0;
            images.forEach((img, i) => {
                if (img.canvas !== currentPage) {
                    if (currentPage !== null) pageBoundaries.push({ page: currentPage, startIdx, endIdx: i });
                    currentPage = img.canvas;
                    startIdx = i;
                }
            });
            if (currentPage !== null) pageBoundaries.push({ page: currentPage, startIdx, endIdx: images.length });

            const maxImageMatches = Math.max(1, ...imageItems.map(i => i.matchCount));
            const maxPageMatches = Math.max(1, ...pageItems.map(p => p.matchCount));
            const maxImagesPerPage = Math.max(1, ...pageItems.map(p => p.imageCount));

            return {
                imageItems,
                pageItems,
                pageBoundaries,
                maxImageMatches,
                maxPageMatches,
                maxImagesPerPage,
                totalImages: images.length,
                totalPages: maxPage
            };
        }
    );

    const modeStore = writable(mode);
    $: modeStore.set(mode);

    const items = derived([friezeData, modeStore], ([$fd, $m]) =>
        $fd ? ($m === "image" ? $fd.imageItems : $fd.pageItems) : []
    );
    const maxVal = derived([friezeData, modeStore], ([$fd, $m]) =>
        $fd ? ($m === "image" ? $fd.maxImageMatches : $fd.maxPageMatches) : 1
    );

    let hoveredDocs = new Set();

    function handleClick(index) {
        selectedClusterSig = null;
        selectedIndex.set(index);
        if (mode === "image") {
            const img = $friezeData.imageItems[index];
            dispatch("imageselect", { imageId: img.id, baseDocId: $baseDocId });
        } else {
            const pageItem = $friezeData.pageItems[index];
            const firstImg = pageItem.images[0];
            dispatch("imageselect", {
                imageId: firstImg?.id || null,
                baseDocId: $baseDocId,
                page: pageItem.page,
                images: pageItem.images
            });
        }
    }

    function handleClusterClick(cluster) {
        const sig = clusterSignature(cluster.docIds);
        selectedClusterSig = selectedClusterSig === sig ? null : sig;
        selectedIndex.set(null);
        if (selectedClusterSig) {
            const imageIds = new Set(
                $items
                    .filter(it => clusterSignature(it.matchedDocs) === sig)
                    .map(it => it.id ?? it.images?.[0]?.id)
                    .filter(Boolean)
            );
            dispatch("clusterselect", { baseDocId: $baseDocId, docIds: cluster.docIds, imageIds });
        } else {
            dispatch("clusterselect", null);
        }
    }

    function handleClusterHover(cluster) {
        hoveredDocs = new Set([$baseDocId, ...cluster.docIds]);
    }

    function handleMouseEnter(item) {
        hoveredDocs = !item.matchedDocs.size
            ? new Set([$baseDocId])
            : item.matchedDocs;
    }

    function handleMouseLeave() {
        hoveredDocs = new Set();
    }

    function getAxisTicks(maxPage) {
        const ticks = [];
        for (let p = 50; p <= maxPage; p += 50) ticks.push(p);
        if (ticks.length === 0 || ticks[ticks.length - 1] !== maxPage) ticks.push(maxPage);
        return ticks;
    }

    $: axisTicks = $friezeData ? getAxisTicks($friezeData.totalPages) : [];

    $: isInStemma = !!stemmaStore?.addEdge;

    let menuOpen = false, menuX = 0, menuY = 0, menuItems = [];

    function docDate(d) {
        return d.min_date ?? d.max_date ?? null;
    }

    function orderDocs(docIds) {
        const docs = docIds.map(id => $documentNodes.get(id)).filter(Boolean);
        if (docs.every(d => docDate(d) != null)) return [...docs].sort((a, b) => docDate(a) - docDate(b));
        const order = new Map(documents.map((d, i) => [d.id, i]));
        return [...docs].sort((a, b) => (order.get(a.id) ?? 0) - (order.get(b.id) ?? 0));
    }

    function openEdgesMenu(event, docIds) {
        if (!isInStemma || docIds.length < 2) return;
        event.preventDefault();
        const ordered = orderDocs(docIds);
        menuItems = [{
            label: i18n("addEdges", t),
            icon: "arrow-right",
            action: () => {
                for (let i = 0; i < ordered.length - 1; i++) {
                    const src = ordered[i], tgt = ordered[i + 1];
                    stemmaStore.addEdge(src.id, tgt.id, src, tgt);
                }
            }
        }];
        menuX = event.clientX;
        menuY = event.clientY;
        menuOpen = true;
    }
</script>

<div class="frieze-container">
    {#if $friezeData}
        {@const baseDoc = $documentNodes.get($baseDocId)}
        <h4 class="title is-6 mb-3">
            {baseDoc.title} {i18n("similarity", t)}
        </h4>
        {@const friezeWidth = $items.length * LINE_WIDTH}
        <div id="spatial-frieze" class="frieze-wrapper">
            <div class="frieze" style="--line-width: {LINE_WIDTH}px;">
                {#each $items as item, idx}
                    <button class="frieze-line"
                        class:is-selected={idx === $selectedIndex}
                        class:is-cluster-selected={clusterSelectedIndices?.has(idx)}
                        class:is-in-stemma={!clusterMode && areInStemma(item.matchedDocs)}
                        style="{clusterData
                            ? `background:${clusterData.itemColors[idx]?.color || '#4a4a4a'};`
                            : `--opacity: ${item.matchCount / $maxVal}`}"
                        title="{mode === 'image' ? `Page ${item.page}, ` : `Page ${item.page}, `}{item.matchCount} match(es)"
                        on:click={() => handleClick(idx)}
                        on:contextmenu={(e) => openEdgesMenu(e, [$baseDocId, ...item.matchedDocs])}
                        on:mouseenter={() => handleMouseEnter(item)}
                        on:mouseleave={handleMouseLeave}
                    />
                {/each}
            </div>

            {#if mode === "page"}
                <div class="heatmap" style="--line-width: {LINE_WIDTH}px;">
                    {#each $friezeData.pageItems as item}
                        <div
                            class="heatmap-cell"
                            style="--opacity: {item.imageCount / $friezeData.maxImagesPerPage}; background-color: {baseDoc?.color}"
                            title="Page {item.page}: {item.imageCount} image(s)"
                        />
                    {/each}
                </div>
            {/if}

            <svg class="axis" height={AXIS_HEIGHT} style="width: {friezeWidth}px;">
                <line x1="0" y1="0" x2={friezeWidth} y2="0" stroke="var(--bulma-border)" />
                {#if mode === "page"}
                    {#each axisTicks as tick}
                        {@const x = (tick - 0.5) * LINE_WIDTH}
                        <line x1={x} y1="0" x2={x} y2="5" stroke="var(--bulma-border)" />
                        <text x={x} y="16" text-anchor="middle" class="axis-label">{tick}</text>
                    {/each}
                {:else}
                    {#each $friezeData.pageBoundaries as boundary}
                        {@const x = boundary.startIdx * LINE_WIDTH}
                        {#if boundary.page % 50 === 0 || boundary.page === $friezeData.totalPages}
                            <line x1={x} y1="0" x2={x} y2="5" stroke="var(--bulma-border)" />
                            <text x={x} y="16" text-anchor="middle" class="axis-label">{boundary.page}</text>
                        {/if}
                    {/each}
                {/if}
            </svg>
        </div>

        <div class="frieze-legend is-size-7 has-text-grey mt-2">
            <span>{$friezeData.totalImages} images</span>
            <span class="mx-2">·</span>
            <span>{$friezeData.totalPages} pages</span>
            <span class="mx-2">·</span>
            <span>Max {$maxVal} matches</span>
        </div>
    {:else}
        <p class="has-text-grey is-size-7">{i18n("noDoc")}</p>
    {/if}

    {#if documents.length}
        <div class="is-flex is-align-items-center" style="gap: 0.75rem;">
            <h4 class="title is-6 my-2">{i18n("base", t)}</h4>
            <label class="checkbox is-size-7 is-flex is-align-items-center">
                <input type="checkbox" bind:checked={clusterMode} class="mr-1"/>
                {i18n("clusters", t)}
            </label>
        </div>
        <div class="doc-selector">
            {#each documents as node (node.id)}
                {@const title = $nodeTitles[node.id] || node.title}
                <button class="tag is-small doc-item" title={title}
                    class:is-base={node.id === $baseDocId}
                    class:is-in-stemma={areInStemma([node.id])}
                    class:is-inactive={hoveredDocs.size > 0 && !hoveredDocs.has(node.id) && node.id !== $baseDocId}
                    style="background-color: {node.color}; color: #222;"
                    on:click={() => { baseDocId.set(node.id); selectedIndex.set(null); }}>
                    {title.length > 15 ? title.slice(0, 13) + "…" : title}
                </button>
            {/each}
        </div>
        {#if clusterData}
            <div class="field is-flex is-align-items-center mt-3" style="gap: 0.5rem;">
                <label class="is-size-7" for="cluster-order">{i18n("orderBy", t)}</label>
                <div class="select is-small">
                    <select id="cluster-order" bind:value={clusterOrder}>
                        <option value="documents">{i18n("orderByDocs", t)}</option>
                        <option value="matches">{i18n("orderByMatches", t)}</option>
                    </select>
                </div>
            </div>
            <div class="cluster-container mt-3">
                {#each clusterData.legend as cl}
                    {@const docLen = cl.names.length}
                    <div class="is-size-7">
                        <span style="color:{cl.color};">●</span>
                        <b>{docLen} document{docLen > 1 ? 's' : ''}</b>
                        <span class="tag is-light is-small is-rounded is-clickable" title={i18n("clickToShow", t)}
                            class:is-active={selectedClusterSig === clusterSignature(cl.docIds)}
                            class:is-in-stemma={areInStemma(cl.docIds)}
                            on:click={() => handleClusterClick(cl)}
                            on:contextmenu={(e) => openEdgesMenu(e, [$baseDocId, ...cl.docIds])}
                            on:mouseenter={() => handleClusterHover(cl)}
                            on:mouseleave={handleMouseLeave} on:keydown={null}>
                            {cl.count}
                        </span>
                        {#each cl.names as name}
                            <br/><span class="pl-3">{name}</span>
                        {/each}
                    </div>
                {/each}
            </div>
        {/if}
    {/if}
</div>

<RightClick bind:open={menuOpen} x={menuX} y={menuY} items={menuItems}/>

<style>
    .frieze-container {
        --stemma-link-color: hsl(19 95.1% 52%);
        --stemma-cluster-color: var(--bulma-link);
        padding: 0.5rem;
    }
    .cluster-container {
        display: flex;
        flex-direction: column;
        gap: 0.35rem;
        max-height: 75vh;
        overflow-y: auto;
    }
    .frieze-wrapper {
        overflow-x: auto;
        padding-top: 5px;
    }
    .frieze {
        display: flex;
        height: 60px;
        background: var(--bulma-scheme-main-bis);
        border-radius: 4px 4px 0 0;
    }
    .frieze-line {
        width: var(--line-width);
        flex-shrink: 0;
        border: none;
        padding: 0;
        cursor: pointer;
        background: color-mix(in srgb, var(--bulma-link) calc(var(--opacity) * 100%), transparent);
        transition: margin-top 0.1s, margin-bottom 0.1s, height 0.1s;
    }
    .frieze-line.is-selected {
        margin-top: -5px;
        height: calc(100% + 5px);
    }
    .frieze-line.is-in-stemma {
        background: color-mix(in srgb, var(--stemma-link-color) calc(var(--opacity) * 100%), transparent);
    }
    .tag.is-clickable.is-in-stemma {
        outline: 1px solid var(--stemma-cluster-color);
        outline-offset: -1px;
    }
    .tag.doc-item {
        cursor: pointer;
        transition: border-color 0.3s, opacity 0.3s, filter 0.3s;
        border-color: var(--bulma-link);
    }
    .tag.doc-item.is-in-stemma {
        border-left: 4px solid var(--stemma-cluster-color);
    }
    .tag.doc-item.is-base {
        border: 2px solid var(--bulma-link);
    }
    .tag.doc-item.is-base.is-in-stemma {
        border-color: var(--stemma-cluster-color);
        border-left: 4px solid var(--stemma-cluster-color);
    }
    .tag.doc-item.is-inactive {
        opacity: 0.3;
        filter: grayscale(0.8);
    }
    .heatmap {
        display: flex;
        height: 8px;
    }
    .heatmap-cell {
        width: var(--line-width);
        flex-shrink: 0;
        opacity: var(--opacity);
    }
    .axis {
        display: block;
    }
    .axis-label {
        font-size: 9px;
        fill: var(--bulma-text-weak);
    }
    .frieze-legend {
        display: flex;
        justify-content: center;
    }
    .doc-selector {
        display: flex;
        flex-wrap: wrap;
        gap: 0.5rem;
    }
    .frieze-line.is-cluster-selected {
        margin-bottom: -5px;
        height: calc(100% + 5px);
    }
    .frieze-line.is-selected.is-cluster-selected {
        margin-top: -5px;
        height: calc(100% + 10px);
    }
    .tag.is-clickable.is-active {
        background-color: var(--selected-text);
        color: var(--selected)
    }
</style>
