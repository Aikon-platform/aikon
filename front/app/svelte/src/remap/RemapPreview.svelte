<script>
    import Loading from "../Loading.svelte";
    import {i18n, refToIIIF, withLoading} from "../utils.svelte.js";
    import {appLang, appName} from "../constants.js";

    const t = {
        intro: {
            en: "Remaps the pairs of the document set onto its regions as corrected in the annotation server (which is never modified):",
            fr: "Réassigne les paires du set de documents à ses régions telles que corrigées dans le serveur d'annotations (qui n'est jamais modifié) :"
        },
        steps: {
            en: [
                "an image whose bbox overlaps a corrected region (IoU ≥ 0.5 or IoA ≥ 0.8) is renamed after it, or duplicated if it overlaps several regions (split)",
                "pairs whose region changed significantly (IoU ≤ 0.8) become \"remapped\": their score is kept but must be recomputed",
                "pairs collapsing onto an existing pair are merged into it, keeping its score and type",
                "pairs with an image matching no region (orphan) are deleted, as well as pairs of a region with itself",
                "categories are then aligned across similarity hashes",
            ],
            fr: [
                "une image dont la bbox recouvre une région corrigée (IoU ≥ 0,5 ou IoA ≥ 0,8) est renommée d'après elle, ou dupliquée si elle en recouvre plusieurs (division)",
                "les paires dont la région a nettement changé (IoU ≤ 0,8) deviennent « réassignées » : leur score est conservé mais doit être recalculé",
                "les paires fusionnant avec une paire existante y sont intégrées, qui garde son score et son type",
                "les paires dont une image ne correspond à aucune région (orpheline) sont supprimées, ainsi que les paires d'une région avec elle-même",
                "les catégories sont ensuite alignées entre les hashs de similarité",
            ]
        },
        run: {en: "Preview the remap", fr: "Prévisualiser la réassignation"},
        noSet: {en: "Select a document set first", fr: "Sélectionnez d'abord un set de documents"},
        title: {en: "Preview of document set #{id}: {d} digitizations, {p} pairs", fr: "Aperçu du set de documents #{id} : {d} numérisations, {p} paires"},
        images: {en: "Images", fr: "Images"},
        changes: {en: "Pairs", fr: "Paires"},
        hashes: {en: "Similarity computations previously applied on the document set", fr: "Calculs de similarité appliqués auparavant sur le set de documents"},
        noHash: {en: "no hash", fr: "sans hash"},
        advised: {en: "advised", fr: "conseillé"},
        lost: {en: "{n} pairs of category 1 (exact match) will be deleted", fr: "{n} paires de catégorie 1 (correspondance exacte) seront supprimées"},
        next: {en: "Submit to apply these changes, then:", fr: "Validez pour appliquer ces changements, puis :"},
        correct: {en: "Correct the remapped pairs in the {pairs}", fr: "Corrigez les paires réassignées dans la {pairs}"},
        rescore: {en: "{relaunch} computation to rescore pairs that were remapped", fr: "{relaunch} le calcul pour attribuer de nouveaux scores aux paires réassignées"},
        pairsView: {en: "pairs view", fr: "vue des paires"},
        relaunch: {en: "Relaunch similarity", fr: "Relancer la similarité"},
        distinct_images: {en: "distinct images", fr: "images distinctes"},
        unchanged: {en: "unchanged", fr: "inchangées"},
        equivalent: {en: "renamed, score still valid", fr: "renommées, score toujours valide"},
        remapped: {en: "renamed, score to recompute", fr: "renommées, score à recalculer"},
        split: {en: "split onto several regions", fr: "divisées en plusieurs régions"},
        orphan: {en: "orphans (no matching region)", fr: "orphelines (aucune région correspondante)"},
        skipped: {en: "skipped (page-level or no indexed region)", fr: "ignorées (page entière ou aucune région indexée)"},
        updates: {en: "updated", fr: "modifiées"},
        insertions: {en: "inserted (splits)", fr: "insérées (divisions)"},
        deletions: {en: "deleted (orphans, merged, self-pairs)", fr: "supprimées (orphelines, fusionnées, auto-paires)"},
        orphans_by_category: {en: "orphans deleted by category", fr: "orphelines supprimées par catégorie"},
        inherited: {en: "pairs inheriting a category", fr: "paires héritant d'une catégorie"},
        conflicts: {en: "pairs with conflicting categories (left unchanged)", fr: "paires aux catégories contradictoires (inchangées)"},
    };
    const fmt = (key, vars) => Object.entries(vars).reduce((s, [k, v]) => s.replace(`{${k}}`, v), i18n(key, t));
    const steps = t.steps[appLang] ?? t.steps.en;

    let preview = $state(null), error = $state("");

    async function run() {
        const dsid = document.getElementById("id_document_set")?.value;
        if (!dsid) return [preview, error] = [null, i18n("noSet", t)];
        const response = await withLoading(() => fetch(`/${appName}/document-set/${dsid}/remap-preview`));
        const data = await response.json().catch(() => ({error: response.statusText}));
        [preview, error] = response.ok ? [{...data, id: dsid}, ""] : [null, data.error];
    }

    let advised = $derived(preview?.hashes.find(h => h.parameters)?.hash);
    const link = (href, label) => href ? `<a href="${href}" target="_blank">${label}</a>` : label;
    let pairsLink = $derived(preview && link(preview.links.pairs, i18n("pairsView", t)));
    let relaunchLink = $derived(preview && link(preview.links.similarity[advised], i18n("relaunch", t)));
</script>

<Loading/>

<div class="content">
    <p class="mb-1">{i18n("intro", t)}</p>
    <ul class="mt-0">{#each steps as step}<li>{step}</li>{/each}</ul>
</div>

<button type="button" class="button is-link is-light" onclick={run}>{i18n("run", t)}</button>

{#if error}
    <article class="message is-danger mt-4"><div class="message-body">{error}</div></article>
{/if}

{#if preview}
    <h3 class="subtitle mt-5">
        {fmt("title", {id: preview.id, d: preview.digitizations, p: preview.pairs})}
    </h3>

    <div class="columns px-2">
        {#each [["images", preview.stats], ["changes", preview]] as [key, values]}
            <div class="column">
                <table class="table is-narrow is-fullwidth box p-1 pl-2">
                    <thead><tr><th colspan="2">{i18n(key, t)}</th></tr></thead>
                    <tbody>
                        {#each (key === "images" ? Object.keys(values) : ["updates", "insertions", "deletions", "orphans_by_category", "inherited", "conflicts"]) as k}
                            <tr>
                                <td>{i18n(k, t)}</td>
                                <td class="has-text-right">
                                    {typeof values[k] === "object" ? Object.entries(values[k]).map(([c, n]) => `${c}: ${n}`).join(", ") || "–" : values[k]}
                                </td>
                            </tr>
                        {/each}
                    </tbody>
                </table>
            </div>
        {/each}
    </div>

    {#if preview.lost.length}
        <article class="message is-warning">
            <div class="message-header"><p>{fmt("lost", {n: preview.lost.length})}</p></div>
            <div class="message-body fixed-grid has-4-cols">
                <div class="grid is-gap-2">
                    {#each preview.lost as {id, img_1, img_2}}
                        <div class="cell is-flex is-gap-1" title="#{id}">
                            {#each [img_1, img_2] as img}
                                <figure class="image is-64x64 card m-0">
                                    <img src={refToIIIF(img, null, "96,")} alt={img}/>
                                </figure>
                            {/each}
                        </div>
                    {/each}
                </div>
            </div>
        </article>
    {/if}

    <article class="message is-info">
        <div class="message-body content">
            <p class="mb-1">{i18n("next", t)}</p>
            <ol class="mt-0">
                <li>{@html fmt("correct", {pairs: pairsLink})}</li>
                <li>{@html fmt("rescore", {relaunch: relaunchLink})}</li>
            </ol>
            <!-- <h4 class="is-size-6 has-text-weight-semibold">{i18n("hashes", t)}</h4>
            <ul class="mt-1 mb-0">
                {#each preview.hashes as {hash, pairs, parameters}}
                    <li class="is-size-7">
                        <code>{hash ?? i18n("noHash", t)}</code>
                        {pairs} {i18n("pairs", t)}
                        {#if parameters}
                            <span class="has-text-grey ml-1">{JSON.stringify(parameters)}</span>
                        {/if}
                        {#if hash !== advised && preview.links.similarity[hash]}
                            <a class="ml-1" href={preview.links.similarity[hash]} target="_blank">
                                {i18n("relaunch", t)}
                            </a>
                        {/if}
                    </li>
                {/each}
            </ul> -->
        </div>
    </article>
{/if}
