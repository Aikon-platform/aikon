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

    $("[id^=manifest_final_]").on("click", function() {
        finalAnnotations($(this));
    } );

    $("[id^=annotate_manifest_]").off("click").on("click", function(e) {
        e.preventDefault();
        idButton = $(this).attr("id")
        idManifest = idButton.split("_").pop();

        if (idButton.includes("annotate_manifest_auto_")) {
            const manifestUrl = $(`#iiif_auto_${idManifest}`).prop("href");
            idMessage = "message_auto_" + idManifest;
            var xhr = new XMLHttpRequest();
            xhr.open("GET", manifestUrl, true);
            xhr.responseType = "json";
            xhr.onload = function() {
                if (xhr.readyState === 4 && xhr.status === 200) {
                    window.open(`${SAS_APP_URL}/indexAnnos.html?iiif-content=${manifestUrl}`, "_blank");
                } else {
                    showMessage(`Failed to load ${manifestUrl} due to ${xhr.status}: ${xhr.statusText}`);
                }
            };
            xhr.send();
            return false;
        }
        manifestUrl = $("#url_manifest_" + idManifest).prop("href");
        idMessage = "message_" + idManifest;
        work = new URL(manifestUrl).pathname.split("/")[4];
        setLoading(idButton);
        getJSON(manifestUrl, sendJson);
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

function finalAnnotations(btn) {
    /* Function triggered on click on the "final" btn that redirects to the show page to correct annotations */
    const idButton = btn.attr("id");
    const innerHtml = btn.html()
    witRef = idButton.split("_").pop();
    setLoading(idButton);
    window.open(`${SAS_APP_URL}/indexView.html?iiif-content=${to_manifest(witRef, "v2")}`, "_blank");
    clearLoading(idButton);
    return false;
}

function editAnnotations(btn) {
    /* Function triggered on click on the "v2" btn that redirects to the show page to correct annotations */
}

function viewAnnotation(btn) {
    /* Function triggered on click on the "auto" btn that redirects to a Mirador viewer */
}

// var sendJson = function sendJson(status, data) {
//     let xhr = new XMLHttpRequest();
//     xhr.open("POST", `${SAS_APP_URL}/manifests`, true);
//     xhr.setRequestHeader("Content-Type", "application/json");
//     xhr.onload = function () {
//         if (xhr.readyState === 4 && xhr.status === 200) {
//             populateAnnotation(`/${APP_NAME}/iiif/v2/${work}/${idManifest}/populate/`);
//         } else {
//             showMessage(`Failed to index ${data["@id"]} due to ${xhr.status}: ${xhr.statusText}`);
//         }
//     };
//     xhr.send(JSON.stringify(data));
// };

const sendJson = function sendJson(status, data) {
    fetch(`${SAS_APP_URL}/manifests`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data)
    }).then(response => {
        if (response.ok) {
            populateAnnotation(`/${APP_NAME}/iiif/v2/${work}/${idManifest}/populate/`);
        } else {
            throw new Error(`Failed to index ${data["@id"]} due to ${response.status}: ${response.statusText}`);
        }
    }).catch(error => {
        showMessage(error.message);
    });
};


function showMessage(message) {
    const messages = document.getElementById(idMessage);
    messages.textContent = message;
    messages.style.display = "block";
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

// function clearLoadingAuto(idButton) {
//     const button = document.getElementById(idButton);
//     button.innerHTML = autoBtn;
//     button.disabled = false;
// }
//
// function clearLoadingEdit(idButton) {
//     const button = document.getElementById(idButton);
//     button.innerHTML = v2Btn;
//     button.disabled = false;
// }
//
// function clearLoadingView(idButton) {
//     const button = document.getElementById(idButton);
//     button.innerHTML = "<i class='fa-solid fa-pen-to-square'></i> ANNOTATIONS FINALES <i class='fa-solid fa-comment'></i>";
//     button.disabled = false;
// }

function populateAnnotation(url) {
    // var xhr = new XMLHttpRequest();
    // xhr.open("GET", url, true); // true for asynchronous
    // xhr.onload = function() {
    //     if (xhr.readyState === 4 && xhr.status === 200) {
    //         window.open(`/${APP_NAME}/${work}/${idManifest}/show/`, "_blank");
    //         clearLoadingEdit(idButton);
    //     } else {
    //         showMessage(`Failed to display ${url} due to ${xhr.status}: ${xhr.statusText}`, idManifest);
    //     }
    // }
    // xhr.send(null);
    fetch(url)
        .then(response => {
            if (response.ok) {
                window.open(`/${APP_NAME}/${work}/${idManifest}/show/`, "_blank");
                clearLoading(idButton, innerHtml)
                clearLoadingEdit(idButton);
            } else {
                throw new Error(`Failed to display ${url} due to ${response.status}: ${response.statusText}`);
            }
        })
        .catch(error => {
            showMessage(error.message, idManifest);
        });
}
