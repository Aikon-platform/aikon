import { writable } from 'svelte/store';

export const loading = writable(false);

export async function withLoading(asyncFunction) {
    loading.set(true);
    try {
        return await asyncFunction();
    } finally {
        loading.set(false);
    }
}

export function getCantaloupeUrl() {
    return CANTALOUPE_APP_URL ?? "http://localhost:8182";
}

export function getSasUrl() {
    return SAS_APP_URL ?? "http://localhost:3000";
}

export async function getRecordList() {
    const res = await fetch('/api/records/');

    if (res.ok) {
        return await res.text();
    } else {
        throw new Error('Request failed');
    }
}

export function refToIIIF(imgRef = null, coord= "full", size="full") {
    // imgRef can be like "wit<id>_<digit><id>_<page_nb>.jpg" or "wit<id>_<digit><id>_<page_nb>_<x,y,h,w>.jpg"
    if (!imgRef) {
        return "https://via.placeholder.com/96x96?text=No+Image";
    }
    imgRef = imgRef.split("_");
    if (imgRef.length < 3) {
        return "https://via.placeholder.com/96x96?text=No+Image";
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
                document.getElementById("modal-title").textContent = title;
            }
            document.getElementById("modal-body").textContent = msg;
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
