import {writable, get} from "svelte/store";

export function createWitnessStore(digits = {}) {
    const digitizations = writable(digits);
    const manifests = writable([...Object.values(digits).map(d => d.manifest)]);
    const selectedManifest = writable(get(manifests)[0] || null);
    const imgPrefix = writable("");
    const nbOfPages = writable(1);
    const leadingZeros = writable(1);

    const selectManifest = (manifest) => {
        selectedManifest.set(manifest);
        const digit = get(digitizations)?.find(d => d.manifest === selectedManifest);
        if (digit) {
            imgPrefix.set(digit.imgPrefix);
            nbOfPages.set(digit.nbOfPages);
            leadingZeros.set(digit.leadingZeros);
        }
    }

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
