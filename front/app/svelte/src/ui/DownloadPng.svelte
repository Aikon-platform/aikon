<script>
    import {toPng, toSvg} from "html-to-image";
    import {showMessage, withLoading} from "../utils.js";
    import {appLang} from "../constants.js";

    export let targetId;
    export let filename = "export";
    export let pixelRatio = 4;
    export let svgExport = false;

    const options = (el) => ({
        width: el.scrollWidth,
        height: el.scrollHeight,
        backgroundColor: getComputedStyle(document.body).backgroundColor,
        skipFonts: true,
        style: {overflow: "visible", maxHeight: "none", maxWidth: "none"},
        filter: node => !node.classList?.contains?.("matrix-tooltip") && !node.classList?.contains?.("scatter-tooltip"),
    });

    async function download() {
        const el = document.getElementById(targetId);
        if (!el) return;

        const asSvg = svgExport && await showMessage(
            appLang === "en" ? "Export as SVG? (Cancel for PNG)" : "Exporter en SVG ? (Annuler pour PNG)",
            appLang === "en" ? "Export format" : "Format d'export", true);

        await withLoading(async () => {
            try {
                const dataUrl = asSvg
                    ? await toSvg(el, options(el))
                    : await toPng(el, {pixelRatio, ...options(el)});

                const link = document.createElement("a");
                link.download = asSvg ? `${filename}.svg` : `${filename}.png`;
                link.href = dataUrl;
                link.click();
            } catch (error) {
                await showMessage(`Error generating export: ${error.message || error}`, appLang === "en" ? "Error" : "Erreur");
            }
        });
    }
</script>

<button class="tag is-link" on:click={download} title="{appLang === 'en' ? 'Download' : 'Télécharger'}">
    <span class="icon is-small p-0">
        <i class="fas fa-download"/>
    </span>
</button>
