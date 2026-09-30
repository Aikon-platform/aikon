<script>
    import {appName, appUrl} from "../../constants.js";
    import {i18n} from "../../utils.js";

    export let isActive = true;
    export let imgCount = null;
    export let id;
    export let toggle = () => {};
    export let meta = {
        title: i18n("Digitization"),
        color: "#999",
        witness_id: 1
    };
    export let clickable = true;
    export let onlyColor = false;

    const docTitle = `${meta.title} #${id}`;

    const t = {
        nbImg: {en: "Number of extracted images", fr: "Nombre d'images extraites"},
        toggle: {en: "Toggle document pairs visibility", fr: "Activer/désactiver la visibilité des paires du document"},
    };
</script>

<div class="legend-item is-flex is-justify-content-space-between" class:inactive={!isActive}>
    <span class="is-flex is-align-items-center" style="gap: 0.5rem;">
        <span class="legend-color" class:inactive={!isActive} class:clickable={clickable && onlyColor}
             aria-label={docTitle} title={docTitle}
             style="background-color: {isActive ? meta.color : '#999'};"
             on:click={onlyColor ? toggle : null} on:keydown={null} role="button" tabindex="0"/>
        <span class="legend-label" class:is-hidden={onlyColor}>
            <a href={`${appUrl}/${appName}/witness/${meta.witness_id}/regions`} target="_blank">
                {meta.title}
            </a>
        </span>
    </span>
    <div class="tags has-addons ml-1 mb-0 is-flex-shrink-0" class:is-hidden={onlyColor}>
        <span class="tag is-rounded mb-0" class:is-light={!isActive} title={i18n("nbImg", t)}>
            {imgCount ?? "–"}
        </span>
        <button class="button tag is-rounded mb-0 pl-3 is-light" class:is-link={isActive}
                title={i18n("toggle", t)} aria-label={i18n("toggle", t)} on:click|stopPropagation={toggle}>
            {#if isActive}
                <svg class="icon is-small" viewBox="20 20 56 54" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M 74.03 46.4 C 68.2 37.48 58.41 32.15 47.86 32.15 C 37.3 32.15 27.51 37.48 21.68 46.4 L 21.38 46.86 L 21.68 47.32 C 27.51 56.24 37.3 61.57 47.86 61.57 C 58.41 61.57 68.2 56.24 74.03 47.31 L 74.33 46.86 L 74.03 46.4 Z M 24.57 46.86 C 28.87 40.84 35.18 36.8 42.25 35.37 C 41.07 35.98 39.97 36.77 39.01 37.74 C 36.61 40.17 35.28 43.4 35.28 46.82 C 35.28 50.26 36.61 53.49 39.01 55.91 C 40.04 56.94 41.2 57.76 42.46 58.38 C 35.3 57 28.92 52.93 24.57 46.86 Z M 47.99 54.79 C 43.66 54.79 40.13 51.23 40.13 46.85 C 40.13 44.74 40.95 42.75 42.43 41.25 C 43.91 39.75 45.89 38.92 47.99 38.92 C 50.09 38.92 52.06 39.75 53.55 41.25 C 55.03 42.75 55.85 44.74 55.85 46.85 C 55.85 48.97 55.03 50.97 53.55 52.47 C 52.06 53.96 50.08 54.79 47.99 54.79 Z M 53.76 58.29 C 54.95 57.68 56.04 56.89 57.01 55.92 C 59.41 53.49 60.73 50.26 60.73 46.83 C 60.73 41.9 57.97 37.62 53.93 35.47 C 60.81 36.96 66.93 40.98 71.13 46.86 C 66.9 52.79 60.71 56.82 53.76 58.29 Z" fill="currentColor" stroke="none"/>
                    <path d="M 45.26 47.3 C 46.69 47.3 47.86 46.13 47.86 44.68 C 47.86 43.23 46.69 42.05 45.26 42.05 C 43.83 42.05 42.67 43.23 42.67 44.68 C 42.67 46.13 43.83 47.3 45.26 47.3" fill="currentColor" stroke="none"/>
                    <ellipse cx="47.86" cy="46.86" rx="11.27" ry="11.27" fill="currentColor" stroke="none"/>
                </svg>
            {:else}
                <svg class="icon is-small" viewBox="20 20 56 54" xmlns="http://www.w3.org/2000/svg">
                    <path d="M 74.03 46.4 C 68.2 37.48 58.41 32.15 47.86 32.15 C 37.3 32.15 27.51 37.48 21.68 46.4 L 21.38 46.86 L 21.68 47.32 C 27.51 56.24 37.3 61.57 47.86 61.57 C 58.41 61.57 68.2 56.24 74.03 47.31 L 74.33 46.86 L 74.03 46.4 Z M 24.57 46.86 C 28.87 40.84 35.18 36.8 42.25 35.37 C 41.07 35.98 39.97 36.77 39.01 37.74 C 36.61 40.17 35.28 43.4 35.28 46.82 C 35.28 50.26 36.61 53.49 39.01 55.91 C 40.04 56.94 41.2 57.76 42.46 58.38 C 35.3 57 28.92 52.93 24.57 46.86 Z M 47.99 54.79 C 43.66 54.79 40.13 51.23 40.13 46.85 C 40.13 44.74 40.95 42.75 42.43 41.25 C 43.91 39.75 45.89 38.92 47.99 38.92 C 50.09 38.92 52.06 39.75 53.55 41.25 C 55.03 42.75 55.85 44.74 55.85 46.85 C 55.85 48.97 55.03 50.97 53.55 52.47 C 52.06 53.96 50.08 54.79 47.99 54.79 Z M 53.76 58.29 C 54.95 57.68 56.04 56.89 57.01 55.92 C 59.41 53.49 60.73 50.26 60.73 46.83 C 60.73 41.9 57.97 37.62 53.93 35.47 C 60.81 36.96 66.93 40.98 71.13 46.86 C 66.9 52.79 60.71 56.82 53.76 58.29 Z" fill="currentColor" stroke="none"/>
                    <path d="M 45.26 47.3 C 46.69 47.3 47.86 46.13 47.86 44.68 C 47.86 43.23 46.69 42.05 45.26 42.05 C 43.83 42.05 42.67 43.23 42.67 44.68 C 42.67 46.13 43.83 47.3 45.26 47.3" fill="currentColor" stroke="none"/>
                    <ellipse cx="47.86" cy="46.86" rx="11.27" ry="11.27" fill="currentColor" stroke="none"/>
                    <path d="M 22.86 71.86 L 72.86 21.86" fill="none" stroke="currentColor" stroke-width="3" stroke-miterlimit="10"/>
                    <path d="M 39 56 L 57 38" fill="none" stroke="#ffffff" stroke-width="3" stroke-miterlimit="10"/>
                </svg>
            {/if}
        </button>
    </div>
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
