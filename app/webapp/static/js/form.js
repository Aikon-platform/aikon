function hide(div) {
    if (div){
        div.find("input").first().val(null);
        div.hide();
    }
}

/**
 * TOGGLE FIELDS IN DIGIT BLOCK
 */
function getFields(digitType, fields){
    const [manifestDiv, pdfDiv, imageDiv, viewDigit, viewAnno, sourceDiv, freeDiv] = fields
    switch (digitType) {
        case MAN_ABBR:
            return [[manifestDiv], [pdfDiv, imageDiv, viewDigit, viewAnno, sourceDiv, freeDiv]]
        case PDF_ABBR:
            return [[pdfDiv, freeDiv, sourceDiv], [manifestDiv, imageDiv, viewDigit, viewAnno]]
        case IMG_ABBR:
            return [[imageDiv, freeDiv, sourceDiv], [manifestDiv, pdfDiv, viewDigit, viewAnno]]
        default:
            return [null, [manifestDiv, pdfDiv, imageDiv, viewDigit, viewAnno, sourceDiv, freeDiv]]
    }
}

function toggleDigitFields(digitSelect, fields) {
    const [divsToShow, divsToHide] = getFields($(digitSelect).val(), fields);
    divsToHide.map(divToHide => hide(divToHide));
    if (divsToShow){
        divsToShow.map(divToShow => divToShow.show());
    }
}

let treatedDigits = {};

function setDigitBlock(digitNb = 0, digitBlockId= "") {
    const prefix = digitBlockId.split('digitizations')[0];

    if (treatedDigits[`#${prefix}digitizations-${digitNb}`]){
        return
    }
    treatedDigits[`#${prefix}digitizations-${digitNb}`] = true;

    const viewDigit = $(`#${prefix}digitizations-${digitNb} .field-view_digit`).first();
    const viewAnno = $(`#${prefix}digitizations-${digitNb} .field-view_regions`).first();
    const hasDigit = viewDigit.length !== 0

    const manifestDiv = $(`#${prefix}digitizations-${digitNb} .field-manifest`).first();
    const pdfDiv = $(`#${prefix}digitizations-${digitNb} .field-pdf`).first();
    const imageDiv = $(`#${prefix}digitizations-${digitNb} .field-images`).first();

    const sourceDiv = $(`#${prefix}digitizations-${digitNb} .field-source`).first();
    const freeDiv = $(`#${prefix}digitizations-${digitNb} .field-is_open`).first();

    let fields = [manifestDiv, pdfDiv, imageDiv, viewDigit, viewAnno, sourceDiv, freeDiv];

    if (hasDigit && viewDigit.find('div.readonly').first().text() !== "-"){
        // if a digitization has already been uploaded
        // hide fields to upload new digit
        const digitTypeDiv = $(`#${prefix}digitizations-${digitNb} .field-digit_type`).first();
        let divsToHide = [digitTypeDiv, manifestDiv, pdfDiv, imageDiv, sourceDiv];
        // if no annotations were yet generated
        const annoText = viewAnno.find('div.readonly').first().text();
        if (annoText === "-" || annoText === ""){
            divsToHide.push(viewAnno)
        }
        divsToHide.map(divToHide => divToHide.hide());
    } else {
        // if not, show only field related to upload
        const digitSelect = $(`#id_${prefix}digitizations-${digitNb}-digit_type`);
        digitSelect.change(function () { toggleDigitFields(digitSelect, fields); });
        toggleDigitFields(digitSelect, fields);
    }

    const digitType = $(this).find(`.field-digit_type`).first();
    digitType.detach().prependTo($(this).find("fieldset.djn-module"))
}

function setFormBlocks(blockContainerId, callback){
    const idPrefix = blockContainerId.replace("-group", "");
    const blockSelector= `#${blockContainerId} [id^="${idPrefix}-"]`;

    $(blockSelector).each(function() {
        const blockId = $(this).attr('id')
        const blockNb = parseInt(blockId.replace(`${idPrefix}-`, "").split("-")[0]);
        if (isNaN(blockNb)) {
            return
        }
        callback(blockNb, blockId);
    });

    const addBlock = $(`#${blockContainerId} a.add-handler`).last();
    addBlock.click(function () {
        setTimeout(function () {
            const addedBlock = $(blockSelector).filter(":visible").last();
            const addedBlockId = addedBlock.attr('id');
            const addedBlockNb = parseInt(addedBlockId.replace(`${idPrefix}-`, "").split("-")[0]);

            if (isNaN(addedBlockNb)) {
                return
            }
            callback(addedBlockNb, addedBlockId);
        }, 50);
    });
}
