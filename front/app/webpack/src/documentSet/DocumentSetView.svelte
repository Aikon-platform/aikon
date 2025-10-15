<script>
    import Layout from '../Layout.svelte';

    export let docSet;
    console.log(docSet);
</script>

<Layout>
    <div slot="sidebar">
        <div class="p-4">
            <h3 class="title is-5">{docSet.title}</h3>
        </div>
    </div>

    <div slot="content">
        <div class="p-4">
        </div>
    </div>
</Layout>
