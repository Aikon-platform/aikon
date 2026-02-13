<script>
    import {onMount, onDestroy, setContext, getContext} from "svelte";
    import {get} from "svelte/store";
    import {fade} from "svelte/transition";
    import {similarityStore} from "./similarityStore.js";
    import {appLang, csrfToken} from "../../constants";
    import {getColNb, manifestToMirador, refToIIIF, showMessage} from "../../utils.js";
    import {toRegionItem} from "../utils.js";

    import MatchedRegions from "./MatchedRegions.svelte";
    import Row from "../../Row.svelte";

    export let qImg;
    export let isInModal = false;

    const {
        selectedRegions, excludedCategories, similarityScoreCutoff,
        propagateParams, baseUrl, currentPageId
    } = similarityStore;

    const [wit, digit, canvas, xywh] = qImg.split(".")[0].split("_");
    const manifest = getContext("manifest");
    const errorName = appLang === "en" ? "Error" : "Erreur";

    let sImg = "";
    let innerWidth = 0;
    $: colNb = getColNb(innerWidth);
    $: sLen = Object.keys($selectedRegions[currentPageId] || {}).length;
    $: gridClass = `fixed-grid has-${colNb - 1}-cols`;

    setContext("qImgMetadata", toRegionItem(qImg, wit, xywh, canvas));

    // Lazy loading
    let hasBeenVisible = isInModal;
    let rowEl;

    // SIMILAR MATCHES (filtered)
    let computedItems = [];
    let computedLoading = false;
    let computedError = null;
    let computedGen = 0;

    // PROPAGATED MATCHES (unfiltered)
    let propagatedItems = [];
    let propagatedLoading = false;
    let propagatedError = null;
    let propagatedGen = 0;

    // Computed only; propagated are unfiltered
    $: noRegionsSelected = !isInModal
        && Object.keys($selectedRegions[currentPageId] || {}).length === 0;

    $: filteredComputed = computedItems.filter(
        ([score, , , , , category]) =>
            !$excludedCategories.includes(category)
            && (score === null || $similarityScoreCutoff == null || Number(score) >= $similarityScoreCutoff)
    );

    const getRegionsIds = (sel) => Object.values(sel[currentPageId] || {}).map(r => r.id);

    async function fetchComputed(regionsIds) {
        const gen = ++computedGen;
        computedLoading = true;
        computedError = null;
        try {
            const res = await fetch(`${baseUrl}similar-images`, {
                method: "POST",
                headers: {"Content-Type": "application/json", "X-CSRFToken": csrfToken},
                body: JSON.stringify({regionsIds, filterByRegions: !isInModal, qImg, topk: 10}),
            });
            const data = await res.json();
            if (gen === computedGen) computedItems = data;
        } catch (e) {
            if (gen === computedGen) computedError = e.message;
        } finally {
            if (gen === computedGen) computedLoading = false;
        }
    }

    async function fetchPropagated(params, regionsIds) {
        const gen = ++propagatedGen;
        propagatedLoading = true;
        propagatedError = null;
        try {
            const res = await fetch(`${baseUrl}propagated-matches/${qImg}`, {
                method: "POST",
                headers: {"Content-Type": "application/json", "X-CSRFToken": csrfToken},
                body: JSON.stringify({
                    regionsIds: isInModal ? [] : regionsIds,
                    filterByRegions: isInModal ? false : params.propagateFilterByRegions,
                    recursionDepth: params.propagateRecursionDepth,
                }),
            });
            const data = await res.json();
            if (gen === propagatedGen) propagatedItems = data;
        } catch (e) {
            if (gen === propagatedGen) {
                propagatedError = e.message;
                propagatedItems = [];
            }
        } finally {
            if (gen === propagatedGen) propagatedLoading = false;
        }
    }

    function fetchAll() {
        const rids = getRegionsIds(get(selectedRegions));
        if (!isInModal && rids.length === 0) {
            computedItems = [];
            computedLoading = false;
        } else {
            fetchComputed(rids);
        }
        fetchPropagated(get(propagateParams), rids);
    }

    let unsubs = [];

    onMount(() => {
        if (!isInModal) {
            const observer = new IntersectionObserver(
                ([entry]) => {
                    if (entry.isIntersecting) {
                        hasBeenVisible = true;
                        observer.disconnect();
                        fetchAll();
                    }
                },
                {rootMargin: "200px"}
            );
            observer.observe(rowEl);
            unsubs.push(() => observer.disconnect());
        }

        let mounted = false;
        unsubs.push(selectedRegions.subscribe(() => {
            if (hasBeenVisible && mounted) fetchAll();
        }));
        unsubs.push(propagateParams.subscribe(() => {
            if (hasBeenVisible && mounted) {
                const rids = getRegionsIds(get(selectedRegions));
                fetchPropagated(get(propagateParams), rids);
            }
        }));
        mounted = true;

        if (hasBeenVisible) fetchAll();
    });

    onDestroy(() => unsubs.forEach(fn => fn()));

    function check_region_ref(region_ref) {
        region_ref = region_ref.replace(".jpg", "");
        return /^wit\d+_[a-zA-Z]{3}\d+_\d+_\d+,\d+,\d+,\d+$/.test(region_ref);
    }

    async function addMatch() {
        if (!sImg || !check_region_ref(sImg)) {
            await showMessage(
                appLang === "en"
                    ? "Please insert a valid region reference to add a new match"
                    : "Veuillez insérer une référence de région valide pour ajouter une nouvelle correspondance",
                "Error");
            return;
        }
        try {
            const response = await fetch(`${baseUrl}add-region-pair`, {
                method: "POST",
                headers: {"Content-Type": "application/json", "X-CSRFToken": csrfToken},
                body: JSON.stringify({
                    q_img: qImg.replace(".jpg", ""), // TODO no need to remove .jpg
                    s_img: sImg,
                })
            });
            if (!response.ok) {
                await showMessage(appLang === "en" ? "Problem with network, match was not added" : "Problème de réseau, la correspondance n'a pas été ajoutée", errorName);
                return;
            }
            const data = await response.json();
            if (data.hasOwnProperty("error") || !data.hasOwnProperty("s_regions")) {
                await showMessage(appLang === "en" ? `Request was unsuccessful:<br>${data.error}` : `La requête n'a pas abouti :<br>${data.error}`, errorName);
                return;
            }
            similarityStore.addComparedRegions(data.s_regions);
            similarityStore.select(data.s_regions);
            fetchAll();
        } catch (error) {
            await showMessage(appLang === "en" ? `An error has occurred:<br>${error}` : `Une erreur s'est produite :<br>${error}`, errorName);
        }
    }

    async function noMatch() {
        const regions = Object.values($selectedRegions[currentPageId] || {})[0];
        if (!regions) return;
        const confirmed = await showMessage(
            appLang === "en"
                ? `Do you confirm this region does not have any match in ${regions.title}?`
                : `Confirmez-vous que cette région n'a pas de correspondance dans ${regions.title} ?`,
            appLang === "en" ? "Confirm no match" : "Confirmer l'absence de correspondance",
            true
        );
        if (!confirmed) return;
        try {
            const response = await fetch(`${baseUrl}no-match`, {
                method: "POST",
                headers: {"Content-Type": "application/json", "X-CSRFToken": csrfToken},
                body: JSON.stringify({q_img: qImg, s_regions: regions.id})
            });
            if (!response.ok) {
                await showMessage(appLang === "en" ? "Problem with network" : "Problème de réseau", errorName);
                return;
            }
            fetchAll();
        } catch (error) {
            await showMessage(appLang === "en" ? `An error has occurred:<br>${error}` : `Une erreur s'est produite :<br>${error}`, errorName);
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
            <img src="{refToIIIF(qImg, qImg.split('_').pop(), '250,')}" alt="Query region" class="mb-3 card query-image">
            <div class="new-similarity control pt-2">
                <div class="tags has-addons" style="flex-wrap: nowrap">
                    <input bind:value={sImg} class="input is-small tag" type="text"
                           placeholder="{appLang === 'en' ? 'Add new match' : 'Ajouter une correspondance'}"/>
                    <button class="button is-small tag is-link is-center" on:click={addMatch}>
                        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 448 512">
                            <path fill="currentColor"
                                  d="M256 80c0-17.7-14.3-32-32-32s-32 14.3-32 32l0 144L48 224c-17.7 0-32 14.3-32 32s14.3 32 32 32l144 0 0 144c0 17.7 14.3 32 32 32s32-14.3 32-32l0-144 144 0c17.7 0 32-14.3 32-32s-14.3-32-32-32l-144 0 0-144z"/>
                        </svg>
                    </button>
                </div>
                <button id="no-match" class="button is-small tag is-danger is-center m-0" class:visible={sLen === 1}
                        on:click={noMatch} transition:fade={{ duration: 500 }}
                        title="{appLang === 'en' ? 'No match for this region in this witness' : 'Aucune correspondance de cette région pour ce témoin'}">
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 384 512">
                        <path fill="white"
                              d="M376.6 84.5c11.3-13.6 9.5-33.8-4.1-45.1s-33.8-9.5-45.1 4.1L192 206 56.6 43.5C45.3 29.9 25.1 28.1 11.5 39.4S-3.9 70.9 7.4 84.5L150.3 256 7.4 427.5c-11.3 13.6-9.5 33.8 4.1 45.1s33.8 9.5 45.1-4.1L192 306 327.4 468.5c11.3 13.6 31.5 15.4 45.1 4.1s15.4-31.5 4.1-45.1L233.7 256 376.6 84.5z"/>
                    </svg>
                </button>
            </div>
        </div>
    </svelte:fragment>
    <svelte:fragment slot="row-body">
        {#if hasBeenVisible}
            <div class="{isInModal ? '' : gridClass}">
                <MatchedRegions items={filteredComputed} loading={computedLoading} error={computedError}
                             {qImg} {isInModal} {noRegionsSelected} />
            </div>
            <div class="{isInModal ? '' : gridClass}">
                <div class="block matches-suggestion-wrapper">
                    <div class="matches-suggestion">
                        <MatchedRegions items={propagatedItems} loading={propagatedLoading} error={propagatedError}
                                     isPropagated={true} {qImg} {isInModal} />
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
