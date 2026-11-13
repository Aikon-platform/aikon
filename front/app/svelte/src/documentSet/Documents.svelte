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
        showMatchesIn: {en: "Show images that have matches in", fr: "Afficher les images ayant des correspondances dans"},
        bar: {
            en: "{c} image(s) with {n} match(es). Click to show / hide",
            fr: "{c} image(s) avec {n} correspondance(s). Cliquer pour afficher / masquer"
        },
        hideWit: {en: "click to hide matches in", fr: "cliquer pour masquer les correspondances avec"},
        showWit: {en: "click to show matches in", fr: "cliquer pour afficher les correspondances avec"},
        resetDesc: {en: "Show all bars and witnesses again", fr: "Réafficher toutes les barres et tous les témoins"},
        selectToDelete: {en: "Select images to delete their pairs", fr: "Sélectionner des images pour supprimer leurs paires"},
    };

    const barTitle = (c, i) => i18n("bar", t).replace("{c}", c).replace("{n}", label(i));

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

    let witId, buckets = new Set(), hidden = new Set(), modalOpen = false, modalIndex = 0;
    const reset = () => {
        buckets = new Set();
        hidden = new Set();
    };

    const push = (m, k, v) => (m.get(k) ?? m.set(k, []).get(k)).push(v);

    const witOf = d => d.witness_id ?? +d.images[0]?.ref.match(/^wit(\d+)/)?.[1];
    $: digitsOf = [...$documentNodes].reduce((m, [id, d]) => (push(m, witOf(d), id), m), new Map());
    $: witOfDigit = new Map([...$documentNodes].map(([id, d]) => [id, witOf(d)]));
    $: witnesses = [...digitsOf]
        .map(([id, digits]) => [id, digits.filter(d => $selectedDocuments.has(d))])
        .filter(([, digits]) => digits.length)
        .map(([id, [digit]]) => {
            const {title, color} = $documentNodes.get(digit);
            return {id, witness_id: id, title, color};
        });
    $: witId = witnesses.some(w => w.id === witId) ? witId : witnesses[0]?.id;
    $: witId, reset(), selected.set(new Set());

    $: matches = $visiblePairs.reduce((m, p) => (link(m, p.id_1, p.id_2, p.digit_2), link(m, p.id_2, p.id_1, p.digit_1), m), new Map());
    $: base = (digitsOf.get(witId) ?? [])
        .filter(d => $selectedDocuments.has(d))
        .flatMap(d => $documentNodes.get(d)?.images ?? [])
        .map(img => ({img, wits: [...(matches.get(img.id) ?? [])].map(([, d]) => witOfDigit.get(d))}));
    $: rows = base
        .map(r => ({...r, n: r.wits.filter(w => !hidden.has(w)).length}))
        .filter(r => !hidden.size || r.n);
    $: counts = rows.reduce((c, r) => (c[bucket(r.n)]++, c), Array(MAX + 1).fill(0));
    $: maxCount = Math.max(...counts, 1);
    $: matchedWits = witnesses.filter(w => base.some(r => r.wits.includes(w.id)));
    $: shown = rows.filter(r => !buckets.size || buckets.has(bucket(r.n)));

    async function deletePairs() {
        const ids = [...$selected];
        if (!ids.length || !await showMessage(`${ids.length} ${i18n("confirmDelete", t)}`, i18n("confirm"), true)) return;
        if (!await sendTo(`${appName}/similarity/delete-matches`, {q_imgs: ids})) return;
        removeImages(ids);
        selected.set(new Set());
    }
</script>

<div class="level">
    <div class="level-left">
        <div class="level-item">
            <div style="width: 25rem" class="mr-3">
                {#key witnesses.map(w => w.id).join()}
                    <InputDropdown multiple={false} start={[witId]}
                                   choicesItems={witnesses.map(w => ({value: w.id, label: w.title, prefix: dot(w.color), prefixType: "text"}))}
                                   on:updateValues={e => witId = e.detail[0] ?? witId}/>
                {/key}
            </div>
        </div>

        <div class="level-item columns is-gapless is-mobile mb-0 mr-3" style="width: 12rem">
            {#each counts as c, i}
                <div class="column is-flex is-flex-direction-column is-justify-content-flex-end has-text-centered is-size-7 has-text-grey" style="height: 4rem">
                    <button class="button is-small p-0 mx-1" class:is-link={!buckets.size || buckets.has(i)}
                            style="height: {5 + 70 * c / maxCount}%" title={barTitle(c, i)}
                            on:click={() => buckets = toggle(buckets, i)}/>
                    {label(i)}
                </div>
            {/each}
        </div>

        {#if matchedWits.length}
            <div class="level-item is-flex-wrap-wrap" style="max-width: 24rem; gap: 0.25rem">
                <span class="is-size-7 has-text-grey mr-1">{i18n("showMatchesIn", t)}</span>
                {#each matchedWits as w (w.id)}
                    <LegendItem id={w.id} meta={w} onlyColor isActive={!hidden.has(w.id)}
                                title="{i18n(hidden.has(w.id) ? 'showWit' : 'hideWit', t)} {w.title}"
                                toggle={() => hidden = toggle(hidden, w.id)}/>
                {/each}
            </div>
        {/if}
    </div>

    <div class="level-right">
        <div class="level-item buttons">
            <button class="button is-small" title={i18n("resetDesc", t)}
                    disabled={!buckets.size && !hidden.size} on:click={reset}>
                {i18n("reset", t)}
            </button>
            {#if isSuperuser}
                <span title={i18n($selected.size ? "deletePairs" : "selectToDelete", t)}>
                    <button class="button is-small tag is-danger is-center m-0 has-text-light"
                            disabled={!$selected.size} on:click={deletePairs}>
                        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 448 512">
                            <path fill="currentColor" d="M135.2 17.7L128 32 32 32C14.3 32 0 46.3 0 64S14.3 96 32 96l384 0c17.7 0 32-14.3 32-32s-14.3-32-32-32l-96 0-7.2-14.3C307.4 6.8 296.3 0 284.2 0L163.8 0c-12.1 0-23.2 6.8-28.6 17.7zM416 128L32 128 53.2 467c1.6 25.3 22.6 45 47.9 45l245.8 0c25.3 0 46.3-19.7 47.9-45L416 128z"/>
                        </svg>
                    </button>
                </span>
            {/if}
        </div>
    </div>
</div>

<p class="is-size-7 has-text-grey mb-4">{shown.length} / {base.length} images</p>

{#if !shown.length}
    <p class="has-text-grey is-size-7">{i18n("noImage", t)}</p>
{/if}

<div class="grid is-gap-2 mt-2">
    {#each shown as r, i (r.img.id)}
        <RegionCard item={r.img} index={i} copyable={true} height={96} selectionStore={localSelection} on:openModal={e => [modalIndex, modalOpen] = [e.detail.index ?? 0, true]}/>
    {/each}
</div>

<RegionModal items={shown.map(r => r.img)} bind:currentIndex={modalIndex} bind:open={modalOpen}>
    <svelte:fragment let:item={currentItem}>
        <RegionTabs item={currentItem}/>
    </svelte:fragment>
</RegionModal>
