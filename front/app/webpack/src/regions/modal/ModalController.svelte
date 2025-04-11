<script>
    import { appLang } from "../../constants.js";
    import { eyeSvg } from "./utils.js";

    import TooltipGeneric from "../../ui/TooltipGeneric.svelte";
    import ModalWrapper from "./ModalWrapper.svelte";
    import { destroy_block } from "svelte/internal";

    //////////////////////////////////////////

    /** @type {string} a value of RegionPair.img_(1|2): the "main" image to display */
    export let mainImg;
    /** @type {string?} a value of RegionPair.img_(1|2): an optional image to compare mainImg with (if mainImg is a similarity image, compareImg would be the query image) */
    export let compareImg = undefined;

    const htmlId = `modal-opener-${window.crypto.randomUUID()}`;

    /** @type {boolean} when true, display the modal */
    $: displayModal = false;
    /** @type {SvelteComponent?} */
    $: modal = mountModal(displayModal, modal);

    //////////////////////////////////////////

    /** mounting of the `ModalWrapper` is done in an imperative way and not in the template: this allows us to insert the modal at the end of the html `body` to ensure the modal is not shadowed by other elts */
    const mountModal = (_displayModal, _modal) => {;
        if (_displayModal) {
            _modal = new ModalWrapper({
                target: document.querySelector("body"),
                props: {
                    mainImg: mainImg,
                    compareImg: compareImg
                }
            })
            _modal.$on("closeModal", onCloseModal);
        } else if (!_displayModal && modal!=null ) {
            _modal.$destroy();
        }
        return _modal;
    }

    const onClick = (e) => displayModal = !displayModal;
    const onCloseModal = (e) => displayModal = false;

</script>


<div id={htmlId}>
    <TooltipGeneric targetHtmlId={htmlId}
                    tooltipText={appLang==="fr"
                                ? "Vue détaillée"
                                : "Detailed view"}
    ></TooltipGeneric>
    <button class="button tag"
            on:click={onClick}
    >
        <svg width="54" height="30" viewBox="0 0 54 30" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M53.6443 14.25C47.7042 5.33 37.7293 0 26.9801 0C16.2206 0 6.24576 5.33 0.305653 14.25L0 14.71L0.305653 15.17C6.24576 24.09 16.2206 29.42 26.9801 29.42C37.7293 29.42 47.7042 24.09 53.6443 15.16L53.95 14.71L53.6443 14.25ZM3.25025 14.71C7.63146 8.69001 14.0606 4.65 21.2641 3.22C20.0619 3.83 18.9411 4.62 17.963 5.59C15.5176 8.02 14.1625 11.25 14.1625 14.67C14.1625 18.11 15.5176 21.34 17.963 23.76C19.0124 24.79 20.1943 25.61 21.4781 26.23C14.1829 24.85 7.6824 20.78 3.25025 14.71ZM27.1125 22.64C22.7008 22.64 19.1041 19.08 19.1041 14.7C19.1041 12.59 19.9396 10.6 21.4475 9.10001C22.9555 7.60001 24.9729 6.77 27.1125 6.77C29.2522 6.77 31.2594 7.60001 32.7775 9.10001C34.2855 10.6 35.121 12.59 35.121 14.7C35.121 16.82 34.2855 18.82 32.7775 20.32C31.2594 21.81 29.242 22.64 27.1125 22.64ZM32.9915 26.14C34.204 25.53 35.3146 24.74 36.3029 23.77C38.7482 21.34 40.0932 18.11 40.0932 14.68C40.0932 9.75 37.281 5.47001 33.1647 3.32001C40.1747 4.81001 46.4102 8.83001 50.6896 14.71C46.3797 20.64 40.0728 24.67 32.9915 26.14Z" fill="black"/>
            <path d="M26.9804 25.98C33.3222 25.98 38.4633 20.9343 38.4633 14.71C38.4633 8.48576 33.3222 3.44 26.9804 3.44C20.6386 3.44 15.4976 8.48576 15.4976 14.71C15.4976 20.9343 20.6386 25.98 26.9804 25.98Z" fill="black"/>
            <path d="M17.9529 23.85L36.2928 5.85001" stroke="black" stroke-width="3" stroke-miterlimit="10"/>
        </svg>
    </button>
</div>


<style>
    .button {
        padding-left: .5em;
        padding-right: .5em;
    }
    svg, path {
        fill: var(--bulma-link);
        stroke: var(--bulma-link);
    }
</style>
