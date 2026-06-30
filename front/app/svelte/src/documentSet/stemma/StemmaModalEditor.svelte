<script>
    import { createEventDispatcher } from "svelte";
    import { i18n } from "../../utils.js";

    export let type;        // "node" | "edge"
    export let target = null;

    let value = type === "node" ? (target?.title ?? "") : (target?.label ?? "");

    const dispatch = createEventDispatcher();
    const close = () => dispatch("close");
    const save = () => dispatch("save", { value: value.trim() });
    const onKey = e => { if (e.key === "Enter") save(); if (e.key === "Escape") close(); };

    const t = {
        node:   { en: "Rename node in stemma", fr: "Renommer un nœud au sein du stemma" },
        edge:   { en: "Qualify connection", fr: "Qualifier le lien" },
        save:   { en: "Save", fr: "Enregistrer" },
        cancel: { en: "Cancel", fr: "Annuler" },
    };
</script>

{#if target}
    <div class="modal is-active">
        <div class="modal-background" on:click={close} on:keydown={null}/>
        <div class="modal-content" style="max-width: 300px;">
            <div class="box">
                <h4 class="title is-6 mb-4">{i18n(type, t)}</h4>
                <div class="field is-flex is-align-items-center" style="gap: 0.5rem;">
                    {#if type === "node"}
                        <span class="color-dot" style="background: {target.color}"></span>
                    {:else}
                        <span class="color-dot" style="background: {target.source.color}"></span>
                        <span>→</span>
                        <span class="color-dot" style="background: {target.target.color}"></span>
                    {/if}
                    <div class="control is-flex-grow-1">
                        <input class="input is-small" type="text" bind:value on:keydown={onKey}/>
                    </div>
                </div>
                <div class="buttons is-right mt-3">
                    <button class="button is-small" on:click={close}>{i18n("cancel", t)}</button>
                    <button class="button is-small is-link" on:click={save}>{i18n("save", t)}</button>
                </div>
            </div>
        </div>
    </div>
{/if}

<style>
    .color-dot {
        width: 12px;
        height: 12px;
        border-radius: 50%;
        display: inline-block;
    }
</style>
