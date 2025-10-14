import DocumentSetView from './DocumentSetView.svelte';

const documentSetApp = new DocumentSetView({
    target: document.getElementById('document-set'),
    props: {
        documentSet
    }
});
export default documentSetApp;
