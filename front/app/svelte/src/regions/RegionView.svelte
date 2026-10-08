<script>
    import { setContext } from "svelte";
    import { RegionItem } from "../regions/types.js";
    import { loading } from "../utils.js";
    import RegionTabs from "../regions/modal/RegionTabs.svelte";
    import Modal from "../Modal.svelte";
    import Loading from "../Loading.svelte";

    export let imgRef;

    const item = RegionItem.fromImg(imgRef);
    let activeTab = new URLSearchParams(window.location.search).get("tab") ?? "region";

    setContext("setModalAnchor", (kept) => window.location.assign(`${kept.viewUrl}?tab=${activeTab}`));

    $: {
        const url = new URL(window.location);
        url.searchParams.set("tab", activeTab);
        window.history.replaceState({}, "", url);
    }
</script>

<Loading visible={$loading}/>

<Modal/>

<div class="container is-relative is-flex is-flex-direction-column" style="height: calc(100vh - 7rem)">
    <RegionTabs {item} bind:activeTab showNav={false}/>
</div>
