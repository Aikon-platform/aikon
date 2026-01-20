import {derived, writable, get} from 'svelte/store';
import {csrfToken, appLang} from '../constants';

function createTypedSelectionStore(config) {
    const {
        type,
        modelName,
        title,
        extractMeta = (item) => item // by default, keep item as it is
    } = config;

    const template = {
        id: null,
        type,
        title,
        is_public: false,
        // <{model_name: {record_id: {record_meta}, record_id: {record_meta}}, model_name: {...}, ...}>
        selected: {}
    };

    const initialData = JSON.parse(localStorage.getItem(type)) || template;
    const selection = writable(initialData);
    const isSaved = writable(false);

    function store(data, saved = false) {
        isSaved.set(saved);
        localStorage.setItem(type, JSON.stringify(data));
    }

    function save() {
        selection.update(set => {
            if (type !== 'documentSet') {
                console.error("Document set management is the only type currently supported for saving.");
                return set;
            }

            const selectedIds = Object.fromEntries(
                Object.entries(set.selected).map(([model, records]) =>
                    [model, Object.keys(records)]
                )
            );

            const endpoint = set.id ? `${set.id}/edit` : "new";

            fetch(`${window.location.origin}/${modelName}/${endpoint}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify({
                    title: set.title,
                    is_public: set.is_public,
                    selection: set,
                    ...selectedIds
                })
            })
            .then(res => res.json())
            .then(data => {
                if (!data?.document_set_id) throw new Error('Failed to save');
                selection.update(current => {
                    current.id = data.document_set_id;
                    current.title = data.document_set_title;
                    current.is_public = data.is_public;
                    store(current, true);
                    return current;
                });
            })
            .catch(err => console.error('Error:', err));

            return set;
        });
    }

    const loadSet = (setData) => selection.update(() => {
        const newSet = setData.selection.id ? setData.selection : {...setData.selection, id: setData.id};
        store(newSet);
        return newSet;
    });

    const unloadSet = () => selection.update(() => {
        const newSet = {...template, selected: {}};
        store(newSet);
        return newSet;
    });

    return {
        type,
        subscribe: selection.subscribe,

        add: (item) => selection.update(set => {
            set.selected[item.class] = {
                ...(set.selected[item.class] || {}),
                [item.id]: extractMeta(item)
            };
            store(set);
            return set;
        }),

        addAll: (items) => selection.update(set => {
            items.forEach(item => {
                set.selected[item.class] = {
                    ...(set.selected[item.class] || {}),
                    [item.id]: extractMeta(item)
                };
            });
            store(set);
            return set;
        }),

        remove: (itemId, itemType) => selection.update(set => {
            const {[itemId]: _, ...rest} = set.selected[itemType];
            set.selected[itemType] = rest;
            store(set);
            return set;
        }),

        removeAll: (itemIds, itemType) => selection.update(set => {
            itemIds.forEach(id => delete set.selected[itemType]?.[id]);
            store(set);
            return set;
        }),

        toggle: (item) => selection.update(set => {
            if (set.selected[item.class]?.[item.id]) {
                const {[item.id]: _, ...rest} = set.selected[item.class];
                set.selected[item.class] = rest;
            } else {
                set.selected[item.class] = {
                    ...(set.selected[item.class] || {}),
                    [item.id]: extractMeta(item)
                };
            }
            store(set);
            return set;
        }),

        toggleSet: (set) => {
            const currentSelection = get(selection);
            if (currentSelection.id === set.id) {
                unloadSet();
            } else {
                loadSet(set);
            }
        },

        empty: () => selection.update(set => {
            set.id = null;
            set.title = title;
            set.selected = {};
            store(set, true);
            return set;
        }),

        updateTitle: (title) => selection.update(set => {
            set.title = title;
            store(set, true);
            return set;
        }),
        updatePublic: (is_public) => selection.update(set => {
            set.is_public = is_public;
            store(set, true);
            return set;
        }),

        save,
        isSaved,
        selection,

        selectionTitle: derived(selection, $sel => $sel.title),
        isSelected: derived(selection, $sel =>
            item => $sel.selected[item.class]?.[item.id] || false
        ),

        selected: derived(selection, $sel =>
            $sel.selected
        ),

        nbSelected: derived(selection, $sel =>
            Object.entries($sel.selected).reduce(
                (count, [model, items]) =>
                    model === "User"
                        ? count
                        : count + Object.keys(items).length,
                0
            )
        ),
        isSetSelected: derived(selection, $sel =>
            set => $sel.id === set.id
        ),
    };
}

export const recordsSelection = createTypedSelectionStore({
    type: 'documentSet',
    modelName: 'document-set',
    title: appLang === 'en' ? 'Document set' : 'Set de documents',
    extractMeta: (item) => ({title: item.title, url: item.url})
});

export const regionsSelection = createTypedSelectionStore({
    type: 'regionsSet',
    modelName: 'regions-set',
    title: appLang === 'en' ? 'Regions set' : 'Set de régions',
    extractMeta: (item) => item
});

export const clusterSelection = createTypedSelectionStore({
    type: 'clusterSet',
    modelName: 'cluster-set',
    title: appLang === 'en' ? 'Selected regions' : 'Régions sélectionnées',
    extractMeta: (item) => ({imgRef: item.id, clusterId: item.clusterId, title: item.title, xywh: item.xywh, img: item.img})
});
