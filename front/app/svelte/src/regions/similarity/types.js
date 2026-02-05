/**
 * @typedef SimilarityPairType
 *      a similarity between 2 regions in the similarity module.
 * @type {object}
 * @property {string} qImg: query image
 * @property {string} sImg: similarity image
 * @property {number} qRegions: id of the region extraction the query image belongs to
 * @property {number} sRegions: id of the region extraction the similarity image belongs to
 * @property {number} score: score of the similarity. defaults to 0
 * @property {number?} category: category is used by users to classify the similarities. it is an Interger identifying a type of similarity
 * @property {number[]|[]} users: "user selected category". a possibly empty array of the IDs of the users who selected this similarity.
 * @property {boolean} isManual: true if it's a manual similarity
 * @property {number} similarityType: 1 if it's a computed similarity, 2 if it's a manual similarity, 3 if it's a propagation,
 */

export {}
