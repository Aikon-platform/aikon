import {writable, get} from "svelte/store";

export function createWitnessStore(digits = {}) {
    const digitizations = writable(digits);
    const manifests = writable([...Object.values(digits).map(d => d.manifest)]);
    const selectedManifest = writable();
    const imgPrefix = writable("");
    const nbOfPages = writable(1);
    const leadingZeros = writable(1);

    const selectManifest = (manifest) => {
        if (!manifest) return;
        selectedManifest.set(manifest);
        const digit = Object.values(get(digitizations)).find(d => d.manifest === manifest);
        if (digit) {
            imgPrefix.set(digit.img_prefix);
            nbOfPages.set(digit.img_nb);
            leadingZeros.set(digit.img_zeros);
        }
    }

    selectManifest(get(manifests)[0] || null);

    return {
        manifests,
        selectedManifest,
        imgPrefix,
        nbOfPages,
        leadingZeros,
        selectManifest,
        hasDigit: () => get(manifests).length > 0,
    };
}
