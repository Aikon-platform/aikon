<script>
    import {appName, appUrl} from "../../constants.js";
    import {i18n} from '../../utils.js';

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

    const imageCount = meta.images?.length || 0;
    const docTitle = `${meta.title} #${id} (${imageCount} images)`;

    const t = {
        nbImg: {en: 'Number of images for this region extraction', fr: "Nombre d'images extraites pour ce document"},
        toggle: {en: 'Toggle document pairs visibility', fr: "Activer/désactiver la visibilité des paires du document"},
    };
</script>

<div class="legend-item is-flex is-justify-content-space-between" class:inactive={!isActive}>
    <span class="is-flex is-align-items-center" style="gap: 0.5rem;">
        <span class="legend-color" class:inactive={!isActive} class:clickable={clickable}
             aria-label={docTitle} title="{onlyColor ? docTitle : i18n('toggle', t)}"
             style="background-color: {isActive ? meta.color : '#999'};"
             on:click={toggle} on:keydown={null} role="button" tabindex="0"/>
        <span class="legend-label" class:is-hidden={onlyColor}>
            <a href={`${appUrl}/${appName}/witness/${meta.witnessId}/regions/${id}`} target="_blank">
                {meta.title}
            </a>
        </span>
    </span>
    <span class="tag is-small has-text-grey is-rounded px-2"
          title={i18n('nbImg', t)} class:is-hidden={onlyColor}>
        {imageCount}
    </span>
</div>

<style>
    .legend-item {
        display: flex;
        align-items: center;
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
