<script>
    import { refToIIIF } from "../../utils";

    import Region from "../Region.svelte";

    ////////////////////////////////////////

    /** @type {string} */
    export let mainImg;
    export let mainImgItem;

    console.log(">>>", mainImgItem);

    const mainImgHref = refToIIIF(mainImg);

</script>

<!--
<div class="img-wrapper is-flex is-justify-content-center is-align-items-center">
    <img src={mainImgHref}
         alt="Main view of region {mainImg}"
    >
</div>
-->
<div class="img-wrapper">
    <Region item={mainImgItem}
            displayType="full"
    ></Region>
</div>

<style>
    .img-wrapper {
        height: 100%;
        width: 100%;
    }
    img {
        height: 100%;
    }
</style>
