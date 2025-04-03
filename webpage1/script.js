(function ($) {
    apiUrl = "https://9h1wag0ywe.execute-api.us-east-1.amazonaws.com/prod/"
    TableName = 'ccbda-lambda-first';

    $.ajax({
        type: 'GET',
        url: apiUrl,
        data: {'TableName': TableName},
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
            'TableName': TableName,
            'Item': {
                'thingID': {
                    'S': thingID
                }
            }
        }
        $.ajax({
            type: 'POST',
            url: apiUrl,
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
})(jQuery);