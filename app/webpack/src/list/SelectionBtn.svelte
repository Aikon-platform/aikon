<script>
    export let addAnimation = false;
    export let removeAnimation = false;
    export let selectionLength = 0;
    export let appLang = 'en';
</script>

<style>
    .set-container {
        display: flex;
        justify-content: flex-end;
        gap: 10px;
        position: fixed;
        bottom: 0;
        right: 0;
        z-index: 1;
    }
    #set-btn {
        border-radius: 0;
    }
    @keyframes addAnimation {
        0%, 100% { transform: translateY(0); }
        25% { transform: translateY(-7px); }
        75% { transform: translateY(7px); }
    }

    @keyframes removeAnimation {
        0%, 100% { transform: translateX(0); }
        25% { transform: translateX(-5px); }
        75% { transform: translateX(5px); }
    }

    .add-animation span {
        animation: addAnimation 0.3s ease-in-out;
    }

    .remove-animation span {
        animation: removeAnimation 0.3s ease-in-out;
    }
</style>

<div class="set-container">
    <button id="set-btn"
            class="button px-5 py-4 is-link js-modal-trigger"
            data-target="selection-modal"
            class:add-animation={addAnimation}
            class:remove-animation={removeAnimation}>
        <span>
            <i class="fa-solid fa-book-bookmark"></i>
            {appLang === 'en' ? 'Selection' : 'Sélection'}
            (<span id="selection-count">{selectionLength}</span>)
        </span>
    </button>
</div>
