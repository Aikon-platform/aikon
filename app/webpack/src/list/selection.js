export function updateSelection(selection) {
    localStorage.setItem("documentSet", JSON.stringify(selection));
}

export function saveSelection(selection) {
    console.log(selection);
    // api call to save selection in database
    // receive id of saved
}

export function getSelection() {
    return JSON.parse(localStorage.getItem("documentSet"));
}

export function emptySelection() {
    updateSelection({});
    return {}
}

export function removeFromSelection(selection, blockId, blockType) {
    const { [blockId]: _, ...rest } = selection[blockType];
    selection[blockType] = rest;
    updateSelection(selection);
    return selection;
}

 export function addToSelection(selection, block) {
    // todo add only id and title to selection?
    if (!selection.hasOwnProperty(block.type)) {selection[block.type] = []}
    selection[block.type] = { ...selection[block.type], [block.id]: block };
    updateSelection(selection);
    return selection;
}
