<!-- a super generic tooltip that can be used anywhere in the app.
    adapted from regions/Region.svelte

    props:
    - iconifyIcon (string)
        the iconify icon to display inside the tooltip
    - altText (string)
        optional text describing the tooltip for accessibility
    - tooltipText (string)
        text displayed on tooltip hover.
-->
<script>

    export let iconifyIcon,
               altText,
               tooltipText;

    // kinda hacky way to set the width of a tooltip that is by default super thin
    const tooltipWidthClass =
        tooltipText.length < 20
        ? "tooltip-thin"
        : tooltipText.length < 100
        ? "tooltip-mid"
        : "tooltip-wide";
</script>


<div class="is-inline-block tooltip-generic">
    <button>
        <span class="iconify"
              data-icon={iconifyIcon}
              title={altText}
        ></span>
        <span class="tooltip {tooltipWidthClass}">
            {tooltipText}
        </span>
    </button>
</div>


<style>
    .tooltip-generic > button {
        position: relative;
        cursor: pointer;
        display: flex;
        justify-content: center;
        align-items: center;
    }
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
    .tooltip-generic:hover .tooltip {
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
