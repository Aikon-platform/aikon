$(function() {
    /**
     * Update the "country", "latitude" and "longitude" fields with the retrieved data
     */
    document.querySelector("#id_name").onchange=function() {
        const [name, countryCode] = $(this).find("option:selected").text().split(" | ");
        $.ajax({
            url: "/retrieve_place_info/",
            data: { "name": name, "countryCode": countryCode},
            dataType: "json",
            success: function(data) {
                $("#id_country").val(data.country);
                $("#id_latitude").val(data.latitude);
                $("#id_longitude").val(data.longitude);
            },
        });
    }
});
