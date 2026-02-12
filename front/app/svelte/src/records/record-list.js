import RecordList from "./RecordList.svelte";

const recordApp = new RecordList({
    target: document.getElementById("record-list"),
    props: {
        searchFields,  // eslint-disable-line
        modelName,  // eslint-disable-line
        modelTitle  // eslint-disable-line
    }
});

export default recordApp;
