import { writable } from 'svelte/store';
import { miradorUrl, cantaloupeUrl, appName } from './constants';

export const loading = writable(false);
export const errorMsg = writable("");

export async function withLoading(asyncFunction) {
    loading.set(true);
    try {
        return await asyncFunction();
    } finally {
        loading.set(false);
    }
}

export function extractNb(str) {
    return str.match(/\d+/g).toString();
}

export function shorten(str, maxLen=100) {
    // put '...' in between the 75% and last 25% characters if the string it too long
    const nthChar = Math.floor(maxLen * 0.75);
    return str.length > maxLen ? str.slice(0, nthChar) + '...' + str.slice(- maxLen + nthChar) : str;
}

export function getCantaloupeUrl() {
    return cantaloupeUrl ?? "http://localhost:8182";
    // // TO DELETE
    // return "https://vhs.huma-num.fr"
}

export function getMiradorUrl() {
    return miradorUrl ?? "http://localhost:5555";
}

export function initPagination(pageWritable, urlParam) {
    if (typeof window !== 'undefined') {
        const urlPage = parseInt(new URLSearchParams(window.location.search).get(urlParam));
        if (!isNaN(urlPage)) {
            pageWritable.set(urlPage);
            return urlPage;
        }
    }
    pageWritable.set(1);
    return 1;
}

export function pageUpdate(pageNb, pageWritable, urlParam) {
    pageWritable.set(pageNb);
    if (typeof window !== 'undefined') {
        const url = new URL(window.location.href);
        url.searchParams.set(urlParam, pageNb);
        window.history.pushState({}, '', url);
    }
}

/** extract image name by removing crop info and adding `.jpg` at the end */
function refToIIIFName(imgRef=null) {
    imgRef = imgRef.split("_");
    return imgRef.length < 3
        ? undefined
        : `${imgRef.slice(0,3).join("_").replace(".jpg", "")}.jpg`;
}

/** return the root IIIF URL: cantaloupe URL + image name, without any of the IIIF params */
export function refToIIIFRoot(imgRef=null) {
    const imgName = refToIIIFName(imgRef);
    return imgName === undefined
        ? undefined
        : `${getCantaloupeUrl()}/iiif/2/${imgName}`;
}

export function refToIIIF(imgRef=null, coord="full", size="full") {
    // imgRef can be like "wit<id>_<digit><id>_<page_nb>.jpg" or "wit<id>_<digit><id>_<page_nb>_<x,y,h,w>.jpg"
    if (!imgRef) {
        return "https://placehold.co/96x96/png?text=No+image";
    }
    const imgRoot = refToIIIFRoot(imgRef);
    if (imgRoot === undefined) {
        return "https://placehold.co/96x96/png?text=No+image";
    }
    /*if (size !== "full" && imgCoord !== "full") {
        let [_, __, crop_h, crop_w] = String(imgCoord).split(",").map(Number);
        let [size_h, size_w] = size.split(",").map(Number);

        if (size_h && size_h > crop_h) {
            size_h = Math.min(size_h, crop_h);
        }
        if (size_w && size_w > crop_w){
            size_w = Math.min(size_w, crop_w);
        }
        // width and height of the crop cannot exceed the size of whole image
        // to obtain original image size, we could request ${getCantaloupeUrl()}/iiif/2/${imgName}.jpg/info.json
        // to retrieve info["width"] and info["height"] to be used instead of crop_h / crop_w

        size = `${size_h},${size_w}`;
    }*/

    const imgRefArr = imgRef.split("_");
    // const imgCoord = coord ? coord : imgRefArr[imgRefArr.length -1].includes(",") ? imgRefArr.pop().replace(".jpg", "") : "full";
    const imgCoord = imgRefArr[imgRefArr.length -1].includes(",") ? imgRefArr.pop().replace(".jpg", "") : coord;
    return `${imgRoot}/${imgCoord}/${size}/0/default.jpg`;
}

export function refToIIIFInfo(imgRef=null) {
    return `${refToIIIFRoot(imgRef)}/info.json`;
}

export function manifestToMirador(manifest = null, canvasNb = 1) {
    return `${getMiradorUrl()}/index.html?iiif-content=${manifest}&canvas=${canvasNb}`;
}


export function parseData(elementId) {
    if (!document.getElementById(elementId)) {
        return [];
    }
    return JSON.parse(document.getElementById(elementId).textContent);
}

export function showMessage(msg, title = null, confirm = false) {
    return new Promise((resolve) => {
        const msgModal = document.getElementById("msg-modal");
        if (msgModal) {
            if (confirm) {
                document.getElementById("modal-footer").hidden = false;
            } else {
                resolve(undefined);
            }
            if (title) {
                document.getElementById("modal-title").innerHTML = title;
            }
            document.getElementById("modal-body").innerHTML = msg;
            document.getElementById("hidden-msg-btn").click();

            const cancelBtn = document.getElementById("cancel-btn");
            const okBtn = document.getElementById("ok-btn");
            const modalBkg = document.getElementById("modal-bkg");

            const cleanup = () => {
                cancelBtn.removeEventListener("click", handleCancel);
                modalBkg.removeEventListener("click", handleCancel);
                okBtn.removeEventListener("click", handleOk);
                document.getElementById("modal-footer").hidden = true;
            };

            const handleCancel = () => {
                cleanup();
                resolve(false);
            };

            const handleOk = () => {
                cleanup();
                resolve(true);
            };

            cancelBtn.addEventListener("click", handleCancel);
            okBtn.addEventListener("click", handleOk);
        } else {
            if (confirm) {
                resolve(window.confirm(msg));
            } else {
                window.alert(msg);
                resolve(undefined);
            }
        }
    });
}

export function downloadBlob(blob, filename) {
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${filename}`;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
}


export async function getSuccess(url) {
    try {
        const response = await fetch(url);
        return response.ok;
    } catch (error) {
        console.error('Error:', error);
        return false;
    }
}


export async function deleteRecord(recordId, recordType){
    return getSuccess(`/${appName}/${recordType.toLowerCase()}/${recordId}/delete`);
}


/**
 * @typedef NewAndOldType
 *    an object that tracks changes to another object.
 * @type {Object}
 * @property {(x:Any) => void} set
 *      define the newest object and update the old one
 * @property {() => Any} get
 *      get the new object
 * @property {(x:Any) => void} setCompareFn
 *      define the comparison function. defining this function allows to have some custom way to check if `_new` and `_old` are different (i.e., deep equality in case of objects)
 * @property {() => Array<Any>} getNewAndOld
 *      get a pair of [New, Old]
 * @property {() => boolean} same
 *      using this._compareFn, returns a boolean indicating that _new is the same as _old. defined as a function rather than as an attribute to ensure that `same` is always run on the latest [New, Old] pair.
 */
// TODO create a custom event that emits when the value changes ? https://stackoverflow.com/a/62984915
/** @returns {NewAndOldType} */
export function createNewAndOld() {
    let _new = undefined;
    let _old = undefined;
    let _compareFn = (_new, _old) => _new === _old;
    return {
        set: (newVal) => {
            _old = _new;
            _new = newVal;
        },
        setCompareFn: (newCompareFn) => _compareFn = newCompareFn,
        get: () => _new,
        getNewAndOld: () => [_new, _old],
        same: () => _compareFn(_new, _old)
    }
}

/**
 * @typedef {LoadStateType} an object to manage a "loading" state, useful when doing async queries
 * @type {object}
 * @property {() => void} setLoading
 * @property {() => void} setLoaded: loading finished without error
 * @property {() => void} setError: error in loading
 * @property {() => 0|1|-1} get: returns the load state as a number code. 0 = "loading", 1 = "loaded", -1 = "error"
 * @property {() => "loading"|"loaded"|"error"} getString: returns the load state as a string
 */
export function createLoadState() {
    /** @type {0|1|-1} 0="loading", 1="loaded", -1="error" */
    let _state = 0;
    return {
        setLoading: () => _state = 0,
        setLoaded: () => _state = 1,
        setError: () => _state = -1,
        get: () => _state,
        getString: () =>
            _state===0
            ? "loading"
            : _state===1
            ? "loaded"
            : "error"
    }
}


/**
 * @param {Any | Array<Any>} x: an array of hashable values
 * @param {Any | Array<Any>} y: an array of hashable values
 * @returns {boolean} true if the arrays are the same
 */
export const equalArrayShallow = (x, y) =>
    Array.isArray(x) && Array.isArray(y)
    && x.length===y.length
    && x.every((e, idx) => e === y[idx]||undefined);


export function imageToPage(imgName) {
    return parseInt(imgName.split('_').at(-2));
}

export function generateColor(index) {
    const goldenAngle = 137.5;
    const saturations = [85, 70, 60];
    const lightnesses = [50, 65, 40];
    const hue = (index * goldenAngle) % 360;
    const saturation = saturations[index % saturations.length];
    const lightness = lightnesses[Math.floor(index / saturations.length) % lightnesses.length];
    return `hsl(${Math.floor(hue)}, ${saturation}%, ${lightness}%)`;
}
