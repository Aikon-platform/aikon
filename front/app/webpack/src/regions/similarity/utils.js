import { appLang } from "../../constants.js";
import { similarityStore } from './similarityStore.js';

const { getRegionsInfo } = similarityStore;

/**
 * create a descripton to be displayed when hovering on a similarity image.
 * outside of `SimilarityMatches`, it is possible that the similarity's region (identified by `regionRef`) is not contained in `similarityStore.comparedRegions`, that contains metata om the regions. in that cxase, we fetch data from the backend.
 * @param {string} regionRef
 * @param {number} similarityType
 * @param {number?} score
 * @param {string} canvas
 * @param {string} baseUrl : window.location.origin
 * @param {string} path : pathname part of the url
 * @param {boolean} isPropagatedContext: is getDesc used in a descendant of `PropagatedMatches.svelte`
 * @param {boolean} displayScore: if false, no score info or similarityType will be displayed.
 * @returns {Promise<string>}
 *      if `!isPropagatedContext` the result could be synchronous, but
 *      it is returned as a promise to provide the same async interface
 *      for both branches
 */
export async function getDesc(regionRef, similarityType, score, canvas, baseUrl, path, isPropagatedContext= false, displayScore= true) {
    const scoreString = () =>
        displayScore
        ? `<b>${
            !isNaN(parseFloat(score)) && similarityType === 1
            ? `Score: ${score}`
            : similarityType === 2 && appLang === 'en'
            ? 'Manual similarity'
            : similarityType === 2 && appLang === 'fr'
            ? 'Correspondance manuelle'
            : similarityType === 3 && appLang === 'en'
            ? 'Propagated match'
            : 'Correspondance propagée'
        }</b>`
        : ``;
    const formatter = (title) =>
        `${title}<br>
        Page ${parseInt(canvas)}<br>
        ${scoreString()}`;
    return isPropagatedContext===true
        // TODO retrieve regions title ONCE per regions not for each crop
        ? fetch(`${baseUrl}${path}get_regions_title/${regionRef}`)
            .then(r => r.json())
            .then(r => formatter(r.title))
            .catch(e => {
                console.error("similarity.utils.getDesc()", e);
                return formatter(appLang === "fr" ? "Titre inconnu" : "Unknown title");
            })
        : Promise.resolve(formatter(getRegionsInfo(regionRef).title));
}
