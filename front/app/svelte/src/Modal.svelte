<script>
    import { appLang } from './constants';
    import { closeModal, openModal } from './utils.js';
</script>

<button id="hidden-msg-btn" use:openModal data-target="msg-modal" hidden/>

<div id="msg-modal" class="modal fade" use:closeModal tabindex="-1" aria-labelledby="selection-modal-label" aria-hidden="true">
    <div id="modal-bkg" class="modal-background"/>
    <div class="modal-content">
        <div class="modal-card-head media mb-0">
            <div class="title is-4 mb-0 media-content">
                <span id="modal-title" class="mb-0"></span>
            </div>
            <button class="delete media-left" aria-label="close"></button>
        </div>
        <section id="modal-body" class="modal-card-body">
            <div id="modal-msg"></div>
            <div class="py-3">
                <slot name="content"/>
            </div>
        </section>

        <footer id="modal-footer" class="modal-card-foot is-center pt-3" hidden>
            <div class="buttons">
                <button id="cancel-btn" class="button is-link is-light button-close">
                    {appLang === 'en' ? 'Abort' : 'Retour'}
                </button>
                <button id="ok-btn" class="button is-link button-close">OK</button>
            </div>
        </footer>
    </div>
</div>
