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
import {getCantaloupeUrl, getSasUrl} from "../utils.js";

const IMG_REF_REGEX = /^(?:(\d+)_)?wit(\d+)_([a-z]{3})(\d+)(?:_anno(\d+))?_(\d+)(?:_([\d,]+))?(?:\.jpg)?$/;

function parseImgRef(imgRef) {
    if (!imgRef) return null;

    const match = imgRef.match(IMG_REF_REGEX);
    if (!match) return null;

    const [, prefixId, witId, digType, digId, annoId, canvasStr, coordStr] = match;

    return {
        witnessId: parseInt(witId, 10),
        digitizationType: digType,
        digitizationId: parseInt(digId, 10),
        regionId: prefixId ? parseInt(prefixId, 10) : (annoId ? parseInt(annoId, 10) : null),
        canvasNb: parseInt(canvasStr, 10),
        canvasDigits: canvasStr.length,
        coord: coordStr ? coordStr.split(',').map(Number) : null,
        imgRoot: `wit${witId}_${digType}${digId}_${canvasStr}.jpg`
    };
}

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

        this._parsed = null;
    }

    get parsed() {
        if (!this._parsed) {
            this._parsed = parseImgRef(this.img) || {};
        }
        return this._parsed;
    }

    get witnessId() { return this.parsed.witnessId; }
    get digitType() { return this.parsed.digitizationType; }
    get digitId() { return this.parsed.digitizationId; }
    get regionId() { return this.parsed.regionId; }
    get canvasNb() { return this.parsed.canvasNb; }
    get canvasDigits() { return this.parsed.canvasDigits; }
    get imgRoot() { return this.parsed.imgRoot; }
    get coord() { return this.parsed.coord ?? this.xywh; }

    canvasStr(canvasNb = this.canvasNb, digits = this.canvasDigits) {
        return String(canvasNb).padStart(digits, '0');
    }

    get iiifRoot() {
        return this.imgRoot ? `${getCantaloupeUrl()}/iiif/2/${this.imgRoot}` : null;
    }

    url(coord = null, size = "full") {
        if (!this.iiifRoot) return "https://placehold.co/96x96/png?text=No+image";

        let c = coord ?? this.coord ?? "full";
        if (Array.isArray(c)) c = c.join(',');

        return `${this.iiifRoot}/${c}/${size}/0/default.jpg`;
    }

    info() {
        return this.iiifRoot ? `${this.iiifRoot}/info.json` : null;
    }

    manifest() {
        let ref = `wit${this.witnessId}_${this.digitType}${this.digitId}`;
        if (this.regionId) {
            ref += `_anno${this.regionId}`;
        }
        return `${getCantaloupeUrl()}/iiif/v2/${ref}/manifest.json`;
    }

    urlForCanvas(canvasNb = this.canvasNb, coord = this.coord, size = "full") {
        const newImgRoot = this.imgRoot.replace(
            `_${this.canvasStr()}.jpg`,
            `_${this.canvasStr(canvasNb)}.jpg`
        );
        const xywh = Array.isArray(coord) ? coord.join(',') : coord;
        return `${getCantaloupeUrl()}/iiif/2/${newImgRoot}/${xywh}/${size}/0/default.jpg`;
    }

    infoUrlForCanvas(canvasNb = this.canvasNb) {
        const newImgRoot = this.imgRoot.replace(
            `_${this.canvasStr()}.jpg`,
            `_${this.canvasStr(canvasNb)}.jpg`
        );
        return `${getCantaloupeUrl()}/iiif/2/${newImgRoot}/info.json`;
    }

    urlForMirador(canvasNb = this.canvasNb){
        return `${getSasUrl()}/index.html?iiif-content=${this.manifest()}&canvas=${canvasNb}`;
    }
}
