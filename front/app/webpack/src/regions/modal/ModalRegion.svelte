<script>
    import { refToIIIF } from "../../utils";

    ////////////////////////////////////////

    /** @type {string} */
    export let mainImg;

    const mainImgHref = refToIIIF(mainImg);

</script>

<div class="img-wrapper is-flex is-justify-content-center is-align-items-center">
    <img src={mainImgHref}
         alt="Main view of region {mainImg}"
    >
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
