<script>
    import { onMount } from 'svelte';
    import { appLang } from '../constants';
    import Autocomplete from "./Autocomplete.svelte";

    export let recordsStore;
    const { recordSearch, searchParams } = recordsStore;

    export let searchFields = [];
    let formData = {};

    onMount(() => {
        // fill search form according to URL search params
        const params = $searchParams ?? new URLSearchParams(window.location.search);
        searchFields.forEach(field => {
            formData[field.name] = params.get(field.name) || field.initial || '';
        });
    });

    function handleSearch(event) {
        event.preventDefault();
        recordSearch(formData);
    }

    function isAutocomplete(field) {
        return field.type.includes('ChoiceField') && field.choices.length > 5;
    }

    function handleSelect(field, event) {
        formData[field.name] = event.detail.id;
    }

    const isMulti = field => field.type.includes('Multiple');
</script>

{#if searchFields.length > 0}
    <form on:submit={handleSearch} class="fixed-grid is-center">
        <article class="message grid">
            {#each searchFields as field}
                <div class="search-field field columns is-middle">
                    <label for={field.name} class="label column is-small is-3">{field.label}</label>
                    <div class="control has-icons-right column is-9">
                        {#if field.type.includes('ChoiceField')}
                            {#if isAutocomplete(field)}
                                <Autocomplete items={field.choices}
                                    name={field.name} id={field.name}
                                    on:select={(event) => handleSelect(field, event)}
                                />
                            {:else}
                                <div class="select is-small is-wide {isMulti(field) ? 'is-multiple' : ''}">
                                    <select id={field.name} name={field.name} bind:value={formData[field.name]} class="is-wide"
                                            {...isMulti(field) ? { size: 3, multiple: true } : {}}>
                                        {#if !isMulti(field)}
                                            <option value="" disabled selected class="faded">
                                                {appLang === 'en' ? 'Select' : 'Sélectionner'} ...
                                            </option>
                                        {/if}
                                        {#each field.choices as choice}
                                            <option value={choice.id}>{choice.label}</option>
                                        {/each}
                                    </select>
                                </div>
                            {/if}
                        {:else if field.type === 'BooleanField'}
                            <input type='checkbox' id={field.name} name={field.name} bind:checked={formData[field.name]}>
                        {:else if field.type.includes('Date')}}
                            <input type='date' class='input is-small is-wide' id={field.name} name={field.name} bind:value={formData[field.name]}>
                        {:else if field.type === 'IntegerField' || field.type === 'FloatField'}
                            <input type='number' class='input is-small is-wide' id={field.name} name={field.name} bind:value={formData[field.name]}>
                        {:else}
                            <input type='text' class='input is-small is-wide' id={field.name} name={field.name} bind:value={formData[field.name]}>
                        {/if}
                    </div>
                    <!--{#if field.help_text}-->
                    <!--    <small>{field.help_text}</small>-->
                    <!--{/if}-->
                </div>
            {/each}
        </article>

        <div class="panel-block columns">
            <button type="submit" class="button is-link is-outlined is-fullwidth">
                <i class="fa-solid fa-magnifying-glass"></i>
                {appLang === 'en' ? 'Search' : 'Rechercher'}
            </button>
        </div>
    </form>
{/if}

<style>
    .search-field {
        margin-bottom: .2rem;
    }
    label {
        text-align: left;
        padding-left: 2.5em;
    }
</style>
