<script>
    import Item from "./Item.svelte";
	import Modal from "../Modal.svelte";
    import {appLang, appName} from "../constants.js";
    import { showMessage } from "../utils";

    export let item;
    export let recordsStore;

    import { recordsSelection } from "../selection/selectionStore.js";
    const { isSetSelected } = recordsSelection;
    $: setSelected = $isSetSelected(item);

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
</script>

<Item {item} {recordsStore}>
    <div slot="buttons">
        <button class="button" class:is-inverted={setSelected} on:click={() => recordsSelection.toggleSet(item)}>
            {#if appLang === "en"}
                {setSelected ? "Unload from" : "Load to"} selection
            {:else}
                {setSelected ? "Retirer de la" : "Charger dans la"} sélection
            {/if}
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 384 512">
                {#if setSelected}
                    <path d="M0 48V487.7C0 501.1 10.9 512 24.3 512c5 0 9.9-1.5 14-4.4L192 400 345.7 507.6c4.1 2.9 9 4.4 14 4.4c13.4 0 24.3-10.9 24.3-24.3V48c0-26.5-21.5-48-48-48H48C21.5 0 0 21.5 0 48z"/>
                {:else}
                    <path d="M0 48C0 21.5 21.5 0 48 0l0 48V441.4l130.1-92.9c8.3-6 19.6-6 27.9 0L336 441.4V48H48V0H336c26.5 0 48 21.5 48 48V488c0 9-5 17.2-13 21.3s-17.6 3.4-24.9-1.8L192 397.5 37.9 507.5c-7.3 5.2-16.9 5.9-24.9 1.8S0 497 0 488V48z"/>
                {/if}
            </svg>
        </button>
        <div class="dropdown is-hoverable">
            <div class="dropdown-trigger">
                <button class="button is-link" class:is-inverted={setSelected}>
                    <i class="fa-solid fa-file-export"/>
                    {appLang === "en" ? "Export" : "Exporter"}
                </button>
            </div>
            <div class="dropdown-menu">
                <div class="dropdown-content">
                    <a class="dropdown-item" target="_blank" href="/{appName}/document-set/{item.id}/json">
                        {appLang === "en" ? "JSON API" : "API JSON"}
                    </a>
                    <a class="dropdown-item" target="_blank" href="/{appName}/document-set/{item.id}/zip">ZIP</a>
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

        <div class="grid">
            {#each Object.entries(item.selection?.selected || {}) as [modelName, selectedRecords]}
                {#if modelName !== "User"}
                    {#each Object.entries(selectedRecords) as [id, meta]}
                        <div>
                            <span class="tag is-rounded is-accent">{modelName} #{id}</span>
                            {meta.title}
                        </div>
                    {/each}
                {/if}
            {/each}
        </div>

    </div>
</Item>
