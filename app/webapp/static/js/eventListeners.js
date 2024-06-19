$(function() {
    $("[id$=-pdf]").attr("accept", "application/pdf"); // todo check if necessary

    $("p.url a, span.inline_label a, div.readonly a, .field-image p a, p.file-upload a").attr("target", "_blank");

    // Allow multiple image selection
    $(`[id^="id_digitizations-"][id$="-images"]`).attr("multiple", true);


    // $(document).on("click", "[id^=annotate_manifest_]", function(e) {
    //     e.preventDefault();
    //
    //     const idButton = $(this).attr("id");
    //     const witnessId = idButton.split("_").pop();
    //
    //     if (idButton.includes("annotate_manifest_auto_")) {
    //         viewAnnotations(witnessId)
    //         return false;
    //     }
    //     editAnnotations(witnessId, idButton)
    //     return false;
    // }).on("click", "[id^=manifest_final_]", function(e) {
    //     finalAnnotations($(this)); // todo
    // }).on("click", ".add-handler", function(e) {
    //     ("#id_volume_set-__prefix__-title").val($("#id_work").text());
    //     $("#id_volume_set-__prefix__-place").val($("#id_place").val());
    //     $("#id_volume_set-__prefix__-date").val($("#id_date").val());
    //     $("#id_volume_set-__prefix__-publishers_booksellers").val($("#id_publishers_booksellers").val());
    //     $("#id_volume_set-__prefix__-manifest_final").replaceWith("<i class='fa-solid fa-circle-xmark' style='color:red'></i>");
    // });

    $("#delete_regions").click(function() {
        const checkedRegions = $("[id^=bbox_]:checked");
        let regionsIds = [];
        checkedRegions.each(function() {
            regionsIds.push($(this).attr("id").replace("bbox_", ""));
        });
        if (!deleteRegions(regionsIds)) {
            // if the user decided to not delete the selected regions
            checkedRegions.prop("checked", false);
        }
    });

    $("#select_regions").click(function() {
        const checkedRegions = $("[id^=bbox_]");
        checkedRegions.each(function() {
            $(this).prop("checked", true);
        });
    });

    $("#delete_all").click(function() {
        deleteAllRegions(allRegions ?? []);
    });

    $("#validate_regions").click(function() {
        validateRegions();
    });
});
