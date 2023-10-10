$(function() {
    /**
     * TOGGLE FIELDS FOR DIGIT TYPE
     */

    function hide(div) {
        div.find("input").first().val(null);
        div.hide();
    }

    function getFields(digitType, selectNb = "0"){
        const manifestDiv = $(`#digitizations-${selectNb} .field-manifest`).first();
        const pdfDiv = $(`#digitizations-${selectNb} .field-pdf`).first();
        const imageDiv = $(`#digitizations-${selectNb} .field-images`).first();

        switch (digitType) {
            case "man": // TODO use variables defined in model constants
                return [manifestDiv, [pdfDiv, imageDiv]]
            case "pdf":
                return [pdfDiv, [manifestDiv, imageDiv]]
            case "img":
                return [imageDiv, [manifestDiv, pdfDiv]]
            default:
                return [null, [manifestDiv, pdfDiv, imageDiv]]
        }
    }

    function showDigitField(digitSelect){
        const selectNb = $(digitSelect).attr('id').match(/\d+/);
        const digitType = $(digitSelect).val()
        if (selectNb){
            const [divToShow, divsToHide] = getFields(digitType, selectNb);

            divsToHide.map(divToHide => hide(divToHide));
            if (divToShow){
                divToShow.show();
            }
        }
    }

    const digitSelects = $('[id^="id_digitizations-"][id$="-digit_type"]');
    digitSelects.each(function() {
        showDigitField(this);
    });
    digitSelects.change(function () {
        showDigitField(this);
    });

    /**
     * TOGGLE FIELDS FOR WITNESS TYPE
     */
    const titleDiv = $(".field-title").first();
    const volumeDiv = $(".field-volume").first();
    const witTypeSelect = $("#id_type");

    function showPrintFields(witType) {
        // TODO desactivate pour le series form
        switch (witType) {
            case "tpr": case "wpr": // TODO use variables defined in model constants
                [titleDiv, volumeDiv].map(div => div.show())
                break
            case "ms": default:
                [titleDiv, volumeDiv].map(div => hide(div))
                break
        }
    }

    showPrintFields(witTypeSelect.val());
    witTypeSelect.change(function () {
        showPrintFields($(this).val());
    });

    // Remove all h2/h3 tags inside the selected div
    $("div[id$='-contents-group'] h2").remove();
    $("div[id$='-contents-group'] h3").remove();

    // TODO if folio is selected, allow "r" or "v" at the end of the page fields
});
