<script>
    import { createEventDispatcher } from "svelte";
    import { i18n } from "../../utils.svelte.js";

    /**
     * @typedef {Object} Props
     * @property {any} type - "node" | "edge"
     * @property {any} [target]
     */

    /** @type {Props} */
    let { type, target = null } = $props();

    let value = $state(type === "node" ? (target?.title ?? "") : (target?.label ?? ""));

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
        <div class="modal-background" onclick={close} onkeydown={null}></div>
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
                        <input class="input is-small" type="text" bind:value onkeydown={onKey}/>
                    </div>
                </div>
                <div class="buttons is-right mt-3">
                    <button class="button is-small" onclick={close}>{i18n("cancel", t)}</button>
                    <button class="button is-small is-link" onclick={save}>{i18n("save", t)}</button>
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
