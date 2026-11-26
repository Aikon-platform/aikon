<script>
    import Loading from "../Loading.svelte";
    import {i18n, refToIIIF, withLoading} from "../utils.js";
    import {appLang, appName} from "../constants.js";

    const t = {
        intro: {
            en: "Similarities were computed on regions that may have been corrected since. This step carries each pair over to the current regions of the document set digitizations:",
            fr: "Les similarités ont été calculées sur des régions qui ont pu être corrigées depuis. Cette tâche réaligne chaque paire d'images sur les régions actuelles des numérisations du set de documents :"
        },
        steps: {
            en: [
                "<code>equivalent</code> Slightly modified region: the pair is updated and keeps its score",
                "<code>remapped</code> Significantly modified region: the pair is updated, but its score is no longer reliable",
                "<code>split</code> Region divided into several: the pair is duplicated for each new region",
                "<code>merge</code> Regions merged into one: their pairs are combined, keeping the assigned category",
                "<code>orphan</code> Region with no match: its pairs are deleted",
                "<code>self</code> Pair now linking a region to itself: deleted",
            ],
            fr: [
                "<code>equivalent</code> Région légèrement modifiée : la paire est mise à jour et garde son score",
                "<code>remapped</code> Région nettement modifiée : la paire est mise à jour, mais son score n'est plus fiable",
                "<code>split</code> Région divisée en plusieurs : la paire est dupliquée pour chaque nouvelle région",
                "<code>merge</code> Régions fusionnées en une seule : leurs paires sont réunies, en gardant la catégorie attribuée",
                "<code>orphan</code> Région sans équivalent : ses paires sont supprimées",
                "<code>self</code> Paire reliant désormais une région à elle-même : supprimée",
            ]
        },
        run: {en: "Preview the changes", fr: "Prévisualiser les changements"},
        noSet: {en: "Select a document set first", fr: "Sélectionnez d'abord un set de documents"},
        title: {en: "Preview of document set #{id}: {d} digitizations, {p} pairs", fr: "Aperçu du set de documents #{id} : {d} numérisations, {p} paires"},
        images: {en: "Regions in pairs", fr: "Régions des paires"},
        changes: {en: "Pairs", fr: "Paires"},
        hashes: {en: "Similarity computations previously applied on the document set", fr: "Calculs de similarité appliqués auparavant sur le set de documents"},
        noHash: {en: "no hash", fr: "sans hash"},
        advised: {en: "advised", fr: "conseillé"},
        lost: {en: "{n} pairs of category 1 (exact match) will be deleted (orphan)", fr: "{n} paires de catégorie 1 (correspondance exacte) seront supprimées (orphan)"},
        next: {en: "Submit to apply these changes, then:", fr: "Validez pour appliquer ces changements, puis :"},
        correct: {en: "Check the remapped pairs in the {pairs}", fr: "Vérifiez les paires remapped dans la {pairs}"},
        rescore: {en: "{relaunch} to recompute the score of remapped pairs", fr: "{relaunch} pour recalculer le score des paires remapped"},
        pairsView: {en: "pairs view", fr: "vue des paires"},
        relaunch: {en: "Relaunch the similarity", fr: "Relancez la similarité"},
        skipped: {en: "skipped (whole page or digitization without regions)", fr: "ignorées (page entière ou numérisation sans régions)"},
        count: {en: "distinct regions", fr: "régions distinctes"},
        unchanged: {en: "unchanged", fr: "inchangées"},
        equivalent: {en: "slightly modified", fr: "légèrement modifiées"},
        remapped: {en: "significantly modified", fr: "nettement modifiées"},
        split: {en: "divided", fr: "divisées"},
        orphan: {en: "no match", fr: "sans correspondance"},
        updates: {en: "updated", fr: "mises à jour"},
        insertions: {en: "created by split", fr: "créées par division"},
        deletions: {en: "deleted (orphan, merge, self)", fr: "supprimées (orphan, merge, self)"},
        orphans: {en: "deleted by category", fr: "supprimées par catégorie"},
        conflicts: {en: "conflicting categories (left as is)", fr: "catégories contradictoires (inchangées)"},
        merge: {en: "inherited categories", fr: "catégories héritées"},
    };
    const fmt = (key, vars) => Object.entries(vars).reduce((s, [k, v]) => s.replace(`{${k}}`, v), i18n(key, t));
    const steps = t.steps[appLang] ?? t.steps.en;

    let preview = null, error = "";

    async function run() {
        const dsid = document.getElementById("id_document_set")?.value;
        if (!dsid) return [preview, error] = [null, i18n("noSet", t)];
        const response = await withLoading(() => fetch(`/${appName}/document-set/${dsid}/remap-preview`));
        const data = await response.json().catch(() => ({error: response.statusText}));
        [preview, error] = response.ok ? [{...data, id: dsid}, ""] : [null, data.error];
    }

    $: advised = preview?.hashes.find(h => h.parameters)?.hash;
    const link = (href, label) => href ? `<a href="${href}" target="_blank">${label}</a>` : label;
    $: pairsLink = preview && link(preview.links.pairs, i18n("pairsView", t));
    $: relaunchLink = preview && link(preview.links.similarity[advised], i18n("relaunch", t));
</script>

<Loading/>

<div class="content">
    <p class="mb-1">{i18n("intro", t)}</p>
    <ul class="mt-0">
        {#each steps as step}
            <li>{@html step}</li>
        {/each}
    </ul>
</div>

<button type="button" class="button is-link is-light" on:click={run}>{i18n("run", t)}</button>

{#if error}
    <article class="message is-danger mt-4">
        <div class="message-body">{error}</div>
    </article>
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
                        {#each (key === "images" ?
                            Object.keys(values) :
                            ["updates", "insertions", "deletions", "orphans", "inherited", "conflicts"]) as k}
                            <tr>
                                <td><code>{k}</code> {i18n(k, t)}</td>
                                <td class="has-text-right">
                                    {typeof values[k] === "object" ?
                                        Object.entries(values[k]).map(([c, n]) => `${c}: ${n}`).join(", ") || "–"
                                        : values[k]
                                    }
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
