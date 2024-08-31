$(document).ready(function() {
    $('#id_date_range').daterangepicker({
        opens: 'right'
    });

    var selectedEvent = null;

    $('#calendar').fullCalendar({
        header: {
            left: 'prev,next today',
            center: 'title',
            right: 'month,agendaWeek,agendaDay'
        },
        events: events, // Use the globally defined events variable
        eventRender: function(event, element) {
            element.qtip({
                content: event.description,
                style: {
                    classes: 'qtip-bootstrap'
                }
            });
        },
        eventClick: function(event) {
            selectedEvent = event;
            if (confirm('Are you sure you want to delete this booking?')) {
                $.ajax({
                    url: '/bookings/delete/' + event.id + '/',
                    type: 'POST',
                    data: {
                        csrfmiddlewaretoken: $('input[name="csrfmiddlewaretoken"]').val(),
                        _method: 'DELETE'
                    },
                    success: function(response) {
                        if (response.status === 'success') {
                            $('#calendar').fullCalendar('removeEvents', selectedEvent.id);
                            alert('Booking deleted successfully');
                        } else {
                            alert('Failed to delete booking');
                        }
                    },
                    error: function() {
                        alert('Failed to delete booking');
                    }
                });
            }
        }
    });

    // Automatically hide the success alert after 5 seconds
    setTimeout(function() {
        $('.alert-success').fadeOut(500, function() {
            $(this).remove();
        });
    }, 5000);

    // Change Book button to Booked and turn it green after form submission
    $(document).ready(function() {
        $('form').submit(function(event) {
            event.preventDefault(); // Prevent the default form submission
            var form = $(this);
            var bookButton = $('#bookButton');
            
            $.ajax({
                type: form.attr('method'),
                url: form.attr('action'),
                data: form.serialize(),
                success: function(response) {
                    if (response.status === 'success') {
                        bookButton.text('Booked');
                        bookButton.removeClass('btn-primary').addClass('btn-success');
                        $('#success-message').text('Booking successful!').show().delay(5000).fadeOut();
                        location.reload(); // Reload the page to reflect changes
                    } else {
                        bookButton.text('Booking failed');
                        bookButton.removeClass('btn-primary').addClass('btn-danger');
                        var errorMsg = parseErrorMessage(response.errors);
                        $('#error-message').text('Booking failed: ' + errorMsg).show().delay(5000).fadeOut();
                    }
                },
                error: function(xhr) {
                    var errorMsg = "Failed to book. Please try again.";
                    if (xhr.status === 403) {
                        errorMsg = "CSRF verification failed. Please refresh the page and try again.";
                    } else if (xhr.responseJSON && xhr.responseJSON.errors) {
                        errorMsg = parseErrorMessage(xhr.responseJSON.errors);
                    }
                    bookButton.text('Booking failed');
                    bookButton.removeClass('btn-primary').addClass('btn-danger');
                    $('#error-message').text(errorMsg).show().delay(5000).fadeOut();
                }
            });
    
            setTimeout(function() {
                bookButton.text('Book');
                bookButton.removeClass('btn-success btn-danger').addClass('btn-primary');
            }, 5000);
        });
    });
    
    function parseErrorMessage(errors) {
        try {
            if (typeof errors === "string") {
                errors = JSON.parse(errors); // Parse the JSON string if needed
            }
            if (errors.__all__) {
                return errors.__all__.map(e => e.message).join(', ');
            } else {
                return "Unknown error occurred.";
            }
        } catch (e) {
            return "An error occurred while parsing the error message.";
        }
    }

    // Handle month and year navigation
    $('#jump_to_date_btn').click(function() {
        var month = $('#jump_to_month').val();
        var year = $('#jump_to_year').val();
        var date = new Date(year, month, 1); // Set to the first day of the selected month
        $('#calendar').fullCalendar('gotoDate', date);
    });

    // Handle the change event for the scheme selection (multi-select)
    $('#id_scheme').change(function() {
        var schemeIds = $(this).val();  // Get the selected scheme IDs (this is an array of selected values)
        var url = "/bookings/ajax/load-scheme-types/?scheme_ids=" + schemeIds.join(',');  // Construct the URL with multiple IDs

        $.ajax({
            url: url,
            success: function(data) {
                $('#id_scheme_type').html(data);  // Update the scheme type dropdown with the returned HTML
            },
            error: function(xhr, status, error) {
                console.error("Error occurred while loading scheme types: ", status, error);
            }
        });
    });
});
