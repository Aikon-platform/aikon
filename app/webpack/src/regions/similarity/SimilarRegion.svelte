<script>
    import { fade } from 'svelte/transition';
    import {refToIIIF} from "../../utils.js";
    import { similarityStore } from './similarityStore.js';

    // export let appLang = 'en';
    export let sImg; // 'wit42_img42_0125_1025,1032,417,981.jpg'
    // export let score;

    const [wit, digit, canvas, xyhw] = sImg.split('_');
    const coord = xyhw.replace('.jpg', '');
    const img = `${wit}_${digit}_${canvas}`;
</script>

<style>
    .overlay {
        font-size: 75%;
    }
    figure {
        transition: outline 0.1s ease-out;
        outline: 0 solid var(--bulma-link);
    }
    .region {
        cursor: pointer;
        position: relative;
    }
</style>

<div class="region image is-center" transition:fade={{ duration: 500 }}>
    <figure class="image card" tabindex="-1">
        <img src="{refToIIIF(img, coord, '160,')}" alt="Similar region"/>
        <div class="overlay is-center">
            <span class="overlay-desc">{similarityStore.getRegionsInfo(`${wit}_${digit}`).title}</span>
        </div>
    </figure>
    <!--TODO add category button-->
</div>
