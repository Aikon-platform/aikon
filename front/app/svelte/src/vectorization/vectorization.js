import SvgDisplay from "./SvgDisplay.svelte";

const app = new SvgDisplay({
    target: document.getElementById("editing-tool"),
    props: {
        //appel des variables
        svg,  // eslint-disable-line
        backgroundImage,  // eslint-disable-line
    }
});
export default app;
