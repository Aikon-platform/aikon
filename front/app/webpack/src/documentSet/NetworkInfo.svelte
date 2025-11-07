<script>
    import {appLang} from "../constants.js";

    export let activeTab = 0;
    export let documentSetStore;
    const { docSetStats } = documentSetStore;
</script>

<div class="level has-text-centered">
    <div class="level-item">
        <div>
            <p class="heading">{appLang === "en" ? "Nodes" : "Nœuds"}</p>
            <p class="title is-5">{$docSetStats.stats[activeTab].nodes}</p>
        </div>
    </div>
    <div class="level-item">
        <div>
            <p class="heading">{appLang === 'en' ? 'Edges' : 'Liens'}</p>
            <p class="title is-5">{$docSetStats.stats[activeTab].links}</p>
        </div>
    </div>
    <div class="level-item">
        <div>
            <p class="heading">Clusters</p>
            <p class="title is-5">0</p>
        </div>
    </div>
    <div class="level-item">
        <div>
            <p class="heading">{appLang === 'en' ? 'Connectivity' : 'Connectivité'}</p>
            <p class="title is-5">0</p>
        </div>
    </div>
</div>
