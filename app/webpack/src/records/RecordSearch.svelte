<script>
    import { recordsStore } from "./recordStore.js";
    const { fetchPage } = recordsStore;
    import { appLang } from '../constants';

    export let searchFields = [];
    let formData = {};
    searchFields.forEach(field => {
        formData[field.name] = field.initial || '';
    });

    function handleSearch(event) {
        event.preventDefault();
        const queryString = new URLSearchParams(formData).toString();
        fetchPage(queryString);
    }
</script>

{#if searchFields.length > 0}
    <form on:submit={handleSearch}>
        <div class="columns">
            <div class="panel is-link column p-0 mx-4 my-3">
                {#each searchFields as field}
                    <div class="panel-block py-1">
                        <label for={field.name}>{field.label}</label>
                        {#if field.type === 'ChoiceField'}
                            <select id={field.name} name={field.name} bind:value={formData[field.name]}>
                                <option value="">Select {field.label}</option>
                                {#each field.choices as choice}
                                    <option value={choice.value}>{choice.label}</option>
                                {/each}
                            </select>
                        {:else if field.type === 'BooleanField'}
                            <input type="checkbox" id={field.name} name={field.name} bind:checked={formData[field.name]}>
                        {:else if field.type === 'DateTimeField' || field.type === 'DateField'}
                            <input type='date'
                                   id={field.name}
                                   name={field.name}
                                   bind:value={formData[field.name]}>
                        {:else}
                            <input type='text'
                                   id={field.name}
                                   name={field.name}
                                   bind:value={formData[field.name]}>
                        {/if}
                        {#if field.help_text}
                            <small>{field.help_text}</small>
                        {/if}
                    </div>
                {/each}
            </div>
        </div>

        <div class="panel-block columns">
            <button type="submit" class="button is-link is-outlined is-fullwidth">
                <i class="fa-solid fa-magnifying-glass"></i>
                {appLang === 'en' ? 'Search' : 'Rechercher'}
            </button>
        </div>
    </form>
{/if}
