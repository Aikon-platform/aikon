#!/bin/sh
mv "_unused/NetworkInfo.svelte" "src/documentSet/network/NetworkInfo.svelte"
mv "_unused/PropagatedMatches.svelte" "src/regions/similarity/PropagatedMatches.svelte"
mv "_unused/SimilarityMatches.svelte" "src/regions/similarity/SimilarityMatches.svelte"
mv "_unused/Editing.svelte" "src/vectorization/Editing.svelte"
rm -- "$0"
