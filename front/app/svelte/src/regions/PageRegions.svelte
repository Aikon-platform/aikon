<script>
    import { regionsStore } from "./regionsStore.js";
    const { pageRegions, fetchPages } = regionsStore;
    import Pagination from "../Pagination.svelte";
    import Table from "../Table.svelte";
    import ExtractionButtons from "./ExtractionButtons.svelte";
    import { appLang } from "../constants";
    import { manifestToMirador, refToIIIF } from "../utils.svelte.js";
    import Row from "../Row.svelte";
    import Regions from "./Regions.svelte";

    let { witnessStore } = $props();
    const { selectedManifest, imgPrefix, nbOfPages, leadingZeros } = witnessStore;

    const zeros = (n, l) => n.toString().padStart(l, "0");
    const toImgName = (canvasNb) => `${$imgPrefix}_${zeros(canvasNb, $leadingZeros)}`;
</script>

<Pagination store={regionsStore} nbOfItems={$nbOfPages}/>

<Table>
    {#await $fetchPages}
        <tr class="faded is-center">
            <td>{appLang === "en" ? "Retrieving paginated regions..." : "Récupération des pages..."}</td>
        </tr>
    {:then _}
        {#if Object.values($pageRegions).length > 0}
            {#each Object.entries($pageRegions) as [canvasNb, items]}
                <Row>
                    {#snippet rowHeader()}
                        <img src="{refToIIIF(toImgName(canvasNb), 'full', '250,')}" alt="Canvas {canvasNb}" class="mb-3 card">
                        <div class="is-center mb-1">
                            <a class="tag px-2 py-1 is-rounded is-hoverable" href="{manifestToMirador($selectedManifest, canvasNb-1)}" target="_blank">
                                <i class="fa-solid fa-pen-to-square"></i>
                                Page {canvasNb}
                            </a>
                        </div>
                    {/snippet}
                    {#snippet rowBody()}
                        <Regions items={Object.values(items)}/>
                    {/snippet}
                </Row>
            {/each}
        {:else}
            <tr>
                <ExtractionButtons/>
            </tr>
        {/if}
    {:catch error}
        <tr class="faded is-center">
            <td>{appLang === "en"
                ? `Error when retrieving paginated regions: ${error}`
                : `Erreur de récupération des pages : ${error}`
            }</td>
        </tr>
    {/await}
</Table>

<Pagination store={regionsStore} nbOfItems={$nbOfPages}/>
