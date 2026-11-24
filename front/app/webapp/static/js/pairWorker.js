/**
 * Web Worker for incremental pair processing.
 * Fetches the gzipped NDJSON batch stream and builds indexes incrementally.
 */

const IMG_REGEX = /^(wit\d+_[a-z]{3}(\d+)_(\d+))(?:_([\d,]+))?\.jpg$/;
// const weights = { 1: 1.0, 2: 0.5, 3: 0.125, 4: -1.0, 5: 0.125 };
const weights = { 0: 1, 1: 1, 2: 1.5, 3: 1.25, 4: -1.0, 5: 1.25 };
const COLS = { id1: Uint32Array, id2: Uint32Array, score: Float32Array, cat: Uint8Array, um: Uint8Array, st: Uint8Array };
const NO_RANK = 65535;
// similarity_type => priority when several rows describe the same pair of images (manual, auto, propagated, remapped)
const TYPE_RANK = { 2: 0, 1: 1, 3: 2, 4: 3 };
const STRIDE = 6;
const pairKey = (a, b) => a < b ? `${a}-${b}` : `${b}-${a}`;

let state = null;

self.onmessage = async ({ data: { url } }) => {
    state = createState();
    try {
        const res = await fetch(url);
        if (!res.ok) throw new Error((await res.json().catch(() => ({}))).error || `HTTP ${res.status}`);

        const reader = res.body.pipeThrough(new TextDecoderStream()).getReader();
        let buffer = "";
        for (let chunk; !(chunk = await reader.read()).done;) {
            const lines = (buffer + chunk.value).split("\n");
            buffer = lines.pop();
            for (const line of lines) processBatch(...JSON.parse(line));
        }
        finalize();
    } catch (err) {
        self.postMessage({ type: 'error', message: err.message });
    }
};

function createState() {
    return {
        names: [],
        imgs: [],
        imageMap: new Map(),
        categories: {},
        n: 0,
        cols: Object.fromEntries(Object.entries(COLS).map(([k, T]) => [k, new T(1 << 20)])),
    };
}

function reserve(size) {
    const { cols } = state;
    if (size <= cols.id1.length) return;
    const cap = Math.max(size, cols.id1.length * 2);
    for (const k in cols) {
        const a = new cols[k].constructor(cap);
        a.set(cols[k]);
        cols[k] = a;
    }
}

function processBatch(newNames, flat) {
    const { names, imgs, categories } = state;
    for (const name of newNames) names.push(name);

    reserve(state.n + flat.length / STRIDE);
    const { id1, id2, score, cat, um, st } = state.cols;

    for (let i = 0; i < flat.length; i += STRIDE) {
        const a = flat[i], b = flat[i + 1], c = flat[i + 3], u = flat[i + 4];
        if (c === 4) continue;

        categories[c] = (categories[c] || 0) + 1;
        if (u) categories[5] = (categories[5] || 0) + 1;

        imgs[a] ??= getOrAddImage(names[a]);
        imgs[b] ??= getOrAddImage(names[b]);

        const k = state.n++;
        id1[k] = a;
        id2[k] = b;
        score[k] = flat[i + 2] ?? NaN;
        cat[k] = c;
        um[k] = u;
        st[k] = flat[i + 5] ?? 1;
    }

    self.postMessage({ type: 'progress', count: state.n });
}

/** keeps one row per pair of images (rows of a pair differ by their similarity hash): the best by similarity type, then by score */
function dedupe() {
    const { cols, n, names, categories } = state;
    const { id1, id2, score, cat, um, st } = cols;
    const rankOf = i => TYPE_RANK[st[i]] ?? 99;
    const better = (i, j) => {
        const r = rankOf(i) - rankOf(j);
        return r ? r < 0 : isNaN(score[j]) ? !isNaN(score[i]) : score[i] > score[j];
    };

    const m = names.length, byImg1 = csr(m, n, emit => { for (let i = 0; i < n; i++) emit(id1[i], i); });
    const keep = new Uint8Array(n).fill(1), seenFor = new Int32Array(m).fill(-1), bestFor = new Uint32Array(m);
    let dups = 0;
    for (let a = 0; a < m; a++) {
        for (let k = byImg1.start[a]; k < byImg1.start[a + 1]; k++) {
            const i = byImg1.idx[k], b = id2[i];
            if (seenFor[b] !== a) {
                seenFor[b] = a;
                bestFor[b] = i;
                continue;
            }
            if (better(i, bestFor[b])) {
                keep[bestFor[b]] = 0;
                bestFor[b] = i;
            } else keep[i] = 0;
            dups++;
        }
    }
    if (!dups) return;

    const all = Object.values(cols);
    let kept = 0;
    for (let i = 0; i < n; i++) {
        if (keep[i]) {
            for (const col of all) col[kept] = col[i];
            kept++;
            continue;
        }
        if (!--categories[cat[i]]) delete categories[cat[i]];
        if (um[i] && !--categories[5]) delete categories[5];
    }
    state.n = kept;
}

function finalize() {
    dedupe();
    const { names, imgs, imageMap, categories, n } = state;
    const { id1, id2, score, cat, um, st } = Object.fromEntries(
        Object.entries(state.cols).map(([k, a]) => [k, a.subarray(0, n)])
    );
    const m = names.length;
    const weightOf = i => weights[cat[i] || (um[i] && 5)] || 0;

    const w = new Float32Array(n);
    let sum = 0, count = 0, max = 0;
    for (let i = 0; i < n; i++) {
        if (isNaN(score[i])) continue;
        w[i] = Math.max(0.01, score[i] * weightOf(i));
        sum += w[i];
        count++;
        if (w[i] > max) max = w[i];
    }
    const meanReal = count ? sum / count : 1;
    const exactScore = (max || 1) * 1.25;
    for (let i = 0; i < n; i++) {
        if (cat[i] === 1) w[i] = exactScore;
        else if (isNaN(score[i])) w[i] = meanReal * weightOf(i);
    }

    // w >= 0, so its float32 bits sort like its value: native sort of (~bits << 32 | i) gives w desc, then index asc
    const keys = new BigUint64Array(n), kv = new Uint32Array(keys.buffer), bits = new Uint32Array(w.buffer, 0, n);
    for (let i = 0; i < n; i++) {
        kv[2 * i] = i;
        kv[2 * i + 1] = ~bits[i];
    }
    keys.sort();
    const order = new Uint32Array(n);
    for (let i = 0; i < n; i++) order[i] = kv[2 * i];

    const imgDigit = Uint32Array.from({ length: m }, (_, j) => imgs[j]?.digit ?? 0);
    const dOf = new Map(), docDigits = [];
    const dIdx = Uint16Array.from(imgDigit, d => dOf.get(d) ?? dOf.set(d, docDigits.push(d) - 1).get(d));
    const D = docDigits.length;
    const docPair = i => {
        const a = dIdx[id1[i]], b = dIdx[id2[i]];
        return a < b ? a * D + b : b * D + a;
    };

    // byImage as CSR filled in score order: pairs of image j are byImage[start[j]..start[j + 1]], best first
    const byImage = csr(m, 2 * n, emit => order.forEach(i => (emit(id1[i], i), emit(id2[i], i))));
    const byDocPair = csr(D * D, n, emit => { for (let i = 0; i < n; i++) emit(docPair(i), i); });

    const rank1 = new Uint16Array(n), rank2 = new Uint16Array(n);
    for (let j = 0; j < m; j++) {
        for (let k = byImage.start[j]; k < byImage.start[j + 1]; k++) {
            const i = byImage.idx[k];
            const rank = cat[i] === 1 ? 1 : imgDigit[id1[i]] === imgDigit[id2[i]] ? NO_RANK : Math.min(k - byImage.start[j] + 1, NO_RANK - 1);
            (id1[i] === j ? rank1 : rank2)[i] = rank;
        }
    }

    // ranking of the pair relative to the document pair (digit_1, digit_2)
    // for (const [key, group] of rankGroups) {
    //     const imgId = key.slice(0, key.lastIndexOf('|'));
    //     group.sort((a, b) => b.weightedScore - a.weightedScore);
    //     for (let k = 0; k < group.length; k++) {
    //         const pair = group[k];
    //         const rank = pair.digit_1 === pair.digit_2 ? Infinity : (pair.category === 1 ? 1 : k + 1);
    //         if (pair.id_1 === imgId) {
    //             pair.doc_rank_1 = rank;
    //         } else {
    //             pair.doc_rank_2 = rank;
    //         }
    //     }
    // }

    const columns = {
        id1, id2, score, cat, um, st, w, rank1, rank2, order, imgDigit,
        start: byImage.start, byImage: byImage.idx, dpStart: byDocPair.start, byDocPair: byDocPair.idx,
    };

    self.postMessage({
        type: 'complete',
        columns,
        docDigits,
        imageIds: names,
        imageNodes: imageMap,
        categories,
        stats: {
            pairStats: { count: n, scoreRange: range(n ? [w[order[n - 1]], w[order[0]]] : []) },
            documentStats: groupStats(D, d => docDigits[d], emit => { for (let i = 0; i < n; i++) emit(dIdx[id1[i]], w[i]), emit(dIdx[id2[i]], w[i]); }),
            imageStats: groupStats(m, j => names[j], emit => { for (let i = 0; i < n; i++) emit(id1[i], w[i]), emit(id2[i], w[i]); }),
            docPairStats: groupStats(D * D, k => pairKey(docDigits[k / D | 0], docDigits[k % D]), emit => { for (let i = 0; i < n; i++) emit(docPair(i), w[i]); }),
        },
    }, Object.values(columns).map(a => a.buffer));

    state = null;
}

/** compressed sparse rows: each(emit) is run twice and calls emit(k, i) per item; items of key k are idx[start[k]..start[k + 1]], in emission order */
function csr(size, total, each) {
    const start = new Uint32Array(size + 1);
    each(k => start[k + 1]++);
    for (let k = 0; k < size; k++) start[k + 1] += start[k];
    const idx = new Uint32Array(total), next = start.slice(0, -1);
    each((k, i) => idx[next[k]++] = i);
    return { start, idx };
}

function getOrAddImage(imgKey) {
    let imgData = state.imageMap.get(imgKey);

    if (!imgData) {
        const [, ref, digit, page, coords] = imgKey.match(IMG_REGEX);
        imgData = {
            id: imgKey,
            digit: +digit,
            ref: `${ref}.jpg`,
            canvas: +page,
            xywh: coords ? coords.split(',') : null,
            type: "region_extraction",
            // to be initialized in the main thread
            color: null
        };
        state.imageMap.set(imgKey, imgData);
    }

    return imgData;
}

function pushToMap(map, key, value) {
    let arr = map.get(key);
    if (!arr) {
        arr = [];
        map.set(key, arr);
    }
    arr.push(value);
}

/** scoreCount entries in order of first appearance, as emitted by each(emit) with emit(key, weight) */
function groupStats(size, label, each) {
    const score = new Float64Array(size), count = new Uint32Array(size), seen = [];
    each((k, v) => {
        count[k]++ || seen.push(k);
        score[k] += v;
    });
    const scoreCount = new Map(seen.map(k => [label(k), { score: score[k], count: count[k] }]));
    const entries = [...scoreCount.values()];
    return {
        count: scoreCount.size,
        scoreCount,
        scoreRange: range(entries.map(e => e.score)),
        countRange: range(entries.map(e => e.count)),
    };
    // computeDensity(stats);
}

function range(values) {
    let min = Infinity, max = -Infinity;
    for (const v of values) {
        if (v < min) min = v;
        if (v > max) max = v;
    }
    return values.length ? { min, max, range: max - min } : { min: 0, max: 0, range: 0 };
}

// function computeDensity(stats) {
//     if (stats.count <= 1) {
//         stats.density = 0;
//         return;
//     }
//     stats.density = (2 * stats.links) / (stats.count * (stats.count - 1));
// }
