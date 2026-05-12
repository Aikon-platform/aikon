import DocumentSetView from "./DocumentSetView.svelte";

const documentSetApp = new DocumentSetView({
    target: document.getElementById("document-set"),
    props: {
        docSet  // eslint-disable-line
    }
});

export default documentSetApp;
