<script>
    import {onDestroy} from "svelte";
    import {writable, get} from "svelte/store";
    import InputDropdown from "../../ui/InputDropdown.svelte";
    import Pagination from "../../Pagination.svelte";
    import RegionCard from "../../regions/RegionCard.svelte";
    import RegionModal from "../../regions/modal/RegionModal.svelte";
    import RegionTabs from "../../regions/modal/RegionTabs.svelte";
    import PairCategoryToolbar from "../../regions/similarity/PairCategoryToolbar.svelte";
    import CategoryFilter from "../sidebar/CategoryFilter.svelte";
    import HistogramFilter from "./HistogramFilter.svelte";
    import {typeInfo} from "../../regions/similarity/similarityType.js";
    import {pairCats} from "../documentSetStore.js";
    import {i18n, initPagination, pageUpdate, shorten, syncStoreWithURL} from "../../utils.js";
    import {pageSize} from "../../constants.js";
    import DownloadPng from "../../ui/DownloadPng.svelte";

    export let documentSetStore;
    /** pairs already filtered by selected documents (and score if enabled) */
    export let pairs;
    /** [{id, title, color}] */
    export let witnesses;
    /** Map<digitId, witnessId> */
    export let witOfDigit;

    const {imageNodes, patchPairs} = documentSetStore;

    const CATS = [1, 2, 3, 5];
    const t = {
        witnesses: {en: "Witnesses (both images)", fr: "Témoins (deux images)"},
        noPair: {en: "No pair for these filters", fr: "Aucune paire pour ces filtres"},
        bar: {en: "{s} / {c} {type} pair(s). Click to show / hide", fr: "{s} / {c} paire(s) {type}. Cliquer pour afficher / masquer"},
    };

    const unsubs = [];
    const [wits, cats, types] = ["pwit", "pcat", "ptype"].map(param => {
        const s = writable(new Set());
        unsubs.push(s.subscribe(syncStoreWithURL(s, param, "set")));
        return s;
    });
    onDestroy(() => unsubs.forEach(u => u()));

    const currentPage = writable(1);
    initPagination(currentPage, "pp");
    const pager = {currentPage, handlePageUpdate: n => pageUpdate(n, currentPage, "pp")};

    const setFilter = (store, s) => (store.set(s), pager.handlePageUpdate(1));
    const toggle = (store, v) => setFilter(store, (s => (s.delete(v) || s.add(v), s))(new Set(get(store))));
    const setWits = ids => ids.join() !== [...$wits].join() && setFilter(wits, new Set(ids));
    const count = (ps, keysOf) => ps.reduce((c, p) => (keysOf(p).forEach(k => c[k] = (c[k] ?? 0) + 1), c), {});
    const dot = color => `<i class="fa-solid fa-circle" style="color: ${color}"></i>`;
    const typeIcon = type => `<span class="icon is-small is-align-self-center" title="${typeInfo[type].title}">${typeInfo[type].svg}</span>`;
    const barTitle = (c, s, type) => i18n("bar", t).replace("{s}", s).replace("{c}", c).replace("{type}", typeInfo[type].title);

    let modalOpen = false, modalIndex = 0;

    $: inScope = pairs.filter(p => pairCats(p).some(c => CATS.includes(c))
        && (!$wits.size || ($wits.has(witOfDigit.get(p.digit_1)) && $wits.has(witOfDigit.get(p.digit_2)))));
    $: catCounts = count(inScope, pairCats);
    $: inCat = inScope.filter(p => !$cats.size || pairCats(p).some(c => $cats.has(c)));
    $: inCatCounts = count(inCat, p => [p.similarityType]);
    $: bars = Object.entries(count(inScope, p => [p.similarityType])).map(([type, total]) => ({
        key: +type, total, part: inCatCounts[type] ?? 0, label: typeIcon(type), title: barTitle(total, inCatCounts[type] ?? 0, type)
    }));
    $: filtered = inCat.filter(p => !$types.size || $types.has(p.similarityType));
    $: pagePairs = filtered.slice(($currentPage - 1) * pageSize, $currentPage * pageSize);
    /** images of the page, the partner of image `i` being `i ^ 1` */
    $: pageImgs = pagePairs.flatMap(p => [p.id_1, p.id_2]);
</script>

<div class="level-left is-flex is-justify-content-space-between">
    <div class="mr-3" style="width: 30rem">
        <InputDropdown multiple={true} start={[...$wits]} placeholder={i18n("witnesses", t)} lightDisplay={true}
                       choicesItems={witnesses.map(w => ({value: w.id, label: shorten(w.title), prefix: `${dot(w.color)} #${w.id}`, prefixType: "text"}))}
                       on:updateValues={e => setWits(e.detail)}/>
    </div>
    <div class="is-flex is-align-items-center" style="gap: 2rem;">
        <HistogramFilter {bars} selected={$types} toggle={type => toggle(types, type)}/>
        <CategoryFilter categories={CATS.filter(c => catCounts[c])} counts={catCounts} selected={$cats} toggle={c => toggle(cats, c)}/>
    </div>
</div>

<Pagination store={pager} nbOfItems={filtered.length}/>

{#if !filtered.length}
    <p class="has-text-grey is-size-7">{i18n("noPair", t)}</p>
{/if}

<div class="grid is-gap-2" style="--bulma-grid-column-min: 20rem">
    {#each pagePairs as p, i (p)}
        <div class="cell box p-2 mb-0">
            <div class="is-flex is-justify-content-center is-gap-1">
                {#each [p.id_1, p.id_2] as id, k}
                    <RegionCard item={$imageNodes.get(id)} index={2 * i + k} height={96} selectable={false}
                                on:openModal={e => [modalIndex, modalOpen] = [e.detail.index, true]}/>
                {/each}
            </div>
            <div class="is-flex is-align-items-center is-justify-content-space-between mt-2">
                <div class="is-flex is-align-items-center is-gap-1 is-size-7">
                    <span class="icon-text">
                        {@html typeIcon(p.similarityType)}
                        <span>{typeInfo[p.similarityType].title}</span>
                    </span>
                    <span class="tag ml-4 mb-0">{p.score?.toFixed(2) ?? "–"}</span>
                </div>
                <PairCategoryToolbar qImg={p.id_1} sImg={p.id_2} category={p.category || null} isSelectedByUser={p.userMatch}
                                     similarityType={p.similarityType} onChange={category => patchPairs([{img_1: p.id_1, img_2: p.id_2, category}])}/>
            </div>
        </div>
    {/each}
</div>

<RegionModal items={pageImgs.map(id => $imageNodes.get(id))} bind:currentIndex={modalIndex} bind:open={modalOpen}>
    <svelte:fragment let:item let:index>
        <RegionTabs {item} comparison={pageImgs[index] && {qImg: pageImgs[index], sImg: pageImgs[index ^ 1]}} activeTab="similarity"/>
    </svelte:fragment>
</RegionModal>
