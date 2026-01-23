import SvgDisplay from './SvgDisplay.svelte';

const app = new SvgDisplay({
    target: document.getElementById('editing-tool'),
    props: {
        //appel des variables
        svg: svg,
        backgroundImage: backgroundImage,
    }
});
export default app;
