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

    // Handle form submission via AJAX and prevent default browser form submission
    document.getElementById('bookingForm').addEventListener('submit', function(event) {
        event.preventDefault();  // Prevent the default form submission

        console.log("Form submission intercepted!");  // Debug to check if form submission is handled

        // Submit the form via AJAX
        fetch(this.action, {
            method: 'POST',
            body: new FormData(this),
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            }
        })
        .then(response => response.json())
        .then(data => {
            console.log("Response received:", data);  // Debug to check server response

            if (data.cron_jobs) {
                // Populate the textarea with cron jobs wrapped in backticks
                const cronJobsText = data.cron_jobs.map(job => `\`\`\`${job}\`\`\``).join('\n');
                document.getElementById('cronJobsContent').value = cronJobsText;

                console.log("Showing modal...");  // Debug to check modal triggering
                // Show the modal
                new bootstrap.Modal(document.getElementById('cronJobsModal')).show();

                // Handle "Add to Server" button click
                document.getElementById('addCronToServer').addEventListener('click', function() {
                    console.log("Adding cron job to server...");
                    // Here, you'd call the backend to run a script or trigger a server-side action
                    // to add the cron job on the server. For example:
                    fetch('/slot_booking/add-cron-job/', {
                        method: 'POST',
                        headers: {
                            'X-CSRFToken': getCookie('csrftoken'),
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({ cron_jobs: data.cron_jobs })
                    })
                    .then(response => response.json())
                    .then(serverData => {
                        if (serverData.success) {
                            alert('Cron jobs successfully added to the server!');
                            location.reload();  // Reload the page or calendar if needed
                        } else {
                            alert('Error adding cron jobs to the server.');
                        }
                    })
                    .catch(error => console.error('Error:', error));
                });

// Handle "Skip" button click
document.getElementById('skipCron').addEventListener('click', function(event) {
    event.preventDefault(); // Prevent any default action from occurring (like form submission)
    event.stopPropagation(); // Stop the event from bubbling up

    console.log("Skipping cron job addition...");
    
    // Hide the modal
    new bootstrap.Modal(document.getElementById('cronJobsModal')).hide();

    // Refresh the page to reload the slot booking calendar
    location.reload();  // Just refresh the page, no submission should happen
});
// Listen for when the modal is hidden, and ensure no form submission occurs
document.getElementById('cronJobsModal').addEventListener('hidden.bs.modal', function (event) {
    console.log('Modal closed, stopping any ongoing submission.');
    // You could stop any potential form submission logic here, but the key is to prevent default on "Skip".
});


                
            } else if (data.message) {
                console.log("Message:", data.message);
            }
        })
        .catch(error => {
            console.error('Error:', error);
        });
    });

    // Copy cron jobs to clipboard
    document.getElementById('copyCronJobs').addEventListener('click', function() {
        var cronText = document.getElementById('cronJobsContent').value;
        navigator.clipboard.writeText(cronText).then(function() {
            alert('Cron jobs copied to clipboard!');
        }, function(err) {
            alert('Failed to copy cron jobs: ', err);
        });
    });
});

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
