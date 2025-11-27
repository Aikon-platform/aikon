<script>
    import { appLang, appName, csrfToken } from '../constants';
    import {onMount} from "svelte";

    export let viewTitle = "";
    export let witness = {};
    export let editUrl = "";

    let choices = {};
    let openContents = new Set();
    let editedField = null;
    let editedValue = "";

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

    function editMetadata(key, value) {
        editedField = key;
        editedValue = value;
    }

    async function saveField(key) {
        const data = {};
        data[key] = editedValue;

        const url = `${window.location.origin}/${appName}/witness/${witness.id}/update`;

        const response = await fetch(url, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": csrfToken
            },
            body: JSON.stringify(data)
        });

        if (!response.ok) {
            alert("Error saving value");
            return;
        }

        witness.metadata_full.wit[key].value = editedValue;
        editedField = null;
    }

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
                <a
                    href={editUrl}
                    class="edit-btn button is-small is-rounded is-link px-3 ml-2 mt-1"
                    title="Edit"
                >
                    <span class="iconify" data-icon="entypo:edit"></span>
                </a>
            </h1>
            {#each Object.entries(witness.metadata_full.wit) as [key, value]}
                <span class="witness-key">{value.label}</span>
                <span class="witness-value">
                    {#if editedField === key}
                        {#if choices[key]}
                            <select
                                class="select is-small is-link"
                                bind:value={editedValue}
                                on:change={() => saveField(key)}
                            >
                                {#each choices[key] as option}
                                    <option value={option.value}>
                                        {option.label}
                                    </option>
                                {/each}
                            </select>
                        {:else}
                            <input
                                class="input is-small"
                                bind:value={editedValue}
                                on:blur={() => saveField(key)}
                            />
                        {/if}
                    {:else}
                        <span
                            class="editable-span"
                            on:click={() => editMetadata(key, value)}
                        >
                            {value.value}
                        </span>
                    {/if}
                </span>
            {/each}

            {#if witness.metadata_full.contents?.length}
                <h3 class="title is-5 mb-3">Contents</h3>

                {#each witness.metadata_full.contents as content, id}
                    <div class="mb-3">
                        <div
                            class="is-flex is-justify-content-space-between witness-key"
                            on:click={() => showContent(id)}
                            on:keypress={() => showContent(id)}
                        >
                            {content.title}
                            {#if Object.entries(content.content).length }
                                <i class="fa-solid fa-chevron-down"></i>
                            {/if}
                        </div>

                        {#if openContents.has(id)}
                            <div class="mt-2 pl-3">
                                {#each Object.entries(content.content) as [key, value]}
                                    <div class="witness-value"><b>{key}:</b> {value}</div>
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
