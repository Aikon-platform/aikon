import { writable } from 'svelte/store';
import { sasUrl, cantaloupeUrl, appName } from './constants';

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
    // put '...' in between the 75% and last 25% characters oif the string it too long
    const nthChar = Math.floor(maxLen * 0.75);
    return str.length > maxLen ? str.slice(0, nthChar) + '...' + str.slice(- maxLen + nthChar) : str;
}

export function getCantaloupeUrl() {
    return cantaloupeUrl ?? "http://localhost:8182";
}

export function getSasUrl() {
    return sasUrl ?? "http://localhost:3000";
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

export function refToIIIF(imgRef = null, coord= "full", size="full") {
    // imgRef can be like "wit<id>_<digit><id>_<page_nb>.jpg" or "wit<id>_<digit><id>_<page_nb>_<x,y,h,w>.jpg"
    if (!imgRef) {
        return "https://placehold.co/96x96/png?text=No+image";
    }
    imgRef = imgRef.split("_");
    if (imgRef.length < 3) {
        return "https://placehold.co/96x96/png?text=No+image";
    }
    const imgCoord = imgRef[imgRef.length -1].includes(",") ? imgRef.pop().replace(".jpg", "") : coord;
    const imgName = imgRef.join("_").replace(".jpg", "");

    return `${getCantaloupeUrl()}/iiif/2/${imgName}.jpg/${imgCoord}/${size}/0/default.jpg`;
}

export function manifestToMirador(manifest = null, canvasNb = 1) {
    return `${getSasUrl()}/index.html?iiif-content=${manifest}&canvas=${canvasNb}`;
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
