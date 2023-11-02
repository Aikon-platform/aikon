$(function() {
    function hide(div) {
        if (div){
            div.find("input").first().val(null);
            div.hide();
        }
    }

    /**
     * TOGGLE FIELDS IN DIGIT BLOCK
     */
    let lastDigitNb = 0;
    function getFields(digitType, fields){
        const [manifestDiv, pdfDiv, imageDiv, viewDigit, viewAnno] = fields
        switch (digitType) {
            case MAN_ABBR:
                return [manifestDiv, [pdfDiv, imageDiv, viewDigit, viewAnno]]
            case PDF_ABBR:
                return [pdfDiv, [manifestDiv, imageDiv, viewDigit, viewAnno]]
            case IMG_ABBR:
                return [imageDiv, [manifestDiv, pdfDiv, viewDigit, viewAnno]]
            default:
                return [null, [manifestDiv, pdfDiv, imageDiv, viewDigit, viewAnno]]
        }
    }

    function toggleDigitFields(digitSelect, fields) {
        const [divToShow, divsToHide] = getFields($(digitSelect).val(), fields);
        divsToHide.map(divToHide => hide(divToHide));
        if (divToShow){
            divToShow.show();
        }
    }

    function setDigitBlock(digitNb) {
        lastDigitNb = digitNb > lastDigitNb ? digitNb : lastDigitNb

        const viewDigit = $(`#digitizations-${digitNb} .field-view_digit`).first();
        const viewAnno = $(`#digitizations-${digitNb} .field-view_anno`).first();
        const hasDigit = viewDigit.length !== 0

        const manifestDiv = $(`#digitizations-${digitNb} .field-manifest`).first();
        const pdfDiv = $(`#digitizations-${digitNb} .field-pdf`).first();
        const imageDiv = $(`#digitizations-${digitNb} .field-images`).first();

        let fields = [manifestDiv, pdfDiv, imageDiv, viewDigit, viewAnno]

        if (hasDigit && viewDigit.find('p').first().text() !== "-"){
            // if a digitization has already been uploaded
            // hide fields to upload new digit
            const digitTypeDiv =$(`#digitizations-${digitNb} .field-digit_type`).first();
            [digitTypeDiv, manifestDiv, pdfDiv, imageDiv].map(divToHide => divToHide.hide());
        } else {
            // if not, show only field related to upload
            const digitSelect = $(`#id_digitizations-${digitNb}-digit_type`);
            digitSelect.change(function () { toggleDigitFields(digitSelect, fields); });
            toggleDigitFields(digitSelect, fields);
        }

        const digitType = $(this).find(`.field-digit_type`).first();
        digitType.detach().prependTo($(this).find("fieldset.djn-module"))
    }

    const addDigit = $(`.djn-model-${WEBAPP_NAME}-digitization.add-handler`);
    addDigit.click(function () {
        setTimeout(function () {
            setDigitBlock(lastDigitNb + 1);
        }, 100);
    })

    const digitBlocks = $('#digitizations-group [id^="digitizations-"]');

    digitBlocks.each(function() {
        const digitNb = parseInt($(this).attr('id').split('-')[1]);
        if (isNaN(digitNb)){
            return
        }
        setDigitBlock(digitNb);
    });

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
