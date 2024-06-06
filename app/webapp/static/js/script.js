// const csrfToken = $("input[name=csrfmiddlewaretoken]").val();
function checkStatus(taskId, callback) {
    $.ajax({
        url: `${APP_URL}/${APP_NAME}/task-status/${taskId}/`,
        type: "GET",
        headers: { "X-CSRFToken": CSRF_TOKEN },
        dataType: "json",
        success: function (data) {
            if (data.status === "running") {
                setTimeout(function () {
                    checkStatus(taskId, callback);
                }, 1000); // Check every 1 second
            } else if (data.status === "success") {
                callback(JSON.parse(data.result));
            }
        },
        error: function (xhr, status, error) {
            console.error("Error checking similarity status:", xhr, status, error);
        }
    });
}

function getUrl() {
    return window.location.href;
}

function capitalize(s) {
    return s[0].toUpperCase() + s.slice(1);
}

function getWitType() {
    // TODO remove fct
    const currentUrl = getUrl();
    if (currentUrl.includes(MS)) {
        return MS;
    } else if (currentUrl.includes("printed") || currentUrl.includes(VOL)) {
        return VOL;
    }
    return null;
}

function getRegionsRef() {
    const currentUrl = getUrl();
    if (currentUrl.includes("show")){
        const parts = currentUrl.split("/show")[0].split("/");
        return parts[parts.length - 1];
    }
    return null;
}

function toManifest(witId, witType, version) {
    return `${APP_URL}/${APP_NAME}/iiif/${version}/${witType}/${witId}/manifest.json`
}

function extractNb(str) {
    return str.match(/\d+/g).toString();
}

function getJSON(url, callback, idMessage) {
    fetch(url).then(response => {
        if (response.ok) {
            return response.json();
        }
        throw new Error(`Failed to load ${url} due to ${response.status}: ${response.statusText}`);
    }).then(response => {
        callback(response.status, response);
    }).catch(error => {
        showMessage(error.message, idMessage);
    });
}

function showMessage(message, idMessage = null) {
    const msgElement = idMessage ? document.getElementById(idMessage) : null;
    if (msgElement) {
        msgElement.textContent = message;
        msgElement.style.display = "block";
    } else {
        alert(message)
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

function deleteRegion(regionId) {
    const HTTP_SAS = SAS_APP_URL.replace("https", "http");
    const urlDelete = `${SAS_APP_URL}/annotation/destroy?uri=${HTTP_SAS}/annotation/${regionId}`;

    fetch(urlDelete, {
        method: "DELETE"
    }).then(response => {
        if (response.status === 204) {
            const regionDiv = $(`#ill_${regionId}`).closest("div");
            regionDiv.fadeOut(function() {
                regionDiv.remove()
            });
        } else {
            showMessage(`Failed to delete ${urlDelete} due to ${response.status}: '${response.statusText}'`, `message_${regionId}`);
        }
    }).catch(error => {
        showMessage(`Failed to delete ${urlDelete}: ${error.message}`, `message_${regionId}`);
    });
}

function deleteRegions(regionsIds) {
    if (regionsIds.length > 0) {
        if (confirm(APP_LANG === "en" ? "Are you sure you want to delete corresponding regions?" :
                "Êtes-vous sûr de vouloir supprimer les régions sélectionnées ?")) {
            for (let i = 0; i < regionsIds.length; i++) {
                deleteRegion(regionsIds[i]);
            }
            return true;
        }
        return false;
    }
    alert(APP_LANG === "en" ? "Please select at least one region to delete" : "Veuillez sélectionner au moins une image à supprimer.");
    return false;
}

function deleteAllRegions(allRegions) {
    if (confirm(APP_LANG === "en" ? "Are you sure you want to delete all regions?" :
            "Êtes-vous sûr de vouloir supprimer toutes les régions ?")) {
        for (let i = allRegions.length - 1; i >= 0; i--) {
            deleteRegion(allRegions[i]);
        }
    }
}

function validateRegions(regions_ref = null) {
    if (!regions_ref) {
        regions_ref = getRegionsRef();
        if (!regions_ref) {
            console.log("No region reference")
            return
        }
    }

    if (confirm(APP_LANG === "en" ? `Once validated, the regions cannot be modified. Continue?` :
            `Une fois validées, les régions ne pourront plus être modifiées. Continuer ?`)) {
        fetch(`${APP_URL}/${APP_NAME}/iiif/validate/${regions_ref}`)
            .then(response => {
            if (response.status === 200) {
                // window.replace(`${SAS_APP_URL}/indexView.html?iiif-content=${toManifest(witId, witType, "v2")}`);
                try { window.replace(`${APP_URL}/${APP_NAME}-admin/${WEBAPP_NAME}/witness`); }
                catch(e) { window.location = `${APP_URL}/${APP_NAME}-admin/${WEBAPP_NAME}/witness`; }
            } else {
                throw new Error(`Could not validate regions #${regions_ref}.`);
            }
        }).catch(error => {
            showMessage(`Error: ${error.message}`);
        });
    }
}
