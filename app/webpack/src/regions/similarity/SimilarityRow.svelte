<script>
    import { getContext } from 'svelte';
    import { appLang } from "../../constants";
    import { manifestToMirador, refToIIIF } from "../../utils.js";
    export let qImg;
    const [wit, digit, canvas, xyhw] = qImg.split('.')[0].split('_');
    const manifest = getContext('manifest');

    function addMatch() {
        console.log('Add match');
        // get input value
        // check if value is correctly formatted


        // TODO send request to add region pair record
        // TODO django side, check if region ref is correctly formatted + correspond to existing wit+digit
        // TODO django side, check if region pair already exists
        // TODO django side, check if digit has already regions, if not create one?
        // TODO django side, create region pair record (if 2 images has been paired, add user id to category x)
        // TODO if successful add region to comparedRegions (if not already the case)
        // TODO if successful select region in selectedRegions (if not already the case)
        // TODO if successful display new similar regions
        // TODO if unsuccessful display error message + do not show new similar regions
    }

    function noMatch() {
        // TODO
        console.log('No match');
    }
</script>

<tr>
    <th class="is-3 center-flex is-narrow" style="width: 260px">
        <div class="content-wrapper py-5">
            <a class="tag px-2 py-1 mb-2 is-rounded is-hoverable" href="{manifestToMirador(manifest, parseInt(canvas))}" target="_blank">
                <i class="fa-solid fa-pen-to-square"></i>
                Page {parseInt(canvas)}
            </a>

            <!--TODO make image copyable-->
            <img src="{refToIIIF(qImg, 'full', '250,')}" alt="Query region" class="mb-3 card">


            <div class="new-similarity control pt-2 is-center">
                <div class="tags has-addons" style="flex-wrap: nowrap">
                    <input class="input is-small tag" type="text"
                           placeholder="{appLang === 'en' ? 'Add new match' : 'Ajouter une correpondance'}"
                    />
                    <button class="button is-small tag is-link is-center">
                        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 448 512">
                            <path fill="currentColor" d="M256 80c0-17.7-14.3-32-32-32s-32 14.3-32 32l0 144L48 224c-17.7 0-32 14.3-32 32s14.3 32 32 32l144 0 0 144c0 17.7 14.3 32 32 32s32-14.3 32-32l0-144 144 0c17.7 0 32-14.3 32-32s-14.3-32-32-32l-144 0 0-144z"/>
                        </svg>
                    </button>
                </div>
                <button class="button is-small tag is-link is-center m-0" on:click={noMatch}
                        title="{appLang === 'en' ? 'No match for this region' : 'Aucune correspondance'}">
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 384 512">
                        <path fill="currentColor" d="M376.6 84.5c11.3-13.6 9.5-33.8-4.1-45.1s-33.8-9.5-45.1 4.1L192 206 56.6 43.5C45.3 29.9 25.1 28.1 11.5 39.4S-3.9 70.9 7.4 84.5L150.3 256 7.4 427.5c-11.3 13.6-9.5 33.8 4.1 45.1s33.8 9.5 45.1-4.1L192 306 327.4 468.5c11.3 13.6 31.5 15.4 45.1 4.1s15.4-31.5 4.1-45.1L233.7 256 376.6 84.5z"/>
                    </svg>
                </button>
            </div>
        </div>
    </th>
    <td class="p-5 is-fullwidth">
        <div class="fixed-grid has-5-cols">
            <div class="grid is-gap-2">
                <slot/>
            </div>
        </div>
    </td>
</tr>

<style>
    .new-similarity {
        display: flex;
        gap: 0.5em;
    }
</style>
