import {derived, writable} from 'svelte/store';
import {csrfToken, regionsType, appLang} from '../constants';


function createSelectionStore() {
    // TODO make isRegion a parameter or make everything modelName centered
    const docSetTemplate = {
        "id": null, // <null|document_set_id>
        "type": "documentSet",
        "title": appLang === "en" ? "Document set" : "Set de document", // <string>
        "selected": {}, // <{model_name: {record_id: {record_meta}, record_id: {record_meta}}, model_name: {...}, ...}>
    }
    const regionsSetTemplate = {
        "id": null, // <null|regions_set_id>
        "type": "regionsSet",
        "title": appLang === "en" ? "Regions set" : "Set de régions", // <string>
        "selected": {} // <{regionsType: {record_id: {record_meta}, record_id: {record_meta}, ...}}>
    }
    const selectedRecords = JSON.parse(localStorage.getItem("documentSet")) || docSetTemplate;
    const selectedRegions = JSON.parse(localStorage.getItem("regionsSet")) || regionsSetTemplate;
    const selection = writable({
        records: selectedRecords,
        regions: selectedRegions
    });
    const { subscribe, update } = selection;

    const isSaved = writable(false);

    function store(selection, saved= false) {
        isSaved.set(saved);
        localStorage.setItem(selection.type, JSON.stringify(selection));
    }

    function getSelected(selection, isRegion) {
        return selection[isRegion ? "regions" : "records"]?.selected || {};
    }
    function filter(selection, isRegion = true) {
        const selected = getSelected(selection, isRegion);
        // TODO make usage more consistent
        return isRegion ? selected[regionsType] ?? {} : Object.entries(selected);
    }

    // TODO load from database

    function remove(selection, itemId, itemType) {
        const isRegion = itemType === regionsType;
        const key = isRegion ? "regions" : "records";
        const set = selection[key];

        const { [itemId]: _, ...rest } = set.selected[itemType];

        selection[key] = {
            ...set,
            selected: {...set.selected, [itemType]: rest}
        };

        store(selection[key]);
        return selection;
    }

    function removeAll(selection, itemIds, itemType) {
        const isRegion = itemType === regionsType;
        const key = isRegion ? "regions" : "records";
        const set = selection[key];
        let selected = set.selected[itemType];

        if (!selected || !Object.keys(selected).length) return selection;

        itemIds.forEach(itemId => {
            delete selected[itemId];
        });

        selection[key] = {
            ...set,
            selected: {...set.selected, [itemType]: selected}
        };

        store(selection[key]);
        return selection;
    }

    function add(selection, item, storing = true) {
        const key = item.type === regionsType ? "regions" : "records";
        const set = selection[key];
        const selected = set.selected;

        const itemMeta = item.type === regionsType ? item : {title: item.title, url: item.url};

        selection[key] = {
            ...set,
            selected: {
                ...selected,
                [item.type]: {
                    ...(selected[item.type] || {}),
                    [item.id]: itemMeta
                }
            }
        };

        if (storing) store(selection[key]);
        return selection;
    }
    function addAll(selection, items) {
        const isRegion = items[0].type === regionsType;
        items.forEach(item => {
            selection = add(selection, item, false)
        });

        store(selection[isRegion ? "regions" : "records"]);
        return selection;
    }
    function save(selection, isRegion) {
        const modelName = isRegion ? "regions-set" : "document-set";
        if (isRegion) {
            window.alert("Region set management is not yet implemented");
            // todo implement region set
            return selection;
        }

        let set = selection[isRegion ? "regions" : "records"];

        let selectedIds = {};
        Object.entries(set.selected).forEach(([modelName, records]) => {
            selectedIds[modelName] = Object.keys(records);
        });

        const endpoint = set.id !== null ? `${set.id}/change` : "add";

        fetch(`${window.location.origin}/${modelName}/${endpoint}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify({
                'title': set.title,
                ...selectedIds
            })
        })
        .then(response => response.json())
        .then(data => {
            if (!data?.document_set_id) {
                throw new Error('Failed to save selection');
            }
            update(currentSelection => {
                const set = currentSelection[isRegion ? "regions" : "records"];
                set.id = data.document_set_id;
                set.title = data.document_set_title;
                isSaved.set(true);
                return currentSelection;
            });
            // TODO if saved, btn for treatment
        })
        .catch(error => console.error('Error:', error));

        return selection;
    }

    function getDocumentSetId() {
        let docSetId;
        update(currentSelection => {
            docSetId = currentSelection.records.id;
            return currentSelection;
        });
        return docSetId;
    }

    return {
        subscribe,
        save: (isRegion) => update(selection => save(selection, isRegion)),
        empty: (isRegion) => update(selection => {
            selection[isRegion ? "regions" : "records"].selected = {};
            store(selection[isRegion ? "regions" : "records"]);
            return selection
        }),
        removeAll: (itemIds, itemType) => update(selection => removeAll(selection, itemIds, itemType)),
        remove: (itemId, itemType) => update(selection => remove(selection, itemId, itemType)),
        addAll: (items) => update(selection => addAll(selection, items)),
        add: (item) => update(selection => add(selection, item)),
        toggle: (item) => update(selection => {
            const selected = getSelected(selection, item.type === regionsType);
            if (selected[item.type]?.[item.id]) {
                return remove(selection, item.id, item.type);
            } else {
                return add(selection, item);
            }
        }),
        updateTitle: (newTitle, isRegion) => update(selection => {
            const key = isRegion ? "regions" : "records";
            selection[key] = { ...selection[key], title: newTitle };
            store(selection[key], true);
            return selection;
        }),
        // REACTIVE STATEMENT
        isSaved,
        isSelected: derived(selection, $selection =>
            item => getSelected($selection, item.type === regionsType)[item.type]?.hasOwnProperty(item.id) || false
        ),
        selected: derived(selection, $selection =>
            isRegion => filter($selection, isRegion)
        ),
        nbSelected: derived(selection, $selection =>
            isRegion => {
                const selected = filter($selection, isRegion);
                if (isRegion) {
                    return Object.keys(selected).length;
                }
                return selected.reduce(
                    (count, [_, selectedItems]) => count + Object.keys(selectedItems).length, 0
                )
            }
        ),
        selectionTitle: derived(selection, $selection =>
            isRegion => {
                return $selection[isRegion ? "regions" : "records"].title;
            }
        ),
        getDocumentSetId
    };
}
export const selectionStore = createSelectionStore();
