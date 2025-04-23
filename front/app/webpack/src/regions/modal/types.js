// NOTE the meanings of 'query' and 'similarity' is the same as in the "similarity" svelte module

/** @typedef {import("../types").RegionItemType} RegionItemType */

/**
 * @typedef SimilarityOverlayType
 * @type {object}
 * @property {{ href: string|URL, title: string }} queryImage
 * @property {{ href: string|URL, title: string }} similarityImage
 */

/**
 * @typedef SimilaritySideBySideType
 * @property {RegionItemType} queryImage
 * @property {RegionItemType} similarityImage
 */

export {}
