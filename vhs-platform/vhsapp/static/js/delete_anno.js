function showMessage(message) {
    var messages = document.getElementById(idMessage);
    messages.textContent = message;
    messages.style.display = "block";
}

function send_deletion(idBbox){
    const HTTP_SAS = SAS_APP_URL.replace("https", "http");
    const urlDelete = `${SAS_APP_URL}/annotation/destroy?uri=${HTTP_SAS}/annotation/${idBbox}`;
    var xhr = new XMLHttpRequest();
    xhr.open("DELETE", urlDelete, true);
    xhr.onload = function() {
        if (xhr.status === 204) {
            const annoDiv = $(`#ill_${idBbox}`).closest("div");
            annoDiv.fadeOut(function() {
                annoDiv.remove();
            } );
        } else {
            idMessage = `message_${idBbox}`;
            showMessage(`Failed to delete ${urlDelete} due to ${xhr.status}: '${xhr.statusText}'`);
        }
    };
    xhr.send();
}

$(function() {
    $("#delete_illustrations").click(function() {
        let ids = [];
        const checkedAnno = $("[id^=bbox_]:checked");
        checkedAnno.each(function() {
            ids.push($(this).attr("id").split("_").pop());
        });

        if (ids.length > 0) {
            if (confirm(APP_LANG === "en" ? "Are you sure you want to delete corresponding annotations"
                : "Êtes-vous sûr de vouloir supprimer les annotations sélectionnées ?")) {
                for (let i = 0; i < ids.length; i++) {
                    send_deletion(ids[i]);
                }
            } else {
                checkedAnno.prop("checked", false);
            }
        } else {
            alert(APP_LANG === "en" ? "Please select at least one annotation to delete" : "Veuillez sélectionner au moins une image à supprimer.");
        }
    });
} );
