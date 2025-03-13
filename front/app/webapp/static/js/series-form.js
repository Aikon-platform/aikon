$(function() {
    // TODO fix because it is not appearing in the form
    $(".djn-drag-handler a").text(WIT_CHANGE).attr("target", "_blank");

    // CHANGE WITNESS DENOMINATION IN SERIES FORM
    $("#witness_set-group h2").text(VOL.capitalize());
    const addWit = $(`#witness_set-group a.add-handler`).last();
    addWit.html(APP_LANG === "en" ? `Add another ${VOL.capitalize()}` : `Ajouter un autre ${VOL.capitalize()}`);

    function setWitBlock(witNb = 0, blockId = "") {
        $(`#witness_set-${witNb} > .djn-drag-handler > b`).html(`${VOL.capitalize()}:`);
        setFormBlocks(`witness_set-${witNb}-digitizations-group`, setDigitBlock);
    }
    setFormBlocks("witness_set-group", setWitBlock);
});
