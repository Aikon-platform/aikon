<script>
    import { refToIIIF } from "../../utils";

    ////////////////////////////////////////

    /** @type {string} */
    export let mainImg;

    const mainImgHref = refToIIIF(mainImg);

</script>

<div>
    <div class="is-flex is-justify-content-center is-align-items-center">
        <img src={mainImgHref}
             alt="Main view of region {mainImg}"
        >
    </div>
</div>

<style>
    img {
        object-fit: contain;
        max-height: 80%;
        max-width: 80%;
    }
</style>
