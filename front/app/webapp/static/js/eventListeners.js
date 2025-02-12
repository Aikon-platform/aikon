$(function() {
    $("[id$=-pdf]").attr("accept", "application/pdf"); // todo check if necessary

    $("p.url a, span.inline_label a, div.readonly a, .field-image p a, p.file-upload a").attr("target", "_blank");

    // Allow multiple image selection
    $(`[id^="id_digitizations-"][id$="-images"]`).attr("multiple", true);

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
