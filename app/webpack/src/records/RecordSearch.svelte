<script>
    import { onMount } from 'svelte';
    import { appLang } from '../constants';

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

    const isMulti = field => field.type.includes('Multiple');
</script>

{#if searchFields.length > 0}
    <form on:submit={handleSearch} class="fixed-grid container">
        <article class="message grid">
            {#each searchFields as field}
                <div class="field columns is-middle">
                    <label for={field.name} class="label column is-small is-3">{field.label}</label>
                    <div class="control has-icons-right column is-8">
                        {#if field.type.includes('ChoiceField')}
                            <div class="select is-small is-wide {isMulti(field) ? 'is-multiple' : ''}">
                                <select id={field.name} name={field.name} bind:value={formData[field.name]} class="is-wide"
                                        {...isMulti(field) ? { size: 3, multiple: true } : {}}>
                                    {#if !isMulti(field)}
                                        <option value="" disabled selected class="faded">Select ...</option>
                                    {/if}
                                    {#each field.choices as choice}
                                        <option value={choice.value}>{choice.label}</option>
                                    {/each}
                                </select>
                            </div>
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
