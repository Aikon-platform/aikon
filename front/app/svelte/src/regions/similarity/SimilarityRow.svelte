<script>
    import { onMount, onDestroy, setContext, getContext } from "svelte";
    import { fade } from "svelte/transition";
    import { similarityStore } from "./similarityStore.js";
    import { csrfToken } from "../../constants";
    import { i18n, getColNb, manifestToMirador, refToIIIF, showMessage } from "../../utils.js";
    import { toRegionItem } from "../utils.js";

    import MatchedRegions from "./MatchedRegions.svelte";
    import Row from "../../Row.svelte";

    export let qImg;
    export let isInModal = false;

    const row = similarityStore.createRowStore(qImg, isInModal);
    const { loading, propagatedLoading, error, propagated, filtered, fetchAll } = row;
    const { selectedRegions, baseUrl, currentPageId } = similarityStore;

    const [wit, digit, canvas, xywh] = qImg.split(".")[0].split("_");
    const manifest = getContext("manifest");

    const t = {
        invalidRef: {
            en: "Please insert a valid region reference to add a new match",
            fr: "Veuillez insérer une référence de région valide pour ajouter une nouvelle correspondance"
        },
        noMatch: {
            en: 'No match for this region in this witness',
            fr: 'Aucune correspondance de cette région pour ce témoin'
        },
        newMatch: {en: 'Add new match', fr: 'Ajouter une correspondance'},
        networkPb: {en: "Problem with network", fr: "Problème de réseau"},
        qImg: {en: "Query image", fr: "Image requête"},
        confirmNoMatch: {
            en: "Do you confirm this region does not have any match in",
            fr: "Confirmez-vous que cette région n'a pas de correspondance dans"
        },
    };

    let sImg = "";
    let innerWidth = 0;
    $: colNb = getColNb(innerWidth);
    $: sLen = Object.keys($selectedRegions[currentPageId] || {}).length;
    $: gridClass = `fixed-grid has-${colNb - 1}-cols`;

    setContext("qImgMetadata", toRegionItem(qImg, wit, xywh, canvas));

    // Lazy loading state
    let hasBeenVisible = isInModal;
    let rowEl;

    $: noRegionsSelected = !isInModal && sLen === 0;
    onMount(() => {
        if (!isInModal) {
            const observer = new IntersectionObserver(([entry]) => {
                if (entry.isIntersecting) {
                    hasBeenVisible = true;
                    row.setVisible(true); // initial fetch
                    observer.disconnect();
                }
            }, { rootMargin: "200px" });

            observer.observe(rowEl);
            return () => observer.disconnect();
        } else {
            row.setVisible(true);
        }
    });

    // Cleanup global subscriptions created by the row store
    onDestroy(row.destroy);

    function check_region_ref(region_ref) {
        region_ref = region_ref.replace(".jpg", "");
        return /^wit\d+_[a-zA-Z]{3}\d+_\d+_\d+,\d+,\d+,\d+$/.test(region_ref);
    }

    async function addMatch() {
        if (!sImg || !check_region_ref(sImg)) {
            await showMessage(i18n("invalidRef", t), i18n("error"));
            return;
        }
        try {
            const response = await fetch(`${baseUrl}add-region-pair`, {
                method: "POST",
                headers: {"Content-Type": "application/json", "X-CSRFToken": csrfToken},
                body: JSON.stringify({
                    q_img: qImg.replace(".jpg", ""),
                    s_img: sImg,
                })
            });
            if (!response.ok) {
                await showMessage(i18n("networkPb", t), i18n("error"));
                return;
            }
            const data = await response.json();
            if (data.hasOwnProperty("error") || !data.hasOwnProperty("s_regions")) {
                await showMessage(`${i18n("errored")}<br>${data.error}`, i18n("error"));
                return;
            }

            // Update global state
            similarityStore.addComparedRegions(data.s_regions);
            similarityStore.select(data.s_regions);

            fetchAll();
        } catch (error) {
            await showMessage(`${i18n("errored")}<br>${error}`, i18n("error"));
        }
    }

    async function noMatch() {
        const regions = Object.values($selectedRegions[currentPageId] || {})[0];
        if (!regions) return;
        const confirmed = await showMessage(
            `${i18n("confirmNoMatch", t)} ${regions.title}?`, i18n("confirm"), true
        );
        if (!confirmed) return;
        try {
            const response = await fetch(`${baseUrl}no-match`, {
                method: "POST",
                headers: {"Content-Type": "application/json", "X-CSRFToken": csrfToken},
                body: JSON.stringify({q_img: qImg, s_regions: regions.id})
            });
            if (!response.ok) {
                await showMessage(`${i18n("networkPb")}`, i18n("error"));
                return;
            }
            fetchAll(); // update only this row
        } catch (error) {
            await showMessage(`${i18n("errored")}<br>${error}`, i18n("error"));
        }
    }
</script>

<svelte:window bind:innerWidth/>

<Row useGrid={false}>
    <svelte:fragment slot="row-header">
        <div bind:this={rowEl} class="is-flex is-flex-direction-column is-align-items-center">
            <a class="tag px-2 py-1 mb-2 is-rounded is-hoverable" href="{manifestToMirador(manifest, parseInt(canvas))}" target="_blank">
                <i class="fa-solid fa-pen-to-square"/>
                Page {parseInt(canvas)}
            </a>
            <img src="{refToIIIF(qImg, qImg.split('_').pop(), '250,')}" alt={i18n("qImg", t)} class="mb-3 card query-image">
            <div class="new-similarity control pt-2">
                <div class="tags has-addons" style="flex-wrap: nowrap">
                    <input bind:value={sImg} class="input is-small tag" type="text" placeholder="{i18n('newMatch', t)}"/>
                    <button class="button is-small tag is-link is-center" on:click={addMatch}>
                        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 448 512">
                            <path fill="currentColor" d="M256 80c0-17.7-14.3-32-32-32s-32 14.3-32 32l0 144L48 224c-17.7 0-32 14.3-32 32s14.3 32 32 32l144 0 0 144c0 17.7 14.3 32 32 32s32-14.3 32-32l0-144 144 0c17.7 0 32-14.3 32-32s-14.3-32-32-32l-144 0 0-144z"/>
                        </svg>
                    </button>
                </div>

                <button id="no-match" class="button is-small tag is-danger is-center m-0" class:visible={sLen === 1}
                        on:click={noMatch} transition:fade={{ duration: 500 }} title="{i18n('noMatch', t)}">
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 384 512">
                        <path fill="white" d="M376.6 84.5c11.3-13.6 9.5-33.8-4.1-45.1s-33.8-9.5-45.1 4.1L192 206 56.6 43.5C45.3 29.9 25.1 28.1 11.5 39.4S-3.9 70.9 7.4 84.5L150.3 256 7.4 427.5c-11.3 13.6-9.5 33.8 4.1 45.1s33.8 9.5 45.1-4.1L192 306 327.4 468.5c11.3 13.6 31.5 15.4 45.1 4.1s15.4-31.5 4.1-45.1L233.7 256 376.6 84.5z"/>
                    </svg>
                </button>
            </div>
        </div>
    </svelte:fragment>

    <svelte:fragment slot="row-body">
        {#if hasBeenVisible}
            <div class="{isInModal ? '' : gridClass}">
                <MatchedRegions items={$filtered} loading={$loading} error={$error} {qImg} {isInModal} {noRegionsSelected} />
            </div>
            <div class="{isInModal ? '' : gridClass}">
                <div class="block matches-suggestion-wrapper">
                    <div class="matches-suggestion">
                        <MatchedRegions items={$propagated} loading={$propagatedLoading} error={null} isPropagated={true} {qImg} {isInModal} />
                    </div>
                </div>
            </div>
        {/if}
    </svelte:fragment>
</Row>

<style>
    .query-image {
        max-height: 60vh;
    }

    .new-similarity {
        display: flex;
        gap: 0.5em;
    }

    #no-match {
        opacity: 0;
        visibility: hidden;
        transition: opacity 0.3s ease-out, visibility 0.3s ease-out;
    }

    .matches-suggestion-wrapper {
        border: 1px solid var(--bulma-border);
        border-radius: 1em;
    }

    .matches-suggestion {
        margin: 1.5rem;
    }
</style>
