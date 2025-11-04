<script>
    import Region from "../Region.svelte";

    /** @typedef {import("../types.js").RegionItemType} RegionItemType */

    /** @type {RegionItemType} */
    export let mainImgItem;
</script>

<div class="img-wrapper">
    <Region item={mainImgItem} height="full"/>
</div>

<style>
    .img-wrapper {
        height: 100%;
        width: 100%;
    }
</style>
