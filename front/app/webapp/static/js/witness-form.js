$(function() {
    /**
     * TOGGLE FIELDS FOR WITNESS TYPE
     */
    const titleDiv = $(".field-volume_nb").first();
    const volumeDiv = $(".field-volume_title").first();
    const editionDiv = $(".field-edition").first();
    const witTypeSelect = $("#id_type");
    const pageNbInput = $("#id_nb_pages");
    const pageTypeSelect = $("#id_page_type");

    function showPrintFields(witType) {
        switch (witType) {
            case TPR_ABBR: case WPR_ABBR:
                [titleDiv, volumeDiv, editionDiv].map(div => div.show())
                break
            case MS_ABBR: default:
                [titleDiv, volumeDiv, editionDiv].map(div => hide(div))
                break
        }
    }

    showPrintFields(witTypeSelect.val());
    witTypeSelect.change(function () {
        showPrintFields($(this).val());
    });

    function hideContentBlocks(contentNb = 1){
        const contentBlock = $(`#contents-${contentNb}`);
        if (contentBlock.length !== 0){
            contentBlock.hide();
            hideContentBlocks(contentNb + 1)
        }
    }

    function toggleContentBlock(contentNb){
        const isCompleteCheckbox = $(`#id_contents-${contentNb}-whole_witness`);
        if (contentNb !== 0){
            isCompleteCheckbox.attr("checked", false);
            isCompleteCheckbox.hide();
            return;
        }
        const isComplete = isCompleteCheckbox.is(":checked");
        // const pagesDiv = $(`#contents-0 .form-row.field-page_min.field-page_max`).first();
        if (isComplete){
            const pageNb = pageNbInput.val();
            if (pageNb){
                const [min, max] = [$(`#id_contents-0-page_min`), $(`#id_contents-0-page_max`)];
                min.val(pageTypeSelect.val() === "fol" ? "1r" : "1");
                max.val(pageTypeSelect.val() === "fol" ? `${pageNb}v` : pageNb);
            }
            // pagesDiv.hide();
            hideContentBlocks();
            $(`#contents-group a.add-handler`).last().parent().hide();
        } else {
            // pagesDiv.show();
            $(`#contents-group a.add-handler`).last().parent().show();
        }
    }

    function setContentBlock(){
        toggleContentBlock(0);
        $(`#id_contents-0-whole_witness`).change(function () {
            toggleContentBlock(0);
        });
    }

    // TODO if folio is selected, allow "r" or "v" at the end of the page fields

    setFormBlocks("digitizations-group", setDigitBlock);
    setContentBlock();
});
