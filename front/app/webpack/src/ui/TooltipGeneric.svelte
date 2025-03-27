<!-- a super generic tooltip (text that appears on top of an element)
    that is displayed when the `targetEl` is clicked or hovered.

    if a targetHtmlId is passed, `targetEl` will be `targetHtmlId`.
    else, the direct parent of the current `TooltipGeneric` will be used.

    props:
    - tooltipText (string)
        text displayed on tooltip hover.
    - targetHtmlId (string)
        the html ID of the element for which we want to listen to events.
-->
<script>
import { onMount, onDestroy } from "svelte";

//////////////////////////////////

export let tooltipText;
export let targetHtmlId;

const htmlId = `tooltip-generic-${window.crypto.randomUUID()}`;

// set the width of a tooltip that is by default super thin
$: tooltipWidthClass = setTooltipWidthClass(tooltipText);
$: setTooltipWidthClass = (_tooltipText) =>
    tooltipWidthClass =
        _tooltipText.length > 100
        ? "tooltip-wide"
        : _tooltipText.length > 20
        ? "tooltip-mid"
        : "tooltip-thin";

$: targetEl = undefined;
$: displayTooltip = false;

//////////////////////////////////

const onMouseover = () => displayTooltip = true;
const onMouseout = () => displayTooltip = false;
const onClick = () => displayTooltip = !displayTooltip;

//////////////////////////////////

onMount(() =>  {
    targetEl =
        targetHtmlId
        ? document.getElementById(targetHtmlId)
        : document.getElementById(htmlId).parentElement;
    if ( targetHtmlId && !targetEl ) {
        console.error(`TooltipGeneric: element with ID ${targetHtmlId} not found, defaulting to the parent element`);
        targetEl = document.getElementById(htmlId).targetElement;
    }
    targetEl.addEventListener("mouseover", onMouseover);
    targetEl.addEventListener("mouseout", onMouseout);
    targetEl.addEventListener("click", onClick);
})
onDestroy(() => {
    targetEl.removeEventListener("mouseover", onMouseover);
    targetEl.removeEventListener("mouseout", onMouseout);
    targetEl.removeEventListener("click", onClick);
})


</script>


<span id={htmlId}
      class="tooltip {tooltipWidthClass} { displayTooltip ? 'display' : '' }"
>{tooltipText}</span>


<style>
.tooltip {
    visibility: hidden;
    background-color: rgba(0, 0, 0, 0.7);
    color: #fff;
    text-align: center;
    border-radius: 6px;
    padding: 5px;
    position: absolute;
    z-index: 6;
    bottom: 125%;
    left: 50%;
    transform: translateX(-50%);
    opacity: 0;
    transition: opacity 0.3s;
}
.tooltip.display {
    visibility: visible;
    opacity: 1;
}
.tooltip-thin {
    width: auto; /** very thin by default */
}
.tooltip-mid {
    width: max(150px, 20vw)
}
.tooltip-wide {
    width: max(300px, 30vw);
}
</style>
