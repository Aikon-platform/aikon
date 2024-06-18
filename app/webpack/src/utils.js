export function getCantaloupeUrl() {
    return CANTALOUPE_APP_URL ?? "http://localhost:8182";
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


export function parseData(elementId) {
    if (!document.getElementById(elementId)) {
        return [];
    }
    return JSON.parse(document.getElementById(elementId).textContent);
}
