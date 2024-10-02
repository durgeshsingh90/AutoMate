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
        },

        // Show all booking details in a persistent tooltip box on hover
        eventMouseEnter: function(info) {
            var tooltip = document.createElement('div');
            tooltip.classList.add('event-tooltip');

            var content = '<strong>Booking Details:</strong><br>';
            for (var key in info.event.extendedProps) {
                if (info.event.extendedProps.hasOwnProperty(key)) {
                    content += `<strong>${key}:</strong> ${info.event.extendedProps[key]}<br>`;
                }
            }

            tooltip.innerHTML = content;
            document.body.appendChild(tooltip);

            var rect = info.el.getBoundingClientRect();
            tooltip.style.position = 'absolute';
            tooltip.style.left = rect.left + window.pageXOffset + 'px';
            tooltip.style.top = rect.bottom + window.pageYOffset + 'px';

            tooltip.addEventListener('mouseenter', function() {
                tooltip.stillHovered = true;
            });

            tooltip.addEventListener('mouseleave', function() {
                tooltip.stillHovered = false;
                tooltip.remove();
            });

            info.el.tooltip = tooltip;
            info.el.stillHovered = true;

            info.el.addEventListener('mouseleave', function() {
                info.el.stillHovered = false;
                setTimeout(function() {
                    if (!info.el.stillHovered && !tooltip.stillHovered) {
                        tooltip.remove();
                    }
                }, 100);
            });
        }
    });

    calendar.render();

    // Handle "Go to Date" button logic
    document.getElementById('jumpToDate').addEventListener('click', function() {
        var month = document.getElementById('monthSelect').value;
        var year = document.getElementById('yearSelect').value;

        if (!month || !year) {
            alert("Please select both a valid month and year.");
            return;
        }

        // Construct the date object using the selected month and year
        var selectedDate = new Date(year, month); // month is 0-indexed, so 0=January, 11=December

        // Use FullCalendar's gotoDate method to navigate to the selected date
        calendar.gotoDate(selectedDate);
    });

    // Handle form submission and validation
    document.getElementById('bookingForm').addEventListener('submit', function(event) {
        event.preventDefault();  // Prevent the default form submission

        var openSlotChecked = document.getElementById('openSlot').checked;
        var formData = new FormData(this);  // Use FormData to handle the form data

        if (openSlotChecked) {
            formData.delete('dateRange');  // Remove the dateRange field
            formData.delete('timeSlot');   // Remove any timeSlot selections
            formData.append('timeSlot', 'AM');  // Set timeSlot to AM
            formData.delete('repeatBooking');  // Remove any other repeat days
            formData.append('repeatBooking', 'Tuesday');  // Set repeat days to Tuesday
            formData.append('repeatBooking', 'Thursday');  // Set repeat days to Thursday
        } else {
            var dateRange = document.getElementById('dateRange').value;
            var timeSlotChecked = document.querySelectorAll('input[name="timeSlot"]:checked').length > 0;

            if (!dateRange || !timeSlotChecked) {
                alert('Please select a valid date range and at least one time slot.');
                return;
            }
        }

        fetch(this.action, {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                alert(data.error);
            } else if (data.cron_jobs) {
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
            originalDateRange = dateRangeInput.value;
            dateRangeInput.value = 'Always';
            dateRangeInput.disabled = true;

            timeSlotCheckboxes.forEach(function(checkbox) {
                checkbox.disabled = true;
            });
            amSlotCheckbox.checked = true;
            resetFormValidation();
        } else {
            dateRangeInput.value = originalDateRange;
            dateRangeInput.disabled = false;

            timeSlotCheckboxes.forEach(function(checkbox) {
                checkbox.disabled = false;
            });
        }
    });

    // Copy cron jobs to clipboard functionality
    document.getElementById('copyCronJobs').addEventListener('click', function(event) {
        event.preventDefault();  // Prevent form submission
        var cronText = document.getElementById('cronJobsContent').value;
        navigator.clipboard.writeText(cronText).then(function() {
            var copyButton = document.getElementById('copyCronJobs');
            copyButton.textContent = 'Copied!';
            copyButton.style.backgroundColor = '#28a745';
            copyButton.style.color = '#fff';

            setTimeout(function() {
                copyButton.textContent = 'Copy';
                copyButton.style.backgroundColor = '';
                copyButton.style.color = '';
            }, 1000);
        }, function(err) {
            alert('Failed to copy cron jobs: ', err);
        });
    });

    // Reload the page when the "Skip" button is clicked
    document.getElementById('skipCron').addEventListener('click', function(event) {
        event.preventDefault();
        location.reload();
    });

    // Add Cron Jobs to Server on Button Click
    document.getElementById('addCronToServer').addEventListener('click', function(event) {
        event.preventDefault();
        var cronJobsText = document.getElementById('cronJobsContent').value.trim();
        var owner = document.getElementById('owner').value;
        var server = document.getElementById('server').value;

        if (!cronJobsText || !owner || !server) {
            alert('Missing cron jobs, owner, or server information.');
            return;
        }

        var cronJobs = cronJobsText.split('\n');

        fetch('/slot_booking/add-cron-job/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
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
                location.reload();
            } else {
                alert('Error adding cron jobs to the server: ' + data.error);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('An error occurred while adding cron jobs to the server.');
        });
    });

// Helper function to delete a booking
function deleteBooking(bookingId) {
    // Ask for confirmation before deleting
    if (confirm(`Are you sure you want to delete the booking with ID: ${bookingId}?`)) {
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
            } else {
                alert('Error deleting booking or cron jobs!');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('An unexpected error occurred while deleting the booking.');
        })
        .finally(() => {
            location.reload();  // Ensure the page reloads regardless of the outcome
        });
    } else {
        console.log('Deletion canceled by the user.');
        location.reload();  // Ensure the page reloads even if the user cancels the deletion
    }
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
        document.getElementById('dateRange').classList.remove('is-invalid');
        document.getElementById('dateRangeError').innerText = '';
        document.getElementById('timeSlotContainer').classList.remove('border', 'border-danger', 'rounded');
        document.getElementById('timeSlotError').innerText = '';
    }
});
