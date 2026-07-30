<script>
    import {toPng} from "html-to-image";
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

    async function downloadSvg(el) {
        const {domToSvg} = await import("dom2svg");
        const res = await domToSvg(el, {
            background: getComputedStyle(document.body).backgroundColor,
            padding: 8,
            compat: "inkscape",
        });
        res.download(`${filename}.svg`);
    }

    async function downloadPng(el){
        const dataUrl = await toPng(el, {pixelRatio, ...options(el)});

        const link = document.createElement("a");
        link.download = `${filename}.png`;
        link.href = dataUrl;
        link.click();
    }

    async function download() {
        const el = document.getElementById(targetId);
        if (!el) return;

        const asSvg = svgExport && await showMessage(
            appLang === "en" ? "Export as SVG? (Cancel for PNG)" : "Exporter en SVG ? (Annuler pour PNG)",
            appLang === "en" ? "Export format" : "Format d'export", true
        );

        await withLoading(async () => {
            try {
                if (asSvg) {
                    await downloadSvg(el);
                } else {
                    await downloadPng(el);
                }
            } catch (error) {
                console.error(error);
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
