import { appLang, regionsType } from '../constants';
import { extractNb } from "../utils.js";

/** @typedef {import("./types.js").RegionItemType} RegionItemType */

/**
 * @param {string} imgName
 * @param {string} witId
 * @param {string} xywh
 * @param {string} canvas
 * @returns {RegionItemType}
 */
export const toRegionItem = (imgName, witId, xywh, canvas) => ({
    id: imgName, // note for normal regions, it is their SAS annotation id: used for region selection
    img: imgName,
    title: `Canvas ${canvas} - ${xywh} - ${appLang === 'en' ? 'Witness' : 'Témoin'} #${extractNb(witId)}`,
    xywh: xywh.split(",").map(Number),
    canvas: canvas,
    ref: imgName.replace('.jpg', ''),
    type: regionsType
})
