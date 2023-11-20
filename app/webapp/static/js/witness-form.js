$(function() {
    /**
     * TOGGLE FIELDS FOR WITNESS TYPE
     */
    const titleDiv = $(".field-title").first();
    const volumeDiv = $(".field-volume").first();
    const witTypeSelect = $("#id_type");

    function showPrintFields(witType) {
        switch (witType) {
            case TPR_ABBR: case WPR_ABBR:
                [titleDiv, volumeDiv].map(div => div.show())
                break
            case MS_ABBR: default:
                [titleDiv, volumeDiv].map(div => hide(div))
                break
        }
    }

    showPrintFields(witTypeSelect.val());
    witTypeSelect.change(function () {
        showPrintFields($(this).val());
    });

    // TODO if folio is selected, allow "r" or "v" at the end of the page fields

    // lastDigitNb = 0;
    setFormBlocks("digitizations-group", setDigitBlock);

});
