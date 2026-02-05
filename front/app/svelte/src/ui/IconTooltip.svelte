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

    export let iconifyIcon,
               altText,
               tooltipText;
</script>


<div class="is-inline-block icon-tooltip">
    <button>
        <span class="iconify"
              data-icon={iconifyIcon}
              title={altText}
        ></span>
        <TooltipGeneric {tooltipText}></TooltipGeneric>
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
