<script>
    import {writable, derived} from "svelte/store";
    import InputDropdown from "../ui/InputDropdown.svelte";
    import LegendItem from "./sidebar/LegendItem.svelte";
    import RegionCard from "../regions/RegionCard.svelte";
    import RegionModal from "../regions/modal/RegionModal.svelte";
    import RegionTabs from "../regions/modal/RegionTabs.svelte";
    import {i18n, sendTo, showMessage} from "../utils.js";
    import {appName, isSuperuser} from "../constants.js";

    export let documentSetStore;
    const {witnessNodes, documentNodes, visiblePairs, selectedDocuments, removeImages} = documentSetStore;

    const MAX = 5;
    const t = {
        matches: {en: "matches", fr: "correspondances"},
        reset: {en: "Remove filters", fr: "Retirer les filtres"},
        selected: {en: "selected", fr: "sélectionnée(s)"},
        noImage: {en: "No image for these filters", fr: "Aucune image pour ces filtres"},
        deletePairs: {
            en: "Delete all pairs containing the selected images",
            fr: "Supprimer toutes les paires contenant les images sélectionnées"
        },
        confirmDelete: {
            en: "selected image(s): all pairs containing them will be permanently deleted, including annotated pairs. Continue?",
            fr: "image(s) sélectionnée(s) : toutes les paires les contenant seront définitivement supprimées, y compris les paires annotées. Continuer ?"
        },
    };

    const selected = writable(new Set());
    const localSelection = {
        toggle: item => selected.update(s => (s.delete(item.id) || s.add(item.id), s)),
        isSelected: derived(selected, $s => item => $s.has(item.id)),
    };

    const toggle = (set, v) => (set.delete(v) || set.add(v), set);
    const link = (m, a, b, digit) => (m.get(a) ?? m.set(a, new Map()).get(a)).set(b, digit);
    const bucket = n => Math.min(n, MAX);
    const label = n => n === MAX ? `${MAX}+` : n;
    const dot = color => `<i class="fa-solid fa-circle" style="color: ${color}"></i>`;
    const newPage = (prev, img) => !prev || prev.digit !== img.digit || prev.canvas !== img.canvas;

    let witId, buckets = new Set(), witFilter = new Set(), modalOpen = false, modalIndex = 0;
    const reset = () => {
        buckets = new Set();
        witFilter = new Set();
    };

    $: witnesses = [...$witnessNodes.values()].filter(w => w.Digitization.some(d => $selectedDocuments.has(d)));
    $: witId = witnesses.some(w => w.id === witId) ? witId : witnesses[0]?.id;
    $: witId, reset(), selected.set(new Set());
    $: witOfDigit = new Map([...$witnessNodes.values()].flatMap(w => w.Digitization.map(d => [d, w.id])));

    $: matches = $visiblePairs.reduce((m, p) => (link(m, p.id_1, p.id_2, p.digit_2), link(m, p.id_2, p.id_1, p.digit_1), m), new Map());
    $: rows = ($witnessNodes.get(witId)?.Digitization ?? [])
        .filter(d => $selectedDocuments.has(d))
        .flatMap(d => $documentNodes.get(d)?.images ?? [])
        .map(img => {
            const m = matches.get(img.id) ?? new Map();
            return {img, n: m.size, wits: new Set([...m.values()].map(d => witOfDigit.get(d)))};
        });
    $: counts = rows.reduce((c, r) => (c[bucket(r.n)]++, c), Array(MAX + 1).fill(0));
    $: maxCount = Math.max(...counts, 1);
    $: matchedWits = witnesses.filter(w => rows.some(r => r.wits.has(w.id)));
    $: shown = rows.filter(r =>
        (!buckets.size || buckets.has(bucket(r.n))) &&
        (!witFilter.size || [...witFilter].some(w => r.wits.has(w)))
    );

    async function deletePairs() {
        const ids = [...$selected];
        if (!ids.length || !await showMessage(`${ids.length} ${i18n("confirmDelete", t)}`, i18n("confirm"), true)) return;
        if (!await sendTo(`${appName}/similarity/delete-matches`, {q_imgs: ids})) return;
        removeImages(ids);
        selected.set(new Set());
    }
</script>

<div class="level is-align-items-flex-end">
    <div class="level-left">
        <div class="level-item" style="min-width: 20rem">
            {#key witnesses.map(w => w.id).join()}
                <InputDropdown multiple={false} start={[witId]}
                               choicesItems={witnesses.map(w => ({value: w.id, label: w.title, prefix: dot(w.color), prefixType: "text"}))}
                               on:updateValues={e => witId = e.detail[0] ?? witId}/>
            {/key}
        </div>

        <div class="level-item columns is-gapless is-mobile mb-0" style="width: 12rem">
            {#each counts as c, i}
                <div class="column is-flex is-flex-direction-column is-justify-content-flex-end has-text-centered is-size-7 has-text-grey" style="height: 4rem">
                    <button class="button is-small p-0 mx-1" class:is-link={!buckets.size || buckets.has(i)}
                            style="height: {5 + 70 * c / maxCount}%" title="{c} images · {label(i)} {i18n('matches', t)}"
                            on:click={() => buckets = toggle(buckets, i)}/>
                    {label(i)}
                </div>
            {/each}
        </div>

        <div class="level-item is-flex-wrap-wrap" style="max-width: 20rem; gap: 0.25rem">
            {#each matchedWits as w (w.id)}
                <LegendItem id={w.id} meta={w} onlyColor
                            isActive={!witFilter.size || witFilter.has(w.id)}
                            toggle={() => witFilter = toggle(witFilter, w.id)}/>
            {/each}
        </div>
    </div>

    <div class="level-right">
        <div class="level-item buttons">
            <button class="button is-small" disabled={!buckets.size && !witFilter.size} on:click={reset}>
                {i18n("reset", t)}
            </button>
            {#if isSuperuser}
                <button class="button is-small tag is-danger is-center m-0 has-text-light" disabled={!$selected.size}
                        on:click={deletePairs} title={i18n("deletePairs", t)}>
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 448 512">
                        <path fill="currentColor" d="M135.2 17.7L128 32 32 32C14.3 32 0 46.3 0 64S14.3 96 32 96l384 0c17.7 0 32-14.3 32-32s-14.3-32-32-32l-96 0-7.2-14.3C307.4 6.8 296.3 0 284.2 0L163.8 0c-12.1 0-23.2 6.8-28.6 17.7zM416 128L32 128 53.2 467c1.6 25.3 22.6 45 47.9 45l245.8 0c25.3 0 46.3-19.7 47.9-45L416 128z"/>
                    </svg>
                </button>
            {/if}
        </div>
    </div>
</div>

<p class="is-size-7 has-text-grey mb-2">{shown.length} / {rows.length} images · {$selected.size} {i18n("selected", t)}</p>

{#if !shown.length}
    <p class="has-text-grey is-size-7">{i18n("noImage", t)}</p>
{/if}

<div class="is-flex is-flex-wrap-wrap" style="gap: 1rem">
    {#each shown as r, i (r.img.id)}
        {#if newPage(shown[i - 1]?.img, r.img)}
            <p class="is-size-7 has-text-grey" style="flex-basis: 100%">Page {r.img.canvas}</p>
        {/if}
        <RegionCard item={r.img} index={i} selectionStore={localSelection}
                    on:openModal={e => [modalIndex, modalOpen] = [e.detail.index ?? 0, true]}>
            <span slot="actions" class="tag is-rounded" title={i18n("matches", t)}>{r.n}</span>
        </RegionCard>
    {/each}
</div>

<RegionModal items={shown.map(r => r.img)} bind:currentIndex={modalIndex} bind:open={modalOpen}>
    <svelte:fragment let:item={currentItem}>
        <RegionTabs item={currentItem}/>
    </svelte:fragment>
</RegionModal>
