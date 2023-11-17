function hide(div) {
    if (div){
        div.find("input").first().val(null);
        div.hide();
    }
}

// Remove all h2/h3 tags inside the selected div
$("div[id$='-contents-group'] h2, div[id$='-contents-group'] h3").remove();

// Select the anchor element, change the text, and set the target attribute
$(".djn-drag-handler a").text(WIT_CHANGE).attr("target", "_blank");

/**
 * TOGGLE FIELDS IN DIGIT BLOCK
 */
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

function setDigitBlock(digitNb = null) {
    const prefix = isSeriesForm ? "" : ""; // TODO set prefix here
    lastDigitNb = digitNb > lastDigitNb ? digitNb : lastDigitNb + 1;

    const viewDigit = $(`#${prefix}digitizations-${digitNb} .field-view_digit`).first();
    const viewAnno = $(`#${prefix}digitizations-${digitNb} .field-view_anno`).first();
    const hasDigit = viewDigit.length !== 0

    const manifestDiv = $(`#${prefix}digitizations-${digitNb} .field-manifest`).first();
    const pdfDiv = $(`#${prefix}digitizations-${digitNb} .field-pdf`).first();
    const imageDiv = $(`#${prefix}digitizations-${digitNb} .field-images`).first();

    let fields = [manifestDiv, pdfDiv, imageDiv, viewDigit, viewAnno]

    if (hasDigit && viewDigit.find('p').first().text() !== "-"){
        // if a digitization has already been uploaded
        // hide fields to upload new digit
        const digitTypeDiv = $(`#${prefix}digitizations-${digitNb} .field-digit_type`).first();
        let divsToHide = [digitTypeDiv, manifestDiv, pdfDiv, imageDiv];
        // if no annotations were yet generated
        if (viewAnno.find('p').first().text() === "-"){
            divsToHide.push(viewAnno)
        }
        divsToHide.map(divToHide => divToHide.hide());
    } else {
        // if not, show only field related to upload
        const digitSelect = $(`#${prefix}id_digitizations-${digitNb}-digit_type`);
        digitSelect.change(function () { toggleDigitFields(digitSelect, fields); });
        toggleDigitFields(digitSelect, fields);
    }

    const digitType = $(this).find(`.field-digit_type`).first();
    digitType.detach().prependTo($(this).find("fieldset.djn-module"))
}

function setFormBlocks(blockContainerId, callback){
    const idPrefix = blockContainerId.replace("-group", "");
    const blocks = $(`#${blockContainerId} [id^="${idPrefix}-"]`);

    blocks.each(function() {
        const blockNb = parseInt($(this).attr('id').split('-')[1]);
        if (isNaN(blockNb)) {
            return
        }
        callback(blockNb);
    });
// =======
//     function setDigitBlock(digitNb, prefix) {
//         lastDigitNb = digitNb > lastDigitNb ? digitNb : lastDigitNb
//
//         const viewDigit = $(`#${prefix}digitizations-${digitNb} .field-view_digit`).first();
//         const viewAnno = $(`#${prefix}digitizations-${digitNb} .field-view_anno`).first();
//         const hasDigit = viewDigit.length !== 0
//
//         const manifestDiv = $(`#${prefix}digitizations-${digitNb} .field-manifest`).first();
//         const pdfDiv = $(`#${prefix}digitizations-${digitNb} .field-pdf`).first();
//         const imageDiv = $(`#${prefix}digitizations-${digitNb} .field-images`).first();
//
//         let fields = [manifestDiv, pdfDiv, imageDiv, viewDigit, viewAnno]
//
//         if (hasDigit && viewDigit.find('p').first().text() !== "-"){
//             // if a digitization has already been uploaded
//             // hide fields to upload new digit
//             const digitTypeDiv = $(`#${prefix}digitizations-${digitNb} .field-digit_type`).first();
//             let divsToHide = [digitTypeDiv, manifestDiv, pdfDiv, imageDiv];
//             // if no annotations were yet generated
//             if (viewAnno.find('p').first().text() === "-"){
//                 divsToHide.push(viewAnno)
//             }
//             divsToHide.map(divToHide => divToHide.hide());
//         } else {
//             // if not, show only field related to upload
//             const digitSelect = $(`#id_${prefix}digitizations-${digitNb}-digit_type`);
//             digitSelect.change(function () { toggleDigitFields(digitSelect, fields); });
//             toggleDigitFields(digitSelect, fields);
//         }
//
//         const digitType = $(this).find(`.field-digit_type`).first();
//         digitType.detach().prependTo($(this).find("fieldset.djn-module"))
//     }
//
//     const addDigit = $(`.djn-model-${WEBAPP_NAME}-digitization.add-handler`);
//     addDigit.click(function () {
//         setTimeout(function () {
//             setDigitBlock(lastDigitNb + 1, prefix);
//         }, 100);
//     })
//
//     // const digitBlocks = $('#digitizations-group [id^="digitizations-"]');
//     const digitBlocks = $('[id$="digitizations-group"] [id^="digitizations-"], [id$="digitizations-group"] [id^="witness_set-"]');
//
//     digitBlocks.each(function() {
//         // const digitNb = parseInt($(this).attr('id').split('-')[1]);
//         const digitNb = $(this).attr('id').split('-').pop();
//         prefix = $(this).attr('id').split('digitizations')[0];
//         if (isNaN(digitNb)){
//             return
//         }
//         setDigitBlock(digitNb, prefix);
// >>>>>>> 937a7eb112f1ff48359b8c3ea11e498893321b8c

    const addBlock = $(`#${blockContainerId} a.add-handler`).first();
    addBlock.click(function () {
        setTimeout(function () { callback() }, 50);
    });
}
