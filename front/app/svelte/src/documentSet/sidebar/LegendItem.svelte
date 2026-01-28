<script>
    import {appName, appUrl} from "../../constants.js";

    export let isActive = true;
    export let id;
    export let toggle = () => {};
    export let meta = {
        title: `Region`,
        color: '#999',
        witnessId: 1
    };
    export let clickable = true;
    export let onlyColor = false;
</script>

<div class="legend-item" class:inactive={!isActive}>
    <span class="legend-nb"><!--IMAGE NUMBER--></span>
    <span class="legend-color" class:inactive={!isActive} class:clickable={clickable}
          aria-label="{meta.title}" title="{meta.title}"
          style="background-color: {isActive ? meta.color : '#999'};"
          on:click={toggle} on:keydown={null} role="button" tabindex="0" />
    {#if !onlyColor}
        <span class="legend-label">
            <a href={`${appUrl}/${appName}/witness/${meta.witnessId}/regions/${id}`} target="_blank">
                {meta.title}
            </a>
        </span>
    {/if}
</div>

<style>
    .legend-nb {
        /* ADD  STYLE */
    }

    .legend-item {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        padding: 0.25rem 0;
        transition: opacity 0.2s;
    }

    .legend-item.inactive {
        opacity: 0.5;
    }

    .legend-color {
        width: 18px;
        height: 18px;
        border-radius: 50%;
        box-shadow: 0 2px 3px rgba(0, 0, 0, 0.3);
        flex-shrink: 0;
        transition: all 0.2s;
    }

    .legend-color.clickable {
        cursor: pointer;
    }

    .legend-color.clickable:hover {
        transform: scale(1.2);
        box-shadow: 0 3px 6px rgba(0, 0, 0, 0.4);
    }

    .legend-color.inactive {
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
    }

    .legend-label {
        display: -webkit-box;
        line-clamp: 2;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
        text-overflow: ellipsis;
        line-height: 1.2em;
        max-height: 2.4em;
        /*text-align: left;*/
    }
</style>
