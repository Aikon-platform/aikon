<script>
    import {appLang} from "../constants.js";

    export let activeTab = 0;
    export let docSetStats;
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
            <p class="heading">{appLang === 'en' ? 'Links' : 'Liens'}</p>
            <p class="title is-5">{$docSetStats.stats[activeTab].links}</p>
        </div>
    </div>
</div>
