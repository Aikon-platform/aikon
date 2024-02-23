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
                    checkStatus(taskId);
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

function getAnnoRef() {
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

function deleteAnnotation(annoId) {
    const HTTP_SAS = SAS_APP_URL.replace("https", "http");
    const urlDelete = `${SAS_APP_URL}/annotation/destroy?uri=${HTTP_SAS}/annotation/${annoId}`;

    fetch(urlDelete, {
        method: "DELETE"
    }).then(response => {
        if (response.status === 204) {
            const annoDiv = $(`#ill_${annoId}`).closest("div");
            annoDiv.fadeOut(function() {
                annoDiv.remove()
            });
        } else {
            showMessage(`Failed to delete ${urlDelete} due to ${response.status}: '${response.statusText}'`, `message_${annoId}`);
        }
    }).catch(error => {
        showMessage(`Failed to delete ${urlDelete}: ${error.message}`, `message_${annoId}`);
    });
}

function deleteAnnotations(annoIds) {
    if (annoIds.length > 0) {
        if (confirm(APP_LANG === "en" ? "Are you sure you want to delete corresponding annotations?" :
                "Êtes-vous sûr de vouloir supprimer les annotations sélectionnées ?")) {
            for (let i = 0; i < annoIds.length; i++) {
                deleteAnnotation(annoIds[i]);
            }
            return true;
        }
        return false;
    }
    alert(APP_LANG === "en" ? "Please select at least one annotation to delete" : "Veuillez sélectionner au moins une image à supprimer.");
    return false;
}

function deleteAllAnnotations(allAnnos) {
    if (confirm(APP_LANG === "en" ? "Are you sure you want to delete all annotations?" :
            "Êtes-vous sûr de vouloir supprimer toutes les annotations ?")) {
        for (let i = allAnnos.length - 1; i >= 0; i--) {
            deleteAnnotation(allAnnos[i]);
        }
    }
}

function validateAnnotations(anno_ref = null) {
    if (!anno_ref) {
        anno_ref = getAnnoRef();
        if (!anno_ref) {
            console.log("No annotation reference")
            return
        }
    }

    if (confirm(APP_LANG === "en" ? `Once validated, the annotations cannot be modified. Continue?` :
            `Une fois validées, les annotations ne pourront plus être modifiées. Continuer ?`)) {
        fetch(`${APP_URL}/${APP_NAME}/iiif/validate/${anno_ref}`)
            .then(response => {
            if (response.status === 200) {
                // window.replace(`${SAS_APP_URL}/indexView.html?iiif-content=${toManifest(witId, witType, "v2")}`);
                try { window.replace(`${APP_URL}/${APP_NAME}-admin/${WEBAPP_NAME}/witness`); }
                catch(e) { window.location = `${APP_URL}/${APP_NAME}-admin/${WEBAPP_NAME}/witness`; }
            } else {
                throw new Error(`Could not validate annotations #${anno_ref}.`);
            }
        }).catch(error => {
            showMessage(`Error: ${error.message}`);
        });
    }
}
