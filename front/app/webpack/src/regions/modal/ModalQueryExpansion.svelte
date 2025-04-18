<script>
    import { refToIIIF } from "../../utils";
    import { appLang } from "../../constants.js";

    import SimilarityRow from "../similarity/SimilarityRow.svelte";

    ////////////////////////////////////////

    /** @type {string} */
    export let mainImg;

    const mainImgHref = refToIIIF(mainImg);


</script>

<div>
    <SimilarityRow qImg={mainImg}></SimilarityRow>
</div>

<style></style>
