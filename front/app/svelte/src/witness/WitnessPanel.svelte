<script>
    import { appName } from '../constants';
    import {onMount} from "svelte";
    import RegionsBtn from "../regions/RegionsBtn.svelte";

    export let viewTitle = "";
    export let witness = {};
    export let editUrl = "";

    let choices = {};
    let openContents = new Set();

    onMount(async () => {
        const url = `${window.location.origin}/${appName}/witness/select`;
        try {
            const response = await fetch(url);
            choices = await response.json();
        } catch (error) {
            console.error('Error:', error);
            return false;
        }
    });

    function showContent(id) {
        if (openContents.has(id)) {
            openContents.delete(id);
        } else {
            openContents.add(id);
        }
        openContents = new Set(openContents);
    }
</script>

<div class="m-4 py-5 px-4">
    <div class="content is-small mt-4">
        <div class="pb-2">
            <h1 class="title">
                {viewTitle}
                {#if witness.can_edit}
                    <a href={editUrl} title="Edit" class="edit-btn button is-small is-rounded is-link px-3 ml-2 mt-1">
                        <span class="iconify" data-icon="entypo:edit"/>
                    </a>
                {/if}
            </h1>

            <div class="cell is-left is-middle">
                <RegionsBtn/>
            </div>

            {#each Object.entries(witness.metadata_full.wit) as [key, value]}
                <span class="witness-key">{value.label}</span>
                <span class="witness-value">{value.value}</span>
            {/each}

            {#if witness.metadata_full.contents?.length}
                <h3 class="title is-5 mb-3">Contents</h3>

                {#each witness.metadata_full.contents as content, id}
                    <div class="mb-3">
                        <div class="is-flex is-justify-content-space-between witness-key"
                            on:click={() => showContent(id)} on:keypress={null}>
                            {content.title}
                            {#if Object.entries(content.content).length }
                                <i class="fa-solid fa-chevron-down"></i>
                            {/if}
                        </div>

                        {#if openContents.has(id)}
                            <div class="mt-2 pl-3">
                                {#each Object.entries(content.content) as [key, value]}
                                    <div class="witness-value">
                                        <b>{key}:</b> {value}
                                    </div>
                                {/each}
                            </div>
                        {/if}
                    </div>
                {/each}
            {/if}
        </div>
    </div>
</div>

<style>
    .witness-key {
        display: block;
        font-weight: bold;
        border-bottom: 1px solid var(--bulma-border);
        padding: 10px 0;
    }

    .witness-value {
        display: block;
        padding-top: 5px;
    }
</style>
