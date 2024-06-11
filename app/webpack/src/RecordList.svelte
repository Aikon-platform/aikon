<script>
    import {refToIIIF} from "./utils.js";

    export let records = [];
    export let appLang = 'en';

    let cart = [];
    $: cartNb = cart.length;
    $: if (cartNb >= 10) {
        alert('Do you wish to save your cart?')
    }

    function addToCart() {
        cart = [...cart, record];
        console.log(cartNb);
    }

</script>

<style>
    .card.image {
        overflow: hidden;
        display: flex;
        justify-content: center;
        align-items: center;
    }
</style>

<!--{#await promise}
    <p>...waiting</p>
{:then number}
    <p>promise has resolved to {number}</p>
{:catch error}
	<p>{error}</p>
{/await}-->

<div>
    {#each records as record (record.id)}
        <div class="record block">
            <div id="record-{record.id}" class="card">
                <div class="card-content">
                    <div class="media">
                        <div class="media-left">
                            <figure class="card image is-96x96">
                                <img src="{refToIIIF(record.img, 'full', '250,')}" alt="Record illustration"/>
                            </figure>
                        </div>
                        <div class="media-content">
                            <p class="title is-4">
                                <span class="tag px-2 py-1 mb-1 is-dark is-rounded">#{record.id}</span>
                                {record.title}
                                {#if record.is_public}
                                    <span class="pl-3 icon-text is-size-7 is-center has-text-weight-normal">
                                        <span class="icon has-text-success"><i class="fas fa-check-circle"></i></span>
                                        <span style="margin-left: -0.5rem">Public</span>
                                    </span>
                                {/if}
                            </p>

                            <p class="subtitle is-6 mb-0 ml-2">
                                {record.user}
                                <span class="tag p-1 mb-1">{record.updated_at}</span>
                            </p>

                            <table class="table pl-2 is-fullwidth">
                                <tbody>
                                {#each Object.entries(record.metadata) as [field, value]}
                                    <tr>
                                        <th class="is-narrow is-3">{field}</th>
                                        <td>{value}</td>
                                    </tr>
                                {/each}
                                </tbody>
                            </table>


                        </div>
                        <div class="media-right">
                            <button class="button" id="cart-button-{record.id}" onclick="toggleCart('{record.id}')" on:click={addToCart}>
                                <i class="fa-solid fa-cart-plus"></i> {appLang === 'en' ? 'Add to cart' : 'Ajouter au Panier'}
                            </button>
                        </div>
                    </div>


                </div>
            </div>
        </div>
    {:else}
        <p>No records found</p>
    {/each}
</div>
