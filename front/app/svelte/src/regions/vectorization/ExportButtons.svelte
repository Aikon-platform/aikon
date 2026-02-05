<script>
    import { getContext } from 'svelte';
    import { downloadBlob, withLoading } from "../../utils.js";
    import { appName, appLang, csrfToken } from '../../constants';

    const baseUrl = `${window.location.origin}${window.location.pathname}`;
    const currentWitnessId = parseInt(baseUrl.split('witness/')[1].replace("/", ""));
    const currentRegionId = parseInt(baseUrl.split('regions/')[1].replace("/", ""));

    async function downloadVectorizations() {
        if (!currentRegionId && !currentWitnessId) {
            console.error("No Region or Witness");
            return;
        }

        const endpoint = currentRegionId
            ? `${window.location.origin}/${appName}/export-regions-imgs-and-svgs/${currentRegionId}`
            : `${window.location.origin}/${appName}/export-all-imgs-and-svgs/${currentWitnessId}`;

        try {
            const response = await withLoading(() =>
                fetch(endpoint, {
                    method: "GET",
                    headers: {
                        "X-CSRFToken": csrfToken,
                        "Content-Type": "application/json"
                    }
                })
            );

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const blob = await response.blob();
            downloadBlob(blob, 'vectorizations.zip');
        } catch (error) {
            console.error("Erreur lors du téléchargement des vectorisations:", error);
        }
}

</script>

<div class="is-right mb-3">
    <button class="button is-link is-light" on:click={downloadVectorizations}>
        <i class="fa-solid fa-download"></i>
        {appLang === 'en' ? 'Download All' : 'Tout Télécharger'}
    </button>
</div>
