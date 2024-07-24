<script>
    import { appLang } from "../constants.js";
    // import { selectionStore } from "./selectionStore.js";
    // const { selected } = selectionStore;
    import SelectionFooter from "./SelectionFooter.svelte";

    export let isRegion = false;
    export let selectionLength = false;
    // $: selectionLength = Object.keys($selected(isRegion)).length;
</script>

<div id="selection-modal" class="modal fade" tabindex="-1" aria-labelledby="selection-modal-label" aria-hidden="true">
    <div class="modal-background"/>
    <div class="modal-content">
        <div class="modal-card-head media mb-0">
            <div class="title is-4 mb-0 media-content">
                <i class="fa-solid fa-book-bookmark"></i>
                {appLang === 'en' ? 'Selected regions' : 'Regions sélectionnées'}
                ({selectionLength})
            </div>
            <button class="delete media-left" aria-label="close"/>
        </div>
        <section class="modal-card-body">
            <slot/>
        </section>
        <SelectionFooter {isRegion}/>
    </div>
</div>
