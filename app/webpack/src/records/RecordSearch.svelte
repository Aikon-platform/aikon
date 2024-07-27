<script>
    import { recordsStore } from "./recordStore.js";
    const { resultPage, fetchPage } = recordsStore;

    function handleSearch(event) {
        event.preventDefault();
        const form = event.target;
        const formData = new FormData(form);
        const queryString = new URLSearchParams(formData).toString();
        resultPage.update(fetchPage(queryString));
    }
</script>

<form on:submit={handleSearch}>
    <!-- Your form fields here -->
    <button type="submit">Search</button>
</form>
