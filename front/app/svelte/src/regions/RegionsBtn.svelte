<script>
    import { getContext, onMount } from "svelte";

    import {showMessage, withLoading} from "../utils.js";
    import { appLang, appName, csrfToken } from "../constants";
    import { activeLayout } from "../ui/tabStore.js";

    const witness = getContext("witness");
    const baseUrl = `${window.location.origin}${window.location.pathname}`;
    const currentRegionId = parseInt(baseUrl.split("regions/")[1].replace("/", ""));

    const allRegionsUrl = baseUrl.replace(/\/\d+\/?$/, "");

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

    async function deleteRegions() {
        const confirmed = await showMessage(
            appLang === "en" ?
                "Are you sure you want to delete all the region extraction of this witness?" :
                "Voulez-vous vraiment supprimer les extractions de régions effectuées sur ce document ?",
            appLang === "en" ? "Confirm deletion" : "Confirmer la suppression",
            true
        );

        if (!confirmed) {
            return;
        }

        if (typeof currentRegionId !== "number") {
            throw new Error("Invalid region ID");
        }
        const url = `${window.location.origin}/${appName}/regions/${currentRegionId}/delete`;
        try {
            const response = await withLoading(() => fetch(url, {
                method: "DELETE",
                headers: { "X-CSRFToken": csrfToken },
            }));
            if (response.status !== 204) {
                throw new Error(`Failed to delete regions: '${response.statusText}'`);
            }
            window.location.href = `${baseUrl.split("regions/")[0]}regions/`;
        } catch (error) {
            console.error(error);
        }
    }

    async function deleteSimilarity() {
        const confirmed = await showMessage(
            appLang === "en" ? "Are you sure you want to delete all similarity scores for this document?" : "Voulez-vous vraiment supprimer l'intégralité des scores de similarité pour ce document ?",
            appLang === "en" ? "Confirm deletion" : "Confirmer la suppression",
            true
        );

        if (!confirmed) {
            return;
        }

        if (typeof currentRegionId !== "number") {
            throw new Error("Invalid region ID");
        }
        const url = `${window.location.origin}/${appName}/similarity/reset/${currentRegionId}`;
        try {
            const response = await withLoading(() => fetch(url, {
                method: "DELETE",
                headers: { "X-CSRFToken": csrfToken },
            }));
            if (response.status === 204 || response.status === 200) {
                window.location.href = `${baseUrl.split("regions/")[0]}regions/`;
            } else {
                throw new Error(`Failed to delete similarity: '${response.statusText}'`);
            }
        } catch (error) {
            console.error(error);
            await showMessage(error.message, "Error");
        }
    }

    function deleteResults() {
        if (["all", "page"].includes($activeLayout)) {
            deleteRegions();
        } else if ($activeLayout === "similarity") {
            deleteSimilarity();
        }
    }

    $: resultName = ["all", "page"].includes($activeLayout)
        ? (appLang === "en" ? "regions" : "régions")
        : (appLang === "en" ? "similarities" : "similarités");
</script>

<div>
    {#if currentRegionId}
        <a href="{allRegionsUrl}/?{searchParamsString}" class="tag is-dark mr-3 mb-3 is-rounded">
            {appLang === "en" ? "Back to all witness view" : "Retour à la vue complète du témoin"}
        </a>
        {#if ["all", "page", "similarity"].includes($activeLayout)}
            <button on:click={deleteResults} class="tag mr-3 mb-3 is-danger">
                {appLang === "en" ? `Delete displayed ${resultName}` : `Supprimer les ${resultName} affichés`}
            </button>
        {/if}
    {:else}
        {#each witness.regions as regionId}
            <a href="{baseUrl}{regionId}/?{searchParamsString}" class="tag is-dark mr-3 mb-3 is-rounded">
                Regions extraction #{regionId}
            </a>
        {/each}
        <!--TODO add NEW REGIONS BUTTON (to create empty region in order to launch new automatic extraction)-->
    {/if}
</div>
