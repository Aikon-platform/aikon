<script>
    import { appLang } from "../constants";
    import { openModal } from "../utils";
    export let docSelectionLength = 0;
    export let regionSelectionLength = 0;
    export let selectionType;

    let previousDocLength = docSelectionLength;
    $: if (docSelectionLength !== previousDocLength) {
        const isIncreasing = docSelectionLength > previousDocLength;
        previousDocLength = docSelectionLength;

        const button = document.getElementById("doc-btn-content");
        if (button) {
            button.animate([
                { transform: isIncreasing ? "translateY(-7px)" : "translateX(-5px)" },
                { transform: isIncreasing ? "translateY(7px)" : "translateX(5px)" },
                { transform: "translate(0)" }
            ], {
                duration: 300,
                easing: "cubic-bezier(0.65, 0, 0.35, 1)"
            });
        }
    }

    let previousRegionLength = regionSelectionLength;
    $: if (regionSelectionLength !== previousRegionLength) {
        const isIncreasing = regionSelectionLength > previousRegionLength;
        previousRegionLength = regionSelectionLength;

        const button = document.getElementById("region-btn-content");
        if (button) {
            button.animate([
                { transform: isIncreasing ? "translateY(-7px)" : "translateX(-5px)" },
                { transform: isIncreasing ? "translateY(7px)" : "translateX(5px)" },
                { transform: "translate(0)" }
            ], {
                duration: 300,
                easing: "cubic-bezier(0.65, 0, 0.35, 1)"
            });
        }
    }
</script>

{#if selectionType === "document-set"}
    <button id="doc-set-btn" class="button px-5 py-4 is-link" data-target={`${selectionType}-modal`} use:openModal>
        <span id="doc-btn-content">
            <i class="fa-solid fa-book-bookmark"></i>
            {appLang === "en" ? "Document selection" : "Sélection de documents"}
            ({docSelectionLength})
        </span>
    </button>
{:else if selectionType === "region-set"}
    <button id="region-set-btn" class="button px-5 py-4 is-link is-light" data-target={`${selectionType}-modal`} use:openModal>
        <span id="region-btn-content">
            <i class="fa-regular fa-images"></i>
            {appLang === "en" ? "Region selection" : "Sélection de régions"}
            ({regionSelectionLength})
        </span>
    </button>
{/if}

<style>
    #doc-set-btn,
    #region-set-btn {
        border-radius: 0;
    }
</style>
