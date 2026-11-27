<!-- @migration-task-ok Error while migrating Svelte code: can't migrate `$: digitsOf = [...$documentNodes].reduce((m, [id, d]) => (push(m, witOf(d), id), m), new Map());` to `$derived` because there's a variable named derived.
     Rename the variable and try again or migrate by hand. -->
<script>
    import { run } from 'svelte/legacy';

    import {onDestroy} from "svelte";
    import {writable, derived} from "svelte/store";
    import InputDropdown from "../../ui/InputDropdown.svelte";
    import InputToggle from "../../ui/InputToggle.svelte";
    // import LegendItem from "../sidebar/LegendItem.svelte";
    import RegionCard from "../../regions/RegionCard.svelte";
    import RegionModal from "../../regions/modal/RegionModal.svelte";
    import RegionTabs from "../../regions/modal/RegionTabs.svelte";
    import CategoryFilter from "../sidebar/CategoryFilter.svelte";
    import HistogramFilter from "./HistogramFilter.svelte";
    import DocumentPairs from "./DocumentPairs.svelte";
    import {pairCats} from "../documentSetStore.js";
    import {i18n, sendTo, shorten, showMessage, syncStoreWithURL} from "../../utils.js";
    import {appName, isSuperuser} from "../../constants.js";

    let { documentSetStore } = $props();
    const {documentNodes, imageNodes, visiblePairs, allPairs, pairsOfDocuments, selectedDocuments, docSetNumber, removeImages} = documentSetStore;

    const MAX = 5;
    const CATS = [0, 1, 2, 3, 5];
    const t = {
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
            en: "{s} / {c} image(s) with {n} match(es). Click to show / hide",
            fr: "{s} / {c} image(s) avec {n} correspondance(s). Cliquer pour afficher / masquer"
        },
        hideWit: {en: "click to hide matches in", fr: "cliquer pour masquer les correspondances avec"},
        showWit: {en: "click to show matches in", fr: "cliquer pour afficher les correspondances avec"},
        selectToDelete: {en: "Select images to delete their pairs", fr: "Sélectionner des images pour supprimer leurs paires"},
        images: {en: "Images", fr: "Images"},
        pairs: {en: "Pairs", fr: "Paires"},
        scoreFilter: {en: "Score filter", fr: "Filtre de score"},
        inPairs: {en: "Images in a pair", fr: "Images dans une paire"},
    };

    const barTitle = (c, s, i) => i18n("bar", t).replace("{s}", s).replace("{c}", c).replace("{n}", label(i));

    const view = writable("images");
    onDestroy(view.subscribe(syncStoreWithURL(view, "docView", "string", "images")));

    // NOTE: selected is kept as a `writable` store instead of a Svelte 5 construct because
    // `RegionCard` excepts `selectionStore` to be an actual store, not a `$state` or reactive object.
    const selected = writable(new Set());
    const localSelection = {
        toggle: (item) => selected.update((s) => {
            if (s.has(item.id)) s.delete(item.id);
            else s.add(item.id);
            return s;
        }),
        clear: () => selected.set(new Set()),
        isSelected: derived(selected, ($s) => (item) => $s.has(item.id)),
    };
    // remove values in `selected`, by reassigning to keep the store reactive.
    const clearSelected = () => selected.set(new Set());

    const toggle = (set, v) => (set.delete(v) || set.add(v), set);
    const link = (m, a, b, digit) => (m.get(a) ?? m.set(a, new Map()).get(a)).set(b, digit);
    const bucket = n => Math.min(n, MAX);
    const label = n => n === MAX ? `${MAX}+` : n;
    const dot = color => `<i class="fa-solid fa-circle" style="color: ${color}"></i>`;

    let witId = $state(), buckets = $state(new Set()), hidden = $state(new Set()), cats = $state(new Set()), scoreFilter = $state(false), modalOpen = $state(false), modalIndex = $state(0);
    const reset = () => {
        buckets = new Set();
        hidden = new Set();
        cats = new Set();
    };
    const toggleCat = c => cats = toggle(cats, c);

    const push = (m, k, v) => (m.get(k) ?? m.set(k, []).get(k)).push(v);

    const witOf = d => d.witness_id ?? +d.images[0]?.ref.match(/^wit(\d+)/)?.[1];
    let digitsOf = $derived([...$documentNodes].reduce((m, [id, d]) => (push(m, witOf(d), id), m), new Map()));
    let witOfDigit = $derived(new Map([...$documentNodes].map(([id, d]) => [id, witOf(d)])));
    let witnesses = $derived([...digitsOf]
        .map(([id, digits]) => [id, digits.filter(d => $selectedDocuments.has(d))])
        .filter(([, digits]) => digits.length)
        .map(([id, [digit]]) => {
            const {title, color} = $documentNodes.get(digit);
            return {id, witness_id: id, title, color};
        }));
    $effect(() => {
        witId = witnesses.some(w => w.id === witId) ? witId : witnesses[0]?.id;
    });
    $effect(() => {
        witId, reset(), clearSelected();
    });

    let pairs = $derived(scoreFilter ? $visiblePairs : ($allPairs, pairsOfDocuments($selectedDocuments)));
    let availableCats = $derived(CATS.filter(c => $docSetNumber.categories[c]));
    let digits = $derived(new Set((digitsOf.get(witId) ?? []).filter(d => $selectedDocuments.has(d))));

    let matches = $derived(pairs.reduce((m, p) => (link(m, p.id_1, p.id_2, p.digit_2), link(m, p.id_2, p.id_1, p.digit_1), m), new Map()));
    let catImgs = $derived(new Set(pairs.filter(p => pairCats(p).some(c => cats.has(c))).flatMap(p => [p.id_1, p.id_2])));
    let base = $derived([...digits]
        .flatMap(d => $documentNodes.get(d)?.images ?? [])
        .map(img => ({img, wits: [...(matches.get(img.id) ?? [])].map(([, d]) => witOfDigit.get(d))})));
    let rows = $derived(base
        .map(r => ({...r, n: r.wits.filter(w => !hidden.has(w)).length, inCat: !cats.size || catImgs.has(r.img.id)}))
        .filter(r => !hidden.size || r.n));
    let bars = $derived(rows.reduce((b, r) => (b[bucket(r.n)].total++, b[bucket(r.n)].part += r.inCat, b),
        Array.from({length: MAX + 1}, (_, i) => ({key: i, total: 0, part: 0, label: label(i)})))
        .map(b => ({...b, title: barTitle(b.total, b.part, b.key)})));
    let matchedWits = $derived(witnesses.filter(w => base.some(r => r.wits.includes(w.id))));
    let shown = $derived(rows.filter(r => r.inCat && (!buckets.size || buckets.has(bucket(r.n)))));

    let pairCounts = $derived(pairs
        .filter(p => digits.has(p.digit_1) || digits.has(p.digit_2))
        .reduce((c, p) => (pairCats(p).forEach(k => c[k] = (c[k] ?? 0) + 1), c), {}));

    async function deletePairs() {
        const ids = [...$selected];
        const images = ids.map(img => ({img, title: $imageNodes.get(img)?.title}));
        if (!ids.length || !await showMessage(`${ids.length} ${i18n("confirmDelete", t)}`, i18n("confirm"), true, images)) return;
        if (!await sendTo(`${appName}/similarity/delete-matches`, {q_imgs: ids})) return;
        removeImages(ids);
        clearSelected();
    }

</script>

<div class="level mb-4">
    <div class="level-left">
        <div class="level-item buttons mb-0">
            {#each ["images", "pairs"] as v}
                <button class="button is-small is-flex-grow-1" class:is-link={$view === v} class:is-contrasted={$view !== v}
                        onclick={() => view.set(v)}>{i18n(v, t)}</button>
            {/each}
        </div>
        <div class="level-item">
            <InputToggle start={scoreFilter} buttonDisplay={true} toggleLabel={i18n("scoreFilter", t)} on:updateChecked={e => scoreFilter = e.detail}/>
        </div>
    </div>
</div>

{#if $view === "pairs"}
    <DocumentPairs {documentSetStore} {pairs} {witnesses} {witOfDigit}/>
{:else}
    <div class="level-left is-flex is-justify-content-space-between mb-4">
        <div class="mr-3" style="width: 25rem">
            {#key witnesses.map(w => w.id).join()}
                <InputDropdown multiple={false} start={[witId]}
                               choicesItems={witnesses.map(w => ({value: w.id, label: w.title, prefix: dot(w.color), prefixType: "text"}))}
                               on:updateValues={e => witId = e.detail[0] ?? witId}/>
            {/key}
        </div>
        <div class="is-flex is-align-items-center" style="gap: 2rem;">
            <HistogramFilter {bars} selected={buckets} toggle={i => buckets = toggle(buckets, i)}/>
            <CategoryFilter categories={availableCats} counts={pairCounts} selected={cats} toggle={toggleCat}/>
            <div class="is-center">
                <p class="is-size-7 has-text-grey">{i18n("inPairs", t)}</p>
                <p class="title is-6">{shown.length} / {base.length}</p>
            </div>
            {#if isSuperuser}
                <span title={i18n($selected.size ? "deletePairs" : "selectToDelete", t)}>
                    <button class="button is-small tag is-danger is-center mx-4 m-0 has-text-light"
                            disabled={!$selected.size} onclick={deletePairs}>
                        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 448 512">
                            <path fill="currentColor" d="M135.2 17.7L128 32 32 32C14.3 32 0 46.3 0 64S14.3 96 32 96l384 0c17.7 0 32-14.3 32-32s-14.3-32-32-32l-96 0-7.2-14.3C307.4 6.8 296.3 0 284.2 0L163.8 0c-12.1 0-23.2 6.8-28.6 17.7zM416 128L32 128 53.2 467c1.6 25.3 22.6 45 47.9 45l245.8 0c25.3 0 46.3-19.7 47.9-45L416 128z"/>
                        </svg>
                    </button>
                </span>
            {/if}
        </div>
    </div>

{#if !shown.length}
    <p class="has-text-grey is-size-7">{i18n("noImage", t)}</p>
{/if}

<div class="grid is-gap-2 mt-2">
    {#each shown as r, i (r.img.id)}
        <RegionCard item={r.img} index={i} copyable={true} height={96} selectionStore={localSelection} on:openModal={e => [modalIndex, modalOpen] = [e.detail.index ?? 0, true]}/>
    {/each}
</div>

<RegionModal items={shown.map(r => r.img)} bind:currentIndex={modalIndex} bind:open={modalOpen}>
    {#snippet children({ item: currentItem })}

            <RegionTabs item={currentItem}/>

            {/snippet}
</RegionModal>
{/if}
