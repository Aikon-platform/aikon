import {derived, writable} from 'svelte/store';

const regionsType = "Regions"

function createSelectionStore() {
    const selection = writable(JSON.parse(localStorage.getItem("documentSet")) || {});
    const { subscribe, get, update } = selection;

    const isSelected = derived(selection, $selection =>
        item => $selection[item.type]?.hasOwnProperty(item.id) || false
    );
    const selected = derived(selection, $selection =>
        isRegion => filter($selection, isRegion)
    )
    const nbSelected = derived(selection, $selection =>
        isRegion => {
            const selected = filter($selection, isRegion)
            if (isRegion) {
                return Object.keys(selected).length;
            }
            return selected.reduce(
                (count, [_, selectedItems]) => count + Object.keys(selectedItems).length, 0
            )
        }
    )

    function store(selection) {
        localStorage.setItem("documentSet", JSON.stringify(selection));
    }
    function filter(selection, isRegion = true) {
        if (isRegion) {
            return selection[regionsType] ?? {};
        }
        return Object.entries(selection).filter(([type, _]) => type !== regionsType)
    }

    function remove(selection, itemId, itemType) {
        if (selection[itemType]) {
            const { [itemId]: _, ...rest } = selection[itemType];
            selection = {...selection, [itemType]: rest};
        }
        store(selection);
        return selection;
    }
    function removeAll(selection, itemIds, itemType) {
        if (!selection[itemType]) {
            return selection
        }
        itemIds.forEach(itemId => {
            delete selection[itemType][itemId];
        });

        store(selection);
        return selection;
    }

    function add(selection, item) {
        // todo add only id and title to selection?
        if (!selection.hasOwnProperty(item.type)) {
            selection[item.type] = {};
        }
        selection[item.type] = { ...selection[item.type], [item.id]: item };
        store(selection);
        return selection;
    }
    function addAll(selection, items) {
        items.forEach(item => {
            if (!selection[item.type]) {
                selection[item.type] = {};
            }
            selection[item.type][item.id] = item;
        });

        store(selection);
        return selection;
    }

    return {
        subscribe,
        save: () => update(selection => {
            console.log(selection);
            // api call to save selection in database
            // receive id of saved
            return selection
        }),
        empty: (isRegion) => update(selection => {
            if (isRegion) {
                delete selection[regionsType];
            } else {
                Object.keys(selection).forEach(type => {
                    if (type !== regionsType) { delete selection[type] }
                });
            }
            store(selection);
            return selection
        }),
        addAll: (items) => update(selection => addAll(selection, items)),
        removeAll: (itemIds, itemType) => update(selection => removeAll(selection, itemIds, itemType)),
        remove: (itemId, itemType) => update(selection => remove(selection, itemId, itemType)),
        add: (item) => update(selection => add(selection, item)),
        toggle: (item) => update(selection => {
            if (selection[item.type]?.[item.id]) {
                return remove(selection, item.id, item.type);
            } else {
                return add(selection, item);
            }
        }),
        toggleAll: (isRegion, items, areAllSelected) => update(selection => {
            // if (areAllSelected) {
            //     return removeAll(selection, item.id, item.type);
            // } else {
            //     return addAll(selection, items);
            // }
        }),
        isSelected,
        selected,
        nbSelected
    };
}
export const selectionStore = createSelectionStore();
