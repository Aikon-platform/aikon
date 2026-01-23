<script>
    import html2canvas from 'html2canvas';
    import {showMessage, withLoading} from "../utils.js";
    import {appLang} from "../constants.js";

    export let targetId;
    export let filename = 'export.png';

    function getScrollParent(el) {
        while (el && el !== document.body) {
            const style = getComputedStyle(el);
            if (/(auto|scroll|hidden)/.test(style.overflow + style.overflowX + style.overflowY)) {
                return el;
            }
            el = el.parentElement;
        }
        return null;
    }

    async function download() {
        await withLoading(async () => {
            const el = document.getElementById(targetId);
            if (!el) return;

            const scrollParent = getScrollParent(el);
            const saved = scrollParent ? {
                overflow: scrollParent.style.overflow,
                maxHeight: scrollParent.style.maxHeight,
                height: scrollParent.style.height
            } : null;

            try {
                if (scrollParent) {
                    scrollParent.style.overflow = 'visible';
                    scrollParent.style.maxHeight = 'none';
                    scrollParent.style.height = 'auto';
                }

                const canvas = await html2canvas(el, {
                    backgroundColor: null,
                    scale: 2,
                    logging: false,
                    useCORS: true,
                    scrollX: 0,
                    scrollY: 0
                });

                const link = document.createElement('a');
                link.download = filename;
                link.href = canvas.toDataURL('image/png');
                link.click();
            } catch (error) {
                await showMessage(
                    `Error generating PNG: ${error}`,
                    appLang === "en" ? "Error" : "Erreur");
            } finally {
                if (scrollParent && saved) {
                    scrollParent.style.overflow = saved.overflow;
                    scrollParent.style.maxHeight = saved.maxHeight;
                    scrollParent.style.height = saved.height;
                }
            }
        });
    }
</script>

<button class="tag is-link" on:click={download} title="{appLang === 'en' ? 'Download as PNG' : 'Télécharger en PNG'}">
    <span class="icon is-small p-0">
        <i class="fas fa-download"></i>
    </span>
</button>
