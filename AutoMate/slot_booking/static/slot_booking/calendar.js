document.addEventListener('DOMContentLoaded', function() {
    var calendarEl = document.getElementById('calendar');

    var calendar = new FullCalendar.Calendar(calendarEl, {
        initialView: 'dayGridMonth',
        headerToolbar: {
            left: 'prev,next today',
            center: 'title',
            right: 'dayGridMonth,timeGridWeek,timeGridDay'
        },
        buttonText: {
            today: 'Today',
            month: 'Month',
            week: 'Week',
            day: 'Day'
        },
        height: 'auto',
        contentHeight: 'auto',

        // Fetch events from the Django view returning bookings
        events: '/slot_booking/get-bookings/',

        eventClick: function(info) {
            // Handle double-click by asking user for confirmation
            if (confirm(`Are you sure you want to delete the booking for ${info.event.title}?`)) {
                // If confirmed, send a request to delete the booking
                deleteBooking(info.event.id);
            }
        }
    });

    calendar.render();

    // Handle date jump logic
    document.getElementById('jumpToDate').addEventListener('click', function() {
        var month = document.getElementById('monthSelect').value;
        var year = document.getElementById('yearSelect').value;
        var selectedDate = new Date(year, month);
        calendar.gotoDate(selectedDate);
    });

    // Form submit handler to prevent double bookings
    const bookingForm = document.querySelector('form');

    bookingForm.addEventListener('submit', function(event) {
        event.preventDefault();  // Prevent default form submission

        const formData = new FormData(bookingForm);  // Collect form data

        // Send the form data via AJAX
        fetch(bookingForm.action, {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': getCookie('csrftoken'),  // Include CSRF token
            },
        })
        .then(response => {
            if (!response.ok) {
                return response.text().then(text => { throw new Error(text); });
            }
            return response.text();
        })
        .then(result => {
            alert(result);  // Show success message
            location.reload();  // Reload the page after successful booking
        })
        .catch(error => {
            // Show error message in a popup if there's a conflict (double booking)
            alert(error.message);
        });
    });
});

function deleteBooking(bookingId) {
    // Send an AJAX request to Django to delete the booking by ID
    fetch(`/slot_booking/delete-booking/${bookingId}/`, {
        method: 'DELETE',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'), // Make sure you pass the CSRF token
            'Content-Type': 'application/json'
        }
    })
    .then(response => {
        if (response.ok) {
            alert('Booking deleted successfully!');
            location.reload();  // Reload the calendar after deletion
        } else {
            alert('Error deleting booking!');
        }
    });
}

// Helper function to get CSRF token from cookies
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

$(function() {
    // Initialize the date range picker
    $('#dateRange').daterangepicker({
        locale: {
            format: 'DD/MM/YYYY'  // Customize the format as per your requirement
        },
        startDate: moment().startOf('day'),
        endDate: moment().add(1, 'month').startOf('day')  // Default range
    });
});
