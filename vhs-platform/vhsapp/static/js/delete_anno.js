const HTTP_SAS = SAS_APP_URL.replace("https", "http");

function showMessage(message) {
    var messages = document.getElementById(idMessage);
    messages.textContent = message;
    messages.style.display = "block";
}

function send_deletion(idBbox){
    const urlDelete = `${SAS_APP_URL}/annotation/destroy?uri=${SAS_APP_URL}/annotation/${idBbox}`;
    var xhr = new XMLHttpRequest();
    xhr.open("DELETE", urlDelete, true);
    xhr.onload = function() {
        if (xhr.status === 204) {
            var $td = $(`#ill_${idBbox}`).closest("td");
            $td.fadeOut(function() {
                $td.remove();
            } );
        } else {
            idMessage = `message_${idBbox}`;
            showMessage(`Failed to delete ${urlDelete} due to ${xhr.status}: '${xhr.statusText}'`);
        }
    };
    xhr.send();
}

$(function() {
    $("[id^=bbox_]").change(function() {
        if (this.checked) {
            if (confirm ("Êtes-vous sûr de vouloir supprimer cette image extraite ?")) {
                send_deletion($(this).attr("id").split("_").pop())
            } else {
                $(this).prop("checked", false);
            }
        }
    } );

    $("#delete_illustrations").click(function() {
        const startIndex = parseInt(document.getElementById("startIndex").value);
        const endIndex = parseInt(document.getElementById("endIndex").value);
        if (confirm ("Êtes-vous sûr de vouloir supprimer toutes les images extraites de Vue " + startIndex + " à Vue " + endIndex + " ?")) {
            for (var i = endIndex; i >= startIndex; i--) {
                $("[id]").filter(function() {
                    return this.id.indexOf("bbox_") !== -1;
                }).each(function() {
                    if (i === parseInt(this.id.split("-")["2"])) {
                        send_deletion(this.id.split("_").pop())
                    }
                } );
            }
        }
    } );
} );
