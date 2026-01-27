/**
 * @typedef {Object} RegionItemType
 * @property {string} id
 * @property {string} img
 * @property {string} title
 * @property {number[]} xywh - [x, y, width, height]
 * @property {string} canvas
 * @property {string} ref
 * @property {string} type
 */

import { regionsType } from "../constants.js";
import { refToIIIF } from "../utils.js";

export class RegionItem {
    /** @param {RegionItemType} data */
    constructor(data) {
        this.id = data.id;
        this.img = data.img ?? data.ref;
        this.title = data.title;
        this.xywh = Array.isArray(data.xywh) ? data.xywh.map(Number) : data.xywh;
        this.canvas = data.canvas;
        this.ref = data.ref;
        this.type = data.type ?? regionsType;
    }

    url(coord = null, size = null) {
        return refToIIIF(this.img, coord ?? this.xywh ?? "full", size ?? "full");
    }
}
