/**
 * @typedef {Object} RegionItemType
 * @property {string} id
 * @property {string} img - Either "wit<id>_<digit><id>_<page_nb>.jpg" or "wit<id>_<digit><id>_<page_nb>_<x,y,h,w>.jpg"
 * @property {string} title - Title of the region (to be displayed in the overlay)
 * @property {number[]|string[]} xywh - [x, y, width, height]
 * @property {string} canvas - Page number
 * @property {string} ref - Unique reference to be copied in the clipboard
 * @property {string} type - Always "Regions"
 */

import {regionsType} from "../constants.js";
import {refToIIIF} from "../utils.js";

export {}

export class RegionItem {
    /**
     * @param {RegionItemType} data
     */
    constructor(data) {
        this.id = data.id;
        this.img = data.img ?? data.ref;
        this.title = data.title;
        this.xywh = data.xywh;
        this.canvas = data.canvas;
        this.ref = data.ref;
        this.type = regionsType;
    }

    url(coord = null, size = null) {
        return refToIIIF(
            this.img,
            coord ?? this.xywh ?? "full",
            size ?? "full"
        );
    }
}
