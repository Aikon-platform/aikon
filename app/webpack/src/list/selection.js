export function updateSelection(selection) {
    localStorage.setItem("documentSet", JSON.stringify(selection));
}

export function saveSelection(selection) {
    console.log(selection);
    // api call to save selection in database
    // receive id of saved
    return selection
}

export function getSelection() {
    return JSON.parse(localStorage.getItem("documentSet"));
}

export function emptySelection(selection, keysToRemove) {
    keysToRemove.forEach(key => selection.hasOwnProperty(key) ? delete selection[key] : true)
    updateSelection(selection);
    return selection
}

export function selectAll(selection, blocks) {
    blocks.forEach(block => {
        if (!selection[block.type]) {
            selection[block.type] = {};
        }
        selection[block.type][block.id] = block;
    });

    updateSelection(selection);
    return selection;
}

export function removeAll(selection, blockIds, blockType) {
    if (!selection[blockType]) {
        return selection
    }
    blockIds.forEach(blockId => {
        delete selection[blockType][blockId];
    });

    updateSelection(selection);
    return selection;
}

export function removeFromSelection(selection, blockId, blockType) {
    const { [blockId]: _, ...rest } = selection[blockType];
    selection[blockType] = rest;
    updateSelection(selection);
    return selection;
}

 export function addToSelection(selection, block) {
    // todo add only id and title to selection?
    if (!selection.hasOwnProperty(block.type)) {selection[block.type] = {}}
    selection[block.type] = { ...selection[block.type], [block.id]: block };
    updateSelection(selection);
    return selection;
}
