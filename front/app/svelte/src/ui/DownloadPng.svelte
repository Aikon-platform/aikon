<script>
    import {toPng} from "html-to-image";
    import {showMessage, withLoading} from "../utils.js";
    import {appLang} from "../constants.js";

    export let targetId;
    export let filename = "export.png";
    export let pixelRatio = 2;

    async function download() {
        await withLoading(async () => {
            const el = document.getElementById(targetId);
            if (!el) return;
            try {
                const dataUrl = await toPng(el, {
                    pixelRatio,
                    width: el.scrollWidth,
                    height: el.scrollHeight,
                    backgroundColor: getComputedStyle(document.body).backgroundColor,
                    skipFonts: true,
                    style: {overflow: "visible", maxHeight: "none", maxWidth: "none"},
                    filter: node => !node.classList?.contains?.("matrix-tooltip") && !node.classList?.contains?.("scatter-tooltip"),
                });

                const link = document.createElement("a");
                link.download = filename;
                link.href = dataUrl;
                link.click();
            } catch (error) {
                await showMessage(`Error generating PNG: ${error.message || error}`, appLang === "en" ? "Error" : "Erreur");
            }
        });
    }
</script>

<button class="tag is-link" on:click={download} title="{appLang === 'en' ? 'Download as PNG' : 'Télécharger en PNG'}">
    <span class="icon is-small p-0">
        <i class="fas fa-download"/>
    </span>
</button>
