function to_manifest(witnessRef, version) {
    const witnessType = witnessRef.startsWith(MS_ABBR) ? MS.toLowerCase() : VOL.toLowerCase()
    return `${VHS_APP_URL}/${APP_NAME}/iiif/${version}/${witnessType}/${formatWitRef(witnessRef)}/manifest.json`
}

function extractNb(str) {
  return str.match(/\d+/g).toString();
}

function formatWitRef(witnessRef, onlyId= false){
    if (onlyId){
        return extractNb(witnessRef);
    }

    if (witnessRef.includes("-")){
        return witnessRef;
    }
    return witnessRef.replace(/([a-zA-Z])(\d+)/g, "$1-$2");
}

function getJSON(url, callback, idMessage) {
    let xhr = new XMLHttpRequest();
    xhr.open("GET", url, true);
    xhr.responseType = "json";
    xhr.onload = function () {
        if (xhr.readyState === 4 && xhr.status === 200) {
            callback(xhr.status, xhr.response);
        } else {
            showMessage(`Failed to load ${url} due to ${xhr.status}: ${xhr.statusText}`, idMessage);
        }
    };
    xhr.send();
}

function editAnnotations(witnessRef, idButton) {
    /* Function triggered on click on the "v2" btn that redirects to the show page to correct annotations */
    const manifestUrl = to_manifest(witnessRef, "auto"); // $(`#url_manifest_${witnessRef}`).prop("href");
    const idMessage = `message_${witnessRef}`;
    const witnessType = new URL(manifestUrl).pathname.split("/")[4];
    const innerHtml = $(`#${idButton}`).html();

    setLoading(idButton);

    const sendJson = function sendJson(status, data) {
        fetch(`${SAS_APP_URL}/manifests`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(data)
        }).then(response => {
            if (response.ok) {
                const populateUrl = `/${APP_NAME}/iiif/v2/${witnessType}/${formatWitRef(witnessRef, true)}/populate/`
                populateAnnotation(populateUrl, idButton);
            } else {
                throw new Error(`Failed to index ${data["@id"]} due to ${response.status}: ${response.statusText}`);
            }
        }).catch(error => {
            showMessage(error.message, idMessage);
        });
    };
    function populateAnnotation(url, idButton) {
        fetch(url)
            .then(response => {
                if (response.ok) {
                    window.open(`/${APP_NAME}/${witnessType}/${formatWitRef(witnessRef, true)}/show/`, "_blank");
                    clearLoading(idButton, innerHtml)
                } else {
                    throw new Error(`Failed to display ${url} due to ${response.status}: ${response.statusText}`);
                }
            })
            .catch(error => {
                showMessage(`Failed to display ${url} due to: ${error.message}`, idMessage);
            });
    }

    getJSON(manifestUrl, sendJson, idMessage);
}


function finalAnnotations(btn) {
    /* Function triggered on click on the "final" btn that redirects to the show page to correct annotations */
    const idButton = btn.attr("id");
    const innerHtml = btn.html()
    const witnessRef = idButton.split("_").pop();
    setLoading(idButton);
    window.open(`${SAS_APP_URL}/indexView.html?iiif-content=${to_manifest(witnessRef, "v2")}`, "_blank");
    clearLoading(idButton, innerHtml);
    return false;
}


function viewAnnotations(witnessRef) {
    /* Function triggered on click on the "auto" btn that redirects to a Mirador viewer */
    const manifestUrl = to_manifest(witnessRef, "auto")// $(`#iiif_auto_${witnessRef}`).prop("href");
    const idMessage = `message_auto_${witnessRef}`;

    fetchManifest(manifestUrl)
        .then(response => {
            if (response.ok) {
                window.open(`${SAS_APP_URL}/indexAnnos.html?iiif-content=${manifestUrl}`, "_blank");
            } else {
                showMessage(`Failed to load ${manifestUrl} due to ${response.status}: ${response.statusText}`, idMessage);
            }
        })
        .catch(error => {
            showMessage(`Failed to load ${manifestUrl}: ${error.message}`, idMessage);
        });

    return false;

}

function showMessage(message, idMessage) {
    const msgElement = document.getElementById(idMessage);
    if (msgElement) {
        msgElement.textContent = message;
        msgElement.style.display = "block";
    }
}

function setLoading(idButton) {
    const button = document.getElementById(idButton);
    button.innerHTML = "<span class='fa fa-spinner fa-spin fa-pulse fa-1x'></span> Indexing...";
    button.disabled = true;
}

function clearLoading(idButton, innerHtml) {
    const button = document.getElementById(idButton);
    button.innerHTML = innerHtml;
    button.disabled = false;
}

function fetchManifest(url) {
    return fetch(url).then(response => response.json());
}
