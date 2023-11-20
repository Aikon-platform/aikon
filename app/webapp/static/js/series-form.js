$(function() {
    // CHANGE WITNESS DENOMINATION IN SERIES FORM
    $("#witness_set-group h2").text(VOL);
    const addWit = $(`#witness_set-group a.add-handler`).last();
    addWit.html(APP_LANG === "en" ? `Add another ${VOL}` : `Ajouter un autre ${VOL}`);

    function setWitBlock(witNb = 0, blockId = "") {
        $(`#witness_set-${witNb} > .djn-drag-handler > b`).html(`${capitalize(VOL)}:`);
        setFormBlocks(`witness_set-${witNb}-digitizations-group`, setDigitBlock);
    }
    setFormBlocks("witness_set-group", setWitBlock);
});
