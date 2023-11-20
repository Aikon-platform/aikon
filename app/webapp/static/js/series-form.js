isSeriesForm = true;

$(function() {
    // CHANGE WITNESS DENOMINATION IN SERIES FORM
    $("#witness_set-group h2").text(VOL);
    const addWit = $(`#witness_set-group a.add-handler`).last();
    addWit.html(APP_LANG === "en" ? `Add another ${VOL}` : `Ajouter un autre ${VOL}`);

    lastWitNb = -1; lastDigitNb = -1; // minus one because by default there is no block defined
    function setWitBlock(witNb = null, blockId = "") {
        lastWitNb = witNb > lastWitNb ? witNb : lastWitNb + 1;
        $(`#witness_set-${witNb ?? 0} > .djn-drag-handler > b`).html(`${capitalize(VOL)}:`);
        setFormBlocks(`witness_set-${witNb}-digitizations-group`, setDigitBlock);
    }
    setFormBlocks("witness_set-group", setWitBlock);
});
