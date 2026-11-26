<!-- an icon which, when hovered, displays a tooltip info.

    props:
    - iconifyIcon (string)
        the iconify icon to display inside the tooltip
    - altText (string)
        optional text describing the tooltip for accessibility
    - tooltipText (string)
        text displayed on tooltip hover.
-->

<script>
    import TooltipGeneric from "./TooltipGeneric.svelte";
    import {makeTooltipGenericState} from "./tooltipGenericState.svelte";

    /** @typedef {import("../../ui/tooltipGenericState.svelte").TooltipGenericState} TooltipGenericState */

    let { iconifyIcon, altText, tooltipText } = $props();
    const tooltipState = makeTooltipGenericState();
    tooltipState.tooltipText = tooltipText;
</script>


<div class="is-inline-block icon-tooltip">
    <button>
        <span class="iconify" data-icon={iconifyIcon} title={altText}></span>
        <TooltipGeneric {tooltipState}/>
    </button>
</div>

<style>
    .icon-tooltip > button {
        position: relative;
        cursor: pointer;
        display: flex;
        justify-content: center;
        align-items: center;
    }
</style>
