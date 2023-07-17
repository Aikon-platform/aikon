$(function() {
    /**
     * TOGGLE FIELDS FOR WITNESS TYPE
     */

    const titleDiv = $(".field-title").first();
    const volumeDiv = $(".field-volume").first();

    [titleDiv, volumeDiv].map(div => div.hide())

    $("#id_type").change(function () {
        switch ($(this).val()) {
            case "ms": // TODO use variables defined in model constants
                // todo hide and empty "print fields"
                break
            case "tpr": case "wpr":
                // todo show "print fields"
                break
            default:
                // todo same as ms
        }
    });

    /**
     * TOGGLE FIELDS FOR DIGIT TYPE
     */

    const manifestDiv = $(".field-manifest").first();
    const pdfDiv = $(".field-pdf").first();
    const imageDiv = $(".field-image").first();

    [manifestDiv, pdfDiv, imageDiv].map(div => div.hide())

    function toggleDiv(divToShow=null){
        [manifestDiv, pdfDiv, imageDiv]
            .filter(div => div !== divToShow)
            .map(divToHide => {
                divToHide.find("input").first().val(null); // TODO: maybe empty value on submit
                divToHide.hide();
            });
        if (divToShow){
            divToShow.show();
        }
    }

    $("#id_digitization_set-0-digit_type").change(function () {
        switch ($(this).val()) {
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
    });
});
