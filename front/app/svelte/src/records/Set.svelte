<script>
    import Item from "./Item.svelte";
    import {appLang, appName} from "../constants.js";

    export let item;
    export let recordsStore;

    import { recordsSelection, regionsSelection } from "../selection/selectionStore.js";
    import {refToIIIF} from "../utils.js";

    const { isSetSelected: isDocSetSelected } = recordsSelection;
    $: docSetSelected = $isDocSetSelected(item);

    const { isSetSelected: isRegionSetSelected } = regionsSelection;
    $: regionSetSelected = $isRegionSetSelected(item);

    function getColor(status) {
        if (!status) return "is-dark";
        if (status === "CANCELLED") return "is-info";
        if (status === "ERROR") return "is-danger";
        if (status === "IN PROGRESS") return "is-warning";
        if (status === "PENDING") return "is-info";
        if (status === "STARTED") return "is-info";
        if (status === "SUCCESS") return "is-success";
        return "is-dark";
    }

    import {getColNb} from "../utils.js";

    let innerWidth = 0;
    $: colNb = getColNb(innerWidth);

    const setType = {
        documentSet: "document-set",
        regionSet: "region-set",
        clusterSet: "cluster-set",
    };

    $: exportType = setType[item.selection.type];
</script>

<svelte:window bind:innerWidth/>

<Item {item} {recordsStore}>
    <div slot="buttons">
        {#if item.selection.type === "documentSet"}
            <button class="button" class:is-inverted={docSetSelected} on:click={() => recordsSelection.toggleSet(item)}>
                {#if appLang === "en"}
                    {docSetSelected ? "Unload from" : "Load to"} document selection
                {:else}
                    {docSetSelected ? "Retirer de la" : "Charger dans la"} sélection de documents
                {/if}
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 384 512">
                    {#if docSetSelected}
                        <path d="M0 48V487.7C0 501.1 10.9 512 24.3 512c5 0 9.9-1.5 14-4.4L192 400 345.7 507.6c4.1 2.9 9 4.4 14 4.4c13.4 0 24.3-10.9 24.3-24.3V48c0-26.5-21.5-48-48-48H48C21.5 0 0 21.5 0 48z"/>
                    {:else}
                        <path d="M0 48C0 21.5 21.5 0 48 0l0 48V441.4l130.1-92.9c8.3-6 19.6-6 27.9 0L336 441.4V48H48V0H336c26.5 0 48 21.5 48 48V488c0 9-5 17.2-13 21.3s-17.6 3.4-24.9-1.8L192 397.5 37.9 507.5c-7.3 5.2-16.9 5.9-24.9 1.8S0 497 0 488V48z"/>
                    {/if}
                </svg>
            </button>
        {:else if item.selection.type === "regionSet"}
            <button class="button" class:is-inverted={regionSetSelected} on:click={() => regionsSelection.toggleSet(item)}>
                {#if appLang === "en"}
                    {regionSetSelected ? "Unload from" : "Load to"} region selection
                {:else}
                    {regionSetSelected ? "Retirer de la" : "Charger dans la"} sélection de régions
                {/if}
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 384 512">
                    {#if regionSetSelected}
                        <path d="M0 48V487.7C0 501.1 10.9 512 24.3 512c5 0 9.9-1.5 14-4.4L192 400 345.7 507.6c4.1 2.9 9 4.4 14 4.4c13.4 0 24.3-10.9 24.3-24.3V48c0-26.5-21.5-48-48-48H48C21.5 0 0 21.5 0 48z"/>
                    {:else}
                        <path d="M0 48C0 21.5 21.5 0 48 0l0 48V441.4l130.1-92.9c8.3-6 19.6-6 27.9 0L336 441.4V48H48V0H336c26.5 0 48 21.5 48 48V488c0 9-5 17.2-13 21.3s-17.6 3.4-24.9-1.8L192 397.5 37.9 507.5c-7.3 5.2-16.9 5.9-24.9 1.8S0 497 0 488V48z"/>
                    {/if}
                </svg>
            </button>
        {/if}

        <div class="dropdown is-hoverable">
            <div class="dropdown-trigger">
                <button class="button is-link" class:is-inverted={docSetSelected || regionSetSelected}>
                    <i class="fa-solid fa-file-export"/>
                    {appLang === "en" ? "Export" : "Exporter"}
                </button>
            </div>
            <div class="dropdown-menu">
                <div class="dropdown-content">
                    <a class="dropdown-item" target="_blank" href="/{appName}/{exportType}/{item.id}/json">
                        {appLang === "en" ? "JSON API" : "API JSON"}
                    </a>
                    <a class="dropdown-item" target="_blank" href="/{appName}/{exportType}/{item.id}/zip">ZIP</a>
                </div>
            </div>
        </div>
    </div>

    <div slot="body">
        <div class="tags container">
            {#each Object.entries(item.treatments) as [id, meta]}
                <a href="{meta.url}" class="tag is-rounded is-small {getColor(meta.status)}">
                    {meta.task_type} #{id}
                </a>
            {/each}
        </div>

        {#if item.selection.type === "documentSet"}
            <div class="grid">
                {#each Object.entries(item.selection?.selected || {}).filter(([modelName]) => modelName !== "User") as [modelName, selectedRecords]}
                    {#each Object.entries(selectedRecords) as [id, meta]}
                        <div>
                            <span class="tag is-rounded is-accent">{modelName} #{id}</span>
                            {meta.title}
                        </div>
                    {/each}
                {/each}
            </div>
        {:else if item.selection.type === "regionSet"}
            {@const regions = Object.entries(item.selection?.selected || {})
                .filter(([modelName]) => modelName !== "User")
                .flatMap(([, selectedRecords]) => Object.entries(selectedRecords))}
            <div class="fixed-grid has-{colNb * 2}-cols is-center">
                <div class="grid mb-0">
                    {#each regions.slice(0, colNb * 2) as [id, meta]}
                        <figure class="image is-64x64 card">
                            <img class="region-icon" src={refToIIIF(meta.img)} alt="Extracted region"/>
                        </figure>
                    {/each}
                </div>
                {#if regions.length > colNb * 2}
                    <div class="tag">
                        {regions.length - colNb * 2}
                        {#if appLang === "en"}
                            more regions
                        {:else}
                            régions supplémentaires
                        {/if}
                    </div>
                {/if}
            </div>
        {/if}
    </div>
</Item>

<style>
    .region-icon {
        object-fit: contain;
        height: 100%;
    }
</style>
