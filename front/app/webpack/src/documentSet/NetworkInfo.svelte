<script>
    import {appLang} from "../constants.js";

    export let activeTab = 0;
    export let documentSetStore;
    const { imageStats, documentStats, docPairStats } = documentSetStore;

    $: currentStats = activeTab === 0 ? imageStats : activeTab === 1 ? documentStats : docPairStats;
</script>

<div class="level has-text-centered">
    <div class="level-item">
        <div>
            <p class="heading">{appLang === "en" ? "Nodes" : "Nœuds"}</p>
            <p class="title is-5">{currentStats.count || 0}</p>
        </div>
    </div>
    <div class="level-item">
        <div>
            <p class="heading">{appLang === 'en' ? 'Edges' : 'Liens'}</p>
            <p class="title is-5">{currentStats.links || 0}</p>
        </div>
    </div>
    <div class="level-item">
        <div>
            <p class="heading">Clusters</p>
            <p class="title is-5">{currentStats.clusters || 0}</p>
        </div>
    </div>
    <div class="level-item">
        <div>
            <p class="heading">{appLang === 'en' ? 'Connectivity' : 'Connectivité'}</p>
            <p class="title is-5">{currentStats.connectivity || 0}</p>
        </div>
    </div>
</div>
