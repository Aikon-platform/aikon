$(function() {
    /**
     * TOGGLE FIELDS FOR DIGIT TYPE
     */

    function hide(div) {
        div.find("input").first().val(null);
        div.hide();
    }

    const digitInlines = $('#digitizations-group [id^="digitizations-"]');
    // TODO remove visualize and annotations if empty
    // TODO enforce the order of the fields

    function getFields(digitType, selectNb = "0"){
        // TODO enforce order of fields, in order to have type select always at first
        const manifestDiv = $(`#digitizations-${selectNb} .field-manifest`).first();
        const pdfDiv = $(`#digitizations-${selectNb} .field-pdf`).first();
        const imageDiv = $(`#digitizations-${selectNb} .field-images`).first();

        switch (digitType) {
            case MAN_ABBR:
                return [manifestDiv, [pdfDiv, imageDiv]]
            case PDF_ABBR:
                return [pdfDiv, [manifestDiv, imageDiv]]
            case IMG_ABBR:
                return [imageDiv, [manifestDiv, pdfDiv]]
            default:
                return [null, [manifestDiv, pdfDiv, imageDiv]]
        }
    }

    function showDigitField(digitSelect, selectNb = null){
        if (selectNb !== null){
            digitSelect = $(`#id_digitizations-${selectNb}-digit_type`);
            digitSelect.change(function () {
                showDigitField(this);
            })
        } else {
            selectNb = $(digitSelect).attr('id').match(/\d+/);
            if (selectNb) { selectNb = parseInt(selectNb[0]) }
        }
        const digitType = $(digitSelect).val()
        if (selectNb !== null){
            lastDigitSelect = selectNb > lastDigitSelect ? selectNb : lastDigitSelect;
            const [divToShow, divsToHide] = getFields(digitType, String(selectNb));
            divsToHide.map(divToHide => hide(divToHide));
            if (divToShow){
                divToShow.show();
            }
        }
    }

    const digitSelects = $('[id^="id_digitizations-"][id$="-digit_type"]');
    let lastDigitSelect = 0;
    digitSelects.each(function() {
        showDigitField(this);
    });
    digitSelects.change(function () {
        showDigitField(this);
    });

    const addDigit = $(`.djn-model-${WEBAPP_NAME}-digitization.add-handler`);
    addDigit.click(function () {
        setTimeout(function () {
            showDigitField(null, lastDigitSelect + 1);
        }, 100);
    })


    /**
     * TOGGLE FIELDS FOR WITNESS TYPE
     */
    const titleDiv = $(".field-title").first();
    const volumeDiv = $(".field-volume").first();
    const witTypeSelect = $("#id_type");

    function showPrintFields(witType) {
        // TODO deactivate pour le series form
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
    $("div[id$='-contents-group'] h2, div[id$='-contents-group'] h3").remove();

    // Select the anchor element, change the text, and set the target attribute
    $(".djn-drag-handler a").text(WIT_CHANGE).attr("target", "_blank");

    // TODO if folio is selected, allow "r" or "v" at the end of the page fields
});
