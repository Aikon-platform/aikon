$(function() {
    /**
     * TOGGLE FIELDS FOR DIGIT TYPE
     */

    const manifestDiv = $(".field-manifest").first();
    const pdfDiv = $(".field-pdf").first();
    const imageDiv = $(".field-image").first();
    const digitSelect = $("#id_digitization_set-0-digit_type");

    function hide(div) {
        div.find("input").first().val(null);
        div.hide();
    }

    function toggleDiv(divToShow=null, divs=[manifestDiv, pdfDiv, imageDiv]){
        divs.filter(div => div !== divToShow)
            .map(divToHide => hide(divToHide));
        if (divToShow){
            divToShow.show();
        }
    }

    function showDigitField(digitType) {
        switch (digitType) {
            case "man": // TODO use variables defined in model constants
                toggleDiv(manifestDiv);
                break
            case "pdf":
                toggleDiv(pdfDiv);
                break
            case "img":
                toggleDiv(imageDiv);
                break
            default:
                toggleDiv();
        }
    }

    showDigitField(digitSelect.val());
    digitSelect.change(function () {
        showDigitField($(this).val());
    });

    /**
     * TOGGLE FIELDS FOR WITNESS TYPE
     */
    const titleDiv = $(".field-title").first();
    const volumeDiv = $(".field-volume").first();
    const witTypeSelect = $("#id_type");

    function showPrintFields(witType) {
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
});
