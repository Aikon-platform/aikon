document.addEventListener('DOMContentLoaded', function () {
    setTimeout(function() {
        const urlParams = new URLSearchParams(window.location.search);

        document.querySelectorAll('input, select').forEach(field => {
            const name = field.name;

            if (urlParams.has(name)) {
                const value = urlParams.get(name);

                if (field.type === 'checkbox') {
                    field.checked = (value === 'True');
                } else if ($(field).is('select') && $(field).data('select2')) {
                    const fetchAndSetTitle = function(id) {
                        $.ajax({
                            url: `/${APP_NAME}/set-title/${id}`,
                            method: 'GET',
                            success: function(response) {
                                let title = response.title;
                                let chosenSet = new Option(title, id, true, true);
                                $(field).append(chosenSet).trigger('change');
                            },
                            error: function() {
                                console.error('Failed to fetch document set title');
                            }
                        });
                    };

                    fetchAndSetTitle(value);
                } else {
                    field.value = value;
                }
            }
        });
    }, 100);
});
