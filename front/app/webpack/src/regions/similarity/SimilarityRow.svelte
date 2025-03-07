<script>
    import { getContext } from 'svelte';
    import { fade } from 'svelte/transition';
    import { similarityStore } from "./similarityStore.js";
    const { selectedRegions } = similarityStore;
    import { appLang, csrfToken } from "../../constants";
    import { manifestToMirador, refToIIIF, showMessage } from "../../utils.js";

    import SimilarityMatches from "./SimilarityMatches.svelte";
    import SimilarityMatchesSuggestions from "./SimilarityMatchesSuggestions.svelte";

    export let qImg;
    let sImg = "";
    const [wit, digit, canvas, xyhw] = qImg.split('.')[0].split('_');
    const manifest = getContext('manifest');
    const baseUrl = `${window.location.origin}${window.location.pathname}`;
    const currentPageId = window.location.pathname.match(/\d+/g).join('-');
    const error_name = appLang === "en" ? "Error" : "Erreur";

    $: sLen = $selectedRegions.hasOwnProperty(currentPageId) ? Object.values($selectedRegions[currentPageId]).length : 0;
    $: hasNoMatch = false; // TODO HERE FIND A WAY TO SET NO MATCH FOR THIS Q REGIONS

    function check_region_ref(region_ref) {
        region_ref = region_ref.replace('.jpg', '');
        const region_ref_regex = /^wit\d+_[a-zA-Z]{3}\d+_\d+_\d+,\d+,\d+,\d+$/;
        return region_ref_regex.test(region_ref);
    }

    async function addMatch() {
        if (!sImg || !check_region_ref(sImg)) {
            await showMessage(
                appLang === "en" ?
                    "Please insert a valid region reference to add a new match" :
                    "Veuillez insérer une référence de région valide pour ajouter une nouvelle correspondance",
                "Error");
            return;
        }

        try {
            const response = await fetch(`${baseUrl}add-region-pair`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify({
                    'q_img': qImg.replace('.jpg', ''),
                    's_img': sImg,
                })
            });

            if (!response.ok) {
                console.error(`Error: Network response was not ok`);
                await showMessage(
                    appLang === "en" ?
                        "Problem with network, match was not added" :
                        "Problème de réseau, la correspondance n'a pas été ajoutée",
                    error_name
                );
            }

            const data = await response.json();
            if (data.hasOwnProperty('error') || !data.hasOwnProperty('s_regions')){
                await showMessage(
                    appLang === "en" ?
                        `Request was unsuccessful, match was not added:<br>${data.error}` :
                        `La requête n'a pas abouti, la correspondance n'a pas été ajoutée :<br>${data.error}`,
                    error_name
                );
                return;
            }
            const regions = data.s_regions;
            similarityStore.addComparedRegions(regions)
            similarityStore.select(regions)

        } catch (error) {
            console.error('Error:', error);
            await showMessage(
                appLang === "en" ?
                    `An error has occurred, match was not added:<br>${error}` :
                    `Une erreur s'est produite, la correspondance n'a pas été ajoutée :<br>${error}`,
                error_name
            );
        }
    }

    async function noMatch() {
        const regions = Object.values($selectedRegions[currentPageId])[0];
        const confirmed = await showMessage(
            appLang === "en" ?
                `Do you confirm this region does not have any match in ${regions.title}?` :
                `Confirmez-vous que cette région n'a pas de correspondance dans ${regions.title} ?`,
            appLang === "en" ? "Confirm no match" : "Confirmer l'absence de correspondance",
            true
        );

        if (!confirmed) {
            return;
        }
        try {
            const response = await fetch(`${baseUrl}no-match`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify({
                    'q_img': qImg,
                    's_regions': regions.id,
                })
            });

            if (!response.ok) {
                console.error(`Error: Network response was not ok`);
                await showMessage(
                    appLang === "en" ? "Problem with network" : "Problème de réseau",
                    error_name
                );
            }

            similarityStore.select(regions)

        } catch (error) {
            console.error('Error:', error);
            await showMessage(
                appLang === "en" ?
                    `An error has occurred, request was unsuccessful:<br>${error}` :
                    `Une erreur s'est produite, la requête n'a pas abouti :<br>${error}`,
                error_name
            );
        }

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
                    <input bind:value={sImg} class="input is-small tag" type="text"
                           placeholder="{appLang === 'en' ? 'Add new match' : 'Ajouter une correspondance'}"
                    />
                    <button class="button is-small tag is-link is-center" on:click={addMatch}>
                        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 448 512">
                            <path fill="currentColor" d="M256 80c0-17.7-14.3-32-32-32s-32 14.3-32 32l0 144L48 224c-17.7 0-32 14.3-32 32s14.3 32 32 32l144 0 0 144c0 17.7 14.3 32 32 32s32-14.3 32-32l0-144 144 0c17.7 0 32-14.3 32-32s-14.3-32-32-32l-144 0 0-144z"/>
                        </svg>
                    </button>
                </div>
                <button id="no-match" class="button is-small tag is-danger is-center m-0 {sLen === 1 ? 'visible' : ''}"
                        on:click={noMatch} transition:fade={{ duration: 500 }}
                        title="{appLang === 'en' ? 'No match for this region in this witness' : 'Aucune correspondance de cette région pour ce témoin'}">
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 384 512">
                        <path fill="white" d="M376.6 84.5c11.3-13.6 9.5-33.8-4.1-45.1s-33.8-9.5-45.1 4.1L192 206 56.6 43.5C45.3 29.9 25.1 28.1 11.5 39.4S-3.9 70.9 7.4 84.5L150.3 256 7.4 427.5c-11.3 13.6-9.5 33.8 4.1 45.1s33.8 9.5 45.1-4.1L192 306 327.4 468.5c11.3 13.6 31.5 15.4 45.1 4.1s15.4-31.5 4.1-45.1L233.7 256 376.6 84.5z"/>
                    </svg>
                </button>
            </div>
        </div>
    </th>
    <td class="p-5 is-fullwidth">
        <div class="fixed-grid has-5-cols">
            <SimilarityMatches {qImg}></SimilarityMatches>
            <SimilarityMatchesSuggestions {qImg}></SimilarityMatchesSuggestions>
        </div>
    </td>
</tr>

<style>
    .new-similarity {
        display: flex;
        gap: 0.5em;
    }
    #no-match {
        opacity: 0;
        visibility: hidden;
        transition: opacity 0.3s ease-out, visibility 0.3s ease-out;
    }
    .visible {
        opacity: 1 !important;
        visibility: visible !important;
    }
</style>
