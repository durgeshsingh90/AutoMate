document.addEventListener('DOMContentLoaded', function() {
    var calendarEl = document.getElementById('calendar');

    // Initialize the FullCalendar
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
            if (confirm(`Are you sure you want to delete the booking for ${info.event.title}?`)) {
                deleteBooking(info.event.id);  // Pass the correct booking ID to the delete function
            }
        }
    });

    calendar.render();

    // Handle form submission and validation
    document.getElementById('bookingForm').addEventListener('submit', function(event) {
        event.preventDefault();  // Prevent the default form submission

        var openSlotChecked = document.getElementById('openSlot').checked;
        var formData = new FormData(this);  // Use FormData to handle the form data

        if (openSlotChecked) {
            // If "Open Slot" is checked, remove dateRange and timeSlot fields, and set timeSlot as "AM" and repeat_days as ["Tuesday", "Thursday"]
            formData.delete('dateRange');  // Remove the dateRange field
            formData.delete('timeSlot');   // Remove any timeSlot selections
            formData.append('timeSlot', 'AM');  // Set timeSlot to AM
            formData.delete('repeatBooking');  // Remove any other repeat days
            formData.append('repeatBooking', 'Tuesday');  // Set repeat days to Tuesday
            formData.append('repeatBooking', 'Thursday');  // Set repeat days to Thursday
        } else {
            // If "Open Slot" is not checked, handle regular date range and time slot selections
            var dateRange = document.getElementById('dateRange').value;
            var timeSlotChecked = document.querySelectorAll('input[name="timeSlot"]:checked').length > 0;

            // Basic validation for date range and time slot
            if (!dateRange || !timeSlotChecked) {
                alert('Please select a valid date range and at least one time slot.');
                return;
            }
        }

        // Continue with form submission via AJAX with the modified formData
        fetch(this.action, {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            }
        })
        .then(response => response.json())
        .then(data => {
            // Handle server error responses
            if (data.error) {
                // If there's an error (e.g., duplicate booking), display it to the user
                alert(data.error);  // Display error message in an alert
            } else if (data.cron_jobs) {
                // If booking was successful, display the cron jobs in the modal
                const cronJobsText = data.cron_jobs.map(job => `${job}`).join('\n');
                document.getElementById('cronJobsContent').value = cronJobsText;
                new bootstrap.Modal(document.getElementById('cronJobsModal')).show();
            } else if (data.message) {
                console.log("Message:", data.message);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('An unexpected error occurred. Please try again.');
        });
    });

    // Initialize the date range picker
    $('#dateRange').daterangepicker({
        locale: {
            format: 'DD/MM/YYYY'
        },
        startDate: moment().startOf('day'),
        endDate: moment().startOf('day')
    });

    // Handle "Open Slot" checkbox change event
    document.getElementById('openSlot').addEventListener('change', function() {
        var isChecked = this.checked;
        var dateRangeInput = document.getElementById('dateRange');
        var timeSlotCheckboxes = document.querySelectorAll('input[name="timeSlot"]');
        var amSlotCheckbox = document.getElementById('amSlot');

        if (isChecked) {
            // Set "Always" as the dateRange value and disable it
            originalDateRange = dateRangeInput.value;
            dateRangeInput.value = 'Always';
            dateRangeInput.disabled = true;

            // Disable time slots but make sure AM is selected
            timeSlotCheckboxes.forEach(function(checkbox) {
                checkbox.disabled = true;
            });
            amSlotCheckbox.checked = true;  // Ensure AM is checked

            // Clear error messages and styles if "Open Slot" is selected
            resetFormValidation();
        } else {
            // Restore the original dateRange value and enable it
            dateRangeInput.value = originalDateRange;
            dateRangeInput.disabled = false;

            // Enable time slots
            timeSlotCheckboxes.forEach(function(checkbox) {
                checkbox.disabled = false;
            });
        }
    });

    // Reload the page when the "Skip" button is clicked
    document.getElementById('skipCron').addEventListener('click', function(event) {
        event.preventDefault();  // Prevent default behavior
        location.reload();  // Reload the page
    });

    // Helper function to delete a booking
// Assuming you already have a function like this for deleting a booking
// Function to delete a booking
function deleteBooking(bookingId) {
    fetch(`/slot_booking/delete-booking/${bookingId}/`, {
        method: 'DELETE',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'Content-Type': 'application/json'
        }
    })
    .then(response => {
        if (response.ok) {
            alert('Booking and cron jobs deleted successfully!');
            location.reload();  // Reload the page after deletion
        } else {
            alert('Error deleting booking or cron jobs!');
        }
    })
    .catch(error => {
        console.error('Error:', error);
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

    // Helper function to reset validation errors
    function resetFormValidation() {
        // Clear any previous error styles or messages
        document.getElementById('dateRange').classList.remove('is-invalid');
        document.getElementById('dateRangeError').innerText = '';
        
        document.getElementById('timeSlotContainer').classList.remove('border', 'border-danger', 'rounded');
        document.getElementById('timeSlotError').innerText = '';
    }

    // Add Cron Jobs to Server on Button Click
    document.getElementById('addCronToServer').addEventListener('click', function(event) {
        event.preventDefault();  // Prevent any form submission action

        var cronJobsText = document.getElementById('cronJobsContent').value.trim();
        var owner = document.getElementById('owner').value;  // Assuming 'owner' is available in the form
        var server = document.getElementById('server').value;  // Assuming 'server' is available in the form

        if (!cronJobsText || !owner || !server) {
            alert('Missing cron jobs, owner, or server information.');
            return;
        }

        // Prepare cron jobs as an array
        var cronJobs = cronJobsText.split('\n');

        // Send a request to the server to add the cron jobs via SSH
        fetch('/slot_booking/add-cron-job/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')  // Make sure you have CSRF token handling
            },
            body: JSON.stringify({
                cron_jobs: cronJobs,
                owner: owner,
                server: server
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('Cron jobs successfully added to the server!');
                location.reload();  // Reload the page or calendar if needed
            } else {
                alert('Error adding cron jobs to the server: ' + data.error);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('An error occurred while adding cron jobs to the server.');
        });
    });
});
