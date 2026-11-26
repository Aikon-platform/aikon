/**
 * State shared between parent components and a TooltipGeneric instance.
 * @typedef {{ tooltipText: string }} TooltipGenericState
 */

/**
 * function to create a svelte $state from which `TooltipGeneric`
 * will read ita values. this allows:
 * - to create as many states as we have tooltips on our page (instead of 1 shared space for all
 *      tooltips, each tooltip gets its own state)
 * - to update tooltip props (necessary for InputSlider)
 * @returns {TooltipGenericState}
 */
export const makeTooltipGenericState = () => {
    // necesssary to assign before returning to avoid svelte state_invalid_placement
    const state = $state({ tooltipText: "" });
    return state;
};
