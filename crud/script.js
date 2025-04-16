async function configure() {
    const request = new Request("./variables.json");
    const response = await fetch(request);
    const variables = await response.json();
    new WrapperWS(variables.url);
}

(function ($) {
    $.getJSON("variables.json", function (data) {
        var config = data;
        $.ajax({
            type: 'GET',
            url: config.url,
            data: {'TableName': config.table},
            crossDomain: true,
            success: function (result) {
                $.each(result.Items, function (i, item) {
                    $('#items').append('<li>' + item.thingID.S + '</li>');
                });
            },
            error: function (xhr, status, error) {
                $('#error').toggle().append('<div>' + error + '</div>');
            }
        });

        // Form submit
        $("#form").submit(function (event) {
            event.preventDefault();
            thingID = $('#thingID').val();
            payload = {
                'TableName': config.table,
                'Item': {
                    'thingID': {
                        'S': thingID
                    }
                }
            }
            $.ajax({
                type: 'POST',
                url: config.url,
                crossDomain: true,
                contentType: 'application/json',
                data: JSON.stringify(payload),
                cache: false,
                success: function (result) {
                    $('#thingID').val('');
                    $('#items').append('<li>' + thingID + '</li>');
                },
                error: function (xhr, status, error) {
                    $('#error').toggle().append('<div>' + status + ',' + error + '</div>');
                }
            });
        });
    });
})(jQuery);