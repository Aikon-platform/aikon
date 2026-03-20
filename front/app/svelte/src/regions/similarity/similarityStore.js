import {derived, get, writable} from "svelte/store";
import {errorMsg, initPagination, loading, pageUpdate} from "../../utils.js";
import {csrfToken} from "../../constants.js";

/**
 * @typedef { Object.<number, Object.<string, RegionsType>> } SelectedRegionsType
 *  { <witness id>: { <regions ref>: RegionsType }
 */
/**
 * @typedef {Object.<number, undefined|>} EmptyRegionsType:
 *  like the above SelectedRegionsType, but there is no RegionsType
 */
/**
 * @typedef RegionsType
 *  a regions extraction
 * @type {object}
 * @property {number} id
 * @property {string} ref
 * @property {string} url: IIIF URL to the extracted image regions
 * @property {"Regions"} type
 * @property {"Regions"} class: python  class
 * @property {string} title
 * @property {number} zeros,
 * @property {number} img_nb: number of extracted images
 */
/**
 * @typedef { Object.<string, RegionsType> } ComparedRegionsType
 *  { <regions ref>: RegionsType }
 */
/**
 * @typedef PropagateParamsType
 * @property {number} propagateRecursionDepth
 * @property {boolean} propagateFilterByRegions
 */
/**
 * @typedef SimilarityParamsType
 * @type {object}
 * @property {number[]} excludedCategories
 * @property {SelectedRegionsType} regions
 * @property {number} similarityScoreCutoff
 */
/**
 * @typedef SimilarityToolbarParamsType
 *      all params defined in SimilarityToolbar
 * @type {object}
 * @property {PropagateParamsType} propagate
 * @property {SimilarityParamsType} similarity
 */


function createSimilarityStore() {
    const baseUrl = `${window.location.origin}${window.location.pathname}`;
    const pageLength = 25;

    /** @type {number} the current witness' ID */
    const currentPageId = window.location.pathname.match(/\d+/g).join("-");

    /** @type {EmptyRegionsType}  */
    const emptySelection = { [currentPageId]: {} };

    const allowedPropagateDepthRange = [2,6];

    const currentPage = writable(1);

    /** @type {writable<ComparedRegionsType>} */
    const comparedRegions = writable({});

    /** @type {writable<SelectedRegionsType>} */
    const selectedRegions = writable(JSON.parse(localStorage.getItem("selectedRegions")) || emptySelection);
    selectedRegions.subscribe((value) => localStorage.setItem("selectedRegions", JSON.stringify(value)));

    /** @type {writable<number[]>} */
    const excludedCategories = writable(JSON.parse(localStorage.getItem("excludedCategories")) || []);
    excludedCategories.subscribe((value) => localStorage.setItem("excludedCategories", JSON.stringify(value)));

    /** @type {writable<number?>} RegionPairs below this score will be hidden from the user */
    const similarityScoreCutoff = writable(JSON.parse(localStorage.getItem("similarityScoreCutoff")) || undefined);
    similarityScoreCutoff.subscribe((value) => {
        // since the 1st value is undefined, we need to ensure we're not writing this to localStorage
        if (value!=null) localStorage.setItem("similarityScoreCutoff", JSON.stringify(value))
    });

    /** @type {writable<number[]>} */
    const propagateRecursionDepth = writable(JSON.parse(localStorage.getItem("propagateRecursionDepth")) || allowedPropagateDepthRange[1]);
    propagateRecursionDepth.subscribe((value) => localStorage.setItem("propagateRecursionDepth", JSON.stringify(value)));

    /** @type {writable<Boolean>} */
    const propagateFilterByRegions = writable(JSON.parse(localStorage.getItem("propagateFilterByRegions")) || false);
    propagateFilterByRegions.subscribe((value) => localStorage.setItem("propagateFilterByRegions", JSON.stringify(value)));

    /** @type {writable<PropagateParamsType>} no localStorage syncing since individual stores are aldready synced */
    const propagateParams = derived([propagateRecursionDepth, propagateFilterByRegions], ([$propagateRecursionDepth, $propagateFilterByRegions]) => ({
        propagateRecursionDepth: $propagateRecursionDepth,
        propagateFilterByRegions: $propagateFilterByRegions
    }));

    /** @type {writable<SimilarityParamsType>} no localStorage syncing since individual stores are aldready synced */
    const similarityParams = derived([excludedCategories, selectedRegions, similarityScoreCutoff], ([$excludedCategories, $selectedRegions, $similarityScoreCutoff]) => ({
        excludedCategories: $excludedCategories,
        regions: $selectedRegions,
        similarityScoreCutoff: $similarityScoreCutoff
    }));

    /** @type {writable<SimilarityToolbarParamsType>} no localStorage syncing since individual stores are aldready synced */
    const similarityToolbarParams = derived([propagateParams, similarityParams], ([$propagateParams, $similarityParams]) => ({
        propagate: $propagateParams,
        similarity: $similarityParams
    }));

    /** @type {writable<string[]|[]>} query image names for the current witness */
    const qImgs = writable([]);
    const pageQImgs = writable([]);

    /**
     * On load, fetches all query images and regions that were compared to current regions
     * @type {Promise<any>}
     */
    async function fetchSimilarity() {
        const getComparedRegions = async () => {
            const regionsResponse = await fetch(`${baseUrl}compared-regions`);
            const regionsData = await regionsResponse.json();
            comparedRegions.set(regionsData);

            // from one refresh to another, in case of database changes, selectedRegions may contain regions that are not in comparedRegions => delete those
            selectedRegions.update((_selectedRegions) => {
                let currentSelectedRegions = _selectedRegions[currentPageId] || {};
                if ( Object.keys(currentSelectedRegions).length ) {
                    // `.filter().reduce()` creates a copy of `currentSelectedRegions` without the keys that are not in `regionsData`
                    _selectedRegions[currentPageId] = Object.keys(currentSelectedRegions)
                        .filter(key => Object.keys(regionsData).includes(key))
                        .reduce((obj, key) => {
                            obj[key] = currentSelectedRegions[key];
                            return obj
                        }, {});
                }
                return _selectedRegions;
            });
        }
        const getQueryImages = async () => {
            const imgsResponse = await fetch(`${baseUrl}query-images`);
            const imgsData = await imgsResponse.json();
            if (imgsData.length > 0) {
                qImgs.set(imgsData);
                handlePageUpdate(initCurrentPage());
            }
        }

        loading.set(true);
        try {
            // Promise.all => parallelize async queries
            await Promise.all([ getComparedRegions(), getQueryImages() ]);
        } catch (err) {
            console.error("Error:", err);
            errorMsg.set(err.message);
        } finally {
            loading.set(false);
        }
    }

    function store(selection) {
        localStorage.setItem("selectedRegions", JSON.stringify(selection));
    }

    function select(region) {
        selectedRegions.update(selection => {
            const updatedSelection = {
                ...selection,
                [currentPageId]: {
                    ...(selection[currentPageId] || {}),
                    [region.ref]: region
                }
            };
            store(updatedSelection);
            return updatedSelection;
        });
    }

    const isSelected = derived(selectedRegions, ($selectedRegions) =>
    // a complex form that is a workaround for eslint `no-prototype-builtins`. see: https://stackoverflow.com/a/39283005
        regionRef => !!(
            $selectedRegions[currentPageId]
      && Object.prototype.hasOwnProperty.call($selectedRegions[currentPageId], regionRef)
        )
    );

    function getRegionsInfo(ref) {
        const displayedRegions = get(comparedRegions);
        const regionRef = Object.keys(displayedRegions).filter(key => key.startsWith(ref));
        if (regionRef.length !== 1) {
            return {title: "Error"};
        }
        return displayedRegions[regionRef[0]]
    }

    const initCurrentPage = () => initPagination(currentPage, "sp");

    // without `qImgs`, `setPageQImgs` may run before qImgs has been defined
    const setPageQImgs = derived([currentPage, qImgs], ([$currentPage, $qImgs]) =>
        (async () => updatePageQImgs($currentPage, $qImgs))());

    function updatePageQImgs(pageNb, _qImgs) {
        const start = (pageNb - 1) * pageLength;
        const end = start + pageLength;
        const currentQImgs = _qImgs.slice(start, end);
        pageQImgs.set(currentQImgs);
        return currentQImgs;
    }

    function handlePageUpdate(pageNb) {
        pageUpdate(pageNb, currentPage, "sp");
    }

    function addComparedRegions(region) {
        if (!region) return false;
        const current = get(comparedRegions);
        if (current[region.ref]) return false; // Already exists

        comparedRegions.update(regions => ({...regions, [region.ref]: region}));
        select(region);
        return true;
    }

    // Global signal to force all visible rows to refresh (e.g. from a toolbar)
    const refreshSignal = writable(0);
    const triggerRefresh = () => refreshSignal.update(n => n + 1);

    /** * Factory to create a dedicated store for a single SimilarityRow.
     * Encapsulates fetch logic, state management, and race-condition handling.
     */
    function createRowStore(qImg, isInModal) {
        const items = writable([]);
        const propagated = writable([]);
        const loading = writable(false);
        const propagatedLoading = writable(false);
        const error = writable(null);
        let cGen = 0, pGen = 0, visible = isInModal;

        const getRids = () => {
            const sel = get(selectedRegions);
            return Object.values(sel[currentPageId] || {}).map(r => r.id);
        };

        const fetchComputed = async (rids) => {
            const gen = ++cGen;
            loading.set(true);
            try {
                const res = await fetch(`${baseUrl}similar-images`, {
                    method: "POST",
                    headers: {"Content-Type": "application/json", "X-CSRFToken": csrfToken},
                    body: JSON.stringify({
                        regionsIds: rids,
                        filterByRegions: !isInModal,
                        qImg,
                        ...(!isInModal && { topk: 10 }) // all matches in modal
                    }),
                });
                const data = await res.json();
                if (gen === cGen) items.set(data);
            } catch (e) {
                if (gen === cGen) error.set(e.message);
            } finally {
                if (gen === cGen) loading.set(false);
            }
        };

        const fetchPropagated = async (rids) => {
            propagatedLoading.set(true);
            const gen = ++pGen;
            const params = get(propagateParams);
            try {
                const res = await fetch(`${baseUrl}propagated-matches/${qImg}`, {
                    method: "POST",
                    headers: {"Content-Type": "application/json", "X-CSRFToken": csrfToken},
                    body: JSON.stringify({
                        regionsIds: isInModal ? [] : rids,
                        filterByRegions: isInModal ? false : params.propagateFilterByRegions,
                        recursionDepth: params.propagateRecursionDepth,
                    })
                });
                const data = await res.json();
                if (gen === pGen) propagated.set(data);
            } catch (e) {
                if (gen === pGen) propagated.set([]);
            }
            propagatedLoading.set(false);
        };

        const fetchRow = () => {
            const rids = getRids();
            if (!isInModal && rids.length === 0) {
                items.set([]);
            } else {
                fetchComputed(rids);
            }
            fetchPropagated(rids);
        };

        const unsubs = [
            refreshSignal.subscribe(() => visible && fetchRow()),
            propagateParams.subscribe(() => visible && fetchPropagated(getRids())),
            selectedRegions.subscribe(() => visible && fetchRow())
        ];

        return {
            items, propagated, loading, propagatedLoading, error, fetchRow,
            setVisible: (v) => { visible = v; if (v) fetchRow(); },
            filtered: derived([items, excludedCategories, similarityScoreCutoff], ([$i, $e, $s]) =>
                $i.filter(([score, , , , , cat]) =>
                    !$e.includes(cat) && (score == null || $s == null || Number(score) >= $s)
                )
            ),
            destroy: () => unsubs.forEach(fn => fn())
        };
    }

    function removeQImg(img) {
        qImgs.update(imgs => imgs.filter(q => q !== img));
    }

    return {
        baseUrl,
        currentPageId,
        currentPage,
        comparedRegions,
        excludedCategories,
        qImgs,
        pageQImgs,
        removeQImg,
        selectedRegions,
        propagateRecursionDepth,
        propagateFilterByRegions,
        similarityToolbarParams,
        propagateParams,
        similarityScoreCutoff,
        allowedPropagateDepthRange,
        fetchSimilarity,
        setPageQImgs,
        getRegionsInfo,
        handlePageUpdate,
        select,
        addComparedRegions,
        isSelected,
        pageLength,
        createRowStore,
        triggerRefresh,
    };
}

export const similarityStore = createSimilarityStore();
