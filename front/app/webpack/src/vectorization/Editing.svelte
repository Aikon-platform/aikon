<script>
    import SVGDisplay from './SVGDisplay.svelte';
    import SideBar from './SideBar.svelte';

    let selectedElement = null;

    function handleElementSelect(event) {
        selectedElement = event.detail;
    }

    function updateElement(event) {
        const { property, value } = event.detail;
        if (selectedElement) {
            if (property === 'remove') {
                selectedElement.remove();
                selectedElement = null;
            } else {
                selectedElement.setAttribute(property, value);
            }
        }
    }
</script>

<main>
    <SVGDisplay on:elementSelect={handleElementSelect} />
    <SideBar on:updateElement={updateElement} />
</main>

<style>
    main {
        display: flex;
    }
</style>
