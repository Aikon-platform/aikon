<script>
    import { getContext, onMount } from "svelte";

    import {showMessage, withLoading} from "../utils.js";
    import { appLang, appName, csrfToken } from "../constants";
    import { activeLayout } from "../ui/tabStore.js";

    const witness = getContext("witness");
    const baseUrl = `${window.location.origin}${window.location.pathname}`;
    const currentRegionId = parseInt(baseUrl.split("regions/")[1].replace("/", ""));

    const regionExtractionTabs = ["viewer", "all", "page"];
    const similarityTabs = ["similarity"];

    const allRegionsUrl = baseUrl.replace(/\/\d+\/?$/, "");
    const similarityName = appLang === "fr" ? "similarités" : "similarity";
    const regionExtractionName = (plural=false) => {
        const extra = plural ? "s" : "";
        return appLang === "fr"
            ? `extraction${extra} de région${extra}`
            : `region extraction${extra}`
    }

    // to persist the current tab when selecting/unselecting a Regions,
    // we can't listen to changes on window.location.search.
    // instead, we need to listen to `activeLayout`
    // that emits an update with the new tab value every time it is updated.
    let searchParamsString = window.location.search;
    activeLayout.subscribe((newTab) => {
        const searchParams = new URLSearchParams(window.location.search);
        searchParams.set("tab", newTab);
        searchParamsString = searchParams.toString();
    });

    /**
     * function to delete a RegionExtraction or a similarity between
     * two RegionExtractions, depending on the tab we are on.
     * @type {(target:"similarity"|"regions") => Promise}
     */
    async function deleteAction (target) {
        const allowedTargets = ["similarity", "regions"];
        if (!allowedTargets.includes(target)) {
            throw new Error(`deleteAction: 'target' must be one of ${allowedTargets}, got ${target}`);
        }

        const targetName = target==="regions"
            ? regionExtractionName(true)
            : similarityName;
        const confirmed = await showMessage(
            appLang === "en"
                ? `Are you sure you want to delete all ${targetName} of this witness?`
                : `Voulez-vous vraiment supprimer les ${targetName} effectuées sur ce document ?`,
            appLang === "en" ? "Confirm deletion" : "Confirmer la suppression",
            true
        )
        if (!confirmed) {
            return;
        }
        if (typeof currentRegionId !== "number") {
            throw new Error("Invalid region ID");
        }

        const url = target==="regions"
            ? `${window.location.origin}/${appName}/regions/${currentRegionId}/delete`
            : `${window.location.origin}/${appName}/similarity/reset/${currentRegionId}`;
        try {
            const response = await withLoading(() => fetch(url, {
                method: "DELETE",
                headers: { "X-CSRFToken": csrfToken },
            }));
            if ( ![200,204].includes(response.status) ) {
                throw new Error(`Failed to delete ${target}: '${response.statusText}'`);
            }
            window.location.href = `${baseUrl.split("regions/")[0]}regions/`;
        } catch (error) {
            console.error(error);
            await showMessage(error.message, "Error");
        }
    }

    function deleteResults() {
        if (regionExtractionTabs.includes($activeLayout)) {
            deleteAction("regions");
        } else if (similarityTabs.includes($activeLayout)) {
            deleteAction("similarity");
        }
    }

    $: resultName = regionExtractionTabs.includes($activeLayout)
        ? regionExtractionName(true)
        : similarityName;
</script>

<div>
    {#if currentRegionId}
        <a href="{allRegionsUrl}/?{searchParamsString}" class="tag is-dark mr-3 mb-3 is-rounded">
            {appLang === "en" ? "Back to all witness view" : "Retour à la vue complète du témoin"}
        </a>
        {#if regionExtractionTabs.concat(similarityTabs).includes($activeLayout)}
            <button on:click={deleteResults} class="tag mr-3 mb-3 is-danger">
                {appLang === "en" ? `Delete displayed ${resultName}` : `Supprimer les ${resultName} affichées`}
            </button>
        {/if}
    {:else}
        {#each witness.region_extraction as regionId}
            <a href="{baseUrl}{regionId}/?{searchParamsString}" class="tag is-dark mr-3 mb-3 is-rounded">
                Regions extraction #{regionId}
            </a>
        {/each}
    {/if}
</div>
