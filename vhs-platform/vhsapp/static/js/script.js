$(function() {
    $("[id$=-pdf]").attr("accept", "application/pdf");
    $("p.url a, span.inline_label a, div.readonly a, .field-image p a, p.file-upload a").attr("target", "_blank");
    $("[id$=-0-image]").attr("multiple", true);
    $(".add-handler").on("click", function() {
        $("#id_volume_set-__prefix__-title").val($("#id_work").text());
        $("#id_volume_set-__prefix__-place").val($("#id_place").val());
        $("#id_volume_set-__prefix__-date").val($("#id_date").val());
        $("#id_volume_set-__prefix__-publishers_booksellers").val($("#id_publishers_booksellers").val());
        $("#id_volume_set-__prefix__-manifest_final").replaceWith("<i class='fa-solid fa-circle-xmark' style='color:red'></i>");
    } );

    $("[id^=annotate_manifest_]").on("click", function() {
        idButton = $(this).attr("id")
        idManifest = idButton.split("_").pop();
        if (idButton.includes("annotate_manifest_auto_")) {
            const urlManifest = $("iiif_auto_" + idManifest).prop("href");
            idMessage = "message_auto_" + idManifest;
            var xhr = new XMLHttpRequest();
            xhr.open("GET", urlManifest, true);
            xhr.responseType = "json";
            xhr.onload = function() {
                if (xhr.readyState === 4 && xhr.status === 200) {
                    window.open(`${SAS_APP_URL}/indexAnnos.html?iiif-content=${urlManifest}`, "_blank");
                } else {
                    showMessage(`Failed to load ${urlManifest} due to ${xhr.status}: ${xhr.statusText}`);
                }
            };
            xhr.send();
            return false;
        }
        urlManifest = $("#url_manifest_" + idManifest).prop("href");
        idMessage = "message_" + idManifest;
        work = new URL(urlManifest).pathname.split("/")[4];
        setLoading(idButton);
        sendUrlManifest(urlManifest);
        return false;
    } );

    $("[id^=manifest_final_]").on("click", function() {
        idButton = $(this).attr("id");
        idManifest = idButton.split("_").pop();
        urlManifest = $(`#url_manifest_${idManifest}`).prop("href");
        setLoading(idButton);
        window.open(`${SAS_APP_URL}/indexView.html?iiif-content=${urlManifest}`, "_blank");
        clearLoadingView(idButton);
        return false;
    } );
} );

var getJSON = function(url, callback) {
    let xhr = new XMLHttpRequest();
    xhr.open("GET", url, true);
    xhr.responseType = "json";
    xhr.onload = function() {
        if (xhr.readyState === 4 && xhr.status === 200) {
            callback(xhr.status, xhr.response);
        } else {
            showMessage(`Failed to load ${url} due to ${xhr.status}: ${xhr.statusText}`);
        }
    };
    xhr.send();
};

var sendJson = function sendJson(status, data) {
    let xhr = new XMLHttpRequest();
    xhr.open("POST", `${SAS_APP_URL}/manifests`, true);
    xhr.setRequestHeader("Content-Type", "application/json");
    xhr.onload = function () {
        if (xhr.readyState === 4 && xhr.status === 200) {
            populateAnnotation(`/${APP_NAME}/iiif/v2/${work}/${idManifest}/populate/`);
        } else {
            showMessage(`Failed to index ${data["@id"]} due to ${xhr.status}: ${xhr.statusText}`);
        }
    };
    xhr.send(JSON.stringify(data));
};

function showMessage(message) {
    const messages = document.getElementById(idMessage);
    messages.textContent = message;
    messages.style.display = "block";
}

function setLoading(idButton) {
    var button = document.getElementById(idButton);
    button.innerHTML = "<span class='fa fa-spinner fa-spin fa-pulse fa-1x'></span> Indexing...";
    button.disabled = true;
}

function clearLoadingAuto(idButton) {
    var button = document.getElementById(idButton);
    button.innerHTML = "<i class='fa-solid fa-eye'></i> VISUALISER ANNOTATIONS <i class='fa-solid fa-comment'></i>";
    button.disabled = false;
}

function clearLoadingEdit(idButton) {
    var button = document.getElementById(idButton);
    button.innerHTML = "<i class='fa-solid fa-pen-to-square'></i> ÉDITER ANNOTATIONS <i class='fa-solid fa-comment'></i>";
    button.disabled = false;
}

function clearLoadingView(idButton) {
    var button = document.getElementById(idButton);
    button.innerHTML = "<i class='fa-solid fa-pen-to-square'></i> ANNOTATIONS FINALES <i class='fa-solid fa-comment'></i>";
    button.disabled = false;
}

function sendUrlManifest(urlManifest) {
    uri = urlManifest;
    getJSON(uri, sendJson);
}

function populateAnnotation(url) {
    var xhr = new XMLHttpRequest();
    xhr.open("GET", url, true); // true for asynchronous
    xhr.onload = function() {
        if (xhr.readyState === 4 && xhr.status === 200) {
            window.open(`/${APP_NAME}/${work}/${idManifest}/show/`, "_blank");
            clearLoadingEdit(idButton);
        } else {
            showMessage(`Failed to display ${url} due to ${xhr.status}: ${xhr.statusText}`, idManifest);
        }
    }
    xhr.send(null);
}
