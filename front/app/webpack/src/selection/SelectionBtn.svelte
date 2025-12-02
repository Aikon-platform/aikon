<script>
    import { appLang } from '../constants';
    export let selectionLength = 0;

    let previousLength = selectionLength;
    $: if (selectionLength !== previousLength) {
        const isIncreasing = selectionLength > previousLength;
        previousLength = selectionLength;

        const button = document.getElementById('btn-content');
        if (button) {
            button.animate([
                { transform: isIncreasing ? 'translateY(-7px)' : 'translateX(-5px)' },
                { transform: isIncreasing ? 'translateY(7px)' : 'translateX(5px)' },
                { transform: 'translate(0)' }
            ], {
                duration: 300,
                easing: 'cubic-bezier(0.65, 0, 0.35, 1)'
            });
        }
    }
</script>

<div class="set-container">
    <button id="set-btn"
            class="button px-5 py-4 is-link js-modal-trigger"
            data-target="selection-modal">
        <span id="btn-content">
            <i class="fa-solid fa-book-bookmark"></i>
            {appLang === 'en' ? 'Selection' : 'Sélection'}
            ({selectionLength})
        </span>
    </button>
</div>

<style>
    .set-container {
        display: flex;
        justify-content: flex-end;
        gap: 10px;
        position: fixed;
        bottom: 0;
        right: 0;
        z-index: 10;
    }
    #set-btn {
        border-radius: 0;
    }
</style>
