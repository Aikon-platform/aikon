$(function() {
    $(".djn-drag-handler a").text(WIT_CHANGE).attr("target", "_blank");

    // CHANGE WITNESS DENOMINATION IN SERIES FORM
    $("#witness_set-group h2").text(VOL);
    const addWit = $(`#witness_set-group a.add-handler`).last();
    addWit.html(APP_LANG === "en" ? `Add another ${capitalize(VOL)}` : `Ajouter un autre ${capitalize(VOL)}`);

    function setWitBlock(witNb = 0, blockId = "") {
        $(`#witness_set-${witNb} > .djn-drag-handler > b`).html(`${capitalize(VOL)}:`);
        setFormBlocks(`witness_set-${witNb}-digitizations-group`, setDigitBlock);
    }
    setFormBlocks("witness_set-group", setWitBlock);
});
