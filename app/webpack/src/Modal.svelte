<script>
    export let appLang = 'en';
</script>

<button id="hidden-msg-btn" class="js-modal-trigger" data-target="msg-modal" hidden/>

<div id="msg-modal" class="modal fade" tabindex="-1" aria-labelledby="selection-modal-label" aria-hidden="true">
    <div id="modal-bkg" class="modal-background"/>
    <div class="modal-content">
        <div class="modal-card-head media mb-0">
            <div class="title is-4 mb-0 media-content">
                <h3 id="modal-title" class="mb-0"></h3>
            </div>
            <button class="delete media-left" aria-label="close"></button>
        </div>
        <section id="modal-body" class="modal-card-body"></section>
        <footer id="modal-footer" class="modal-card-foot is-center pt-1" hidden>
            <div class="buttons">
                <button id="cancel-btn" class="button is-link is-light">
                    {appLang === 'en' ? 'Cancel' : 'Annuler'}
                </button>
                <button id="ok-btn" class="button is-link">OK</button>
            </div>
        </footer>
    </div>
</div>
