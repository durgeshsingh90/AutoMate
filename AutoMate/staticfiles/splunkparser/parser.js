// Function to get CSRF token from hidden input field
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

const csrftoken = getCookie('csrftoken'); // Get CSRF token from cookies

async function connectAndParse() {
    try {
        const logData = document.getElementById('splunkLogs').value;

        // Make an async request to connect to the database
        const response = await fetch('/splunkparser/connect/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json', // Ensure the request expects JSON
                'X-CSRFToken': csrftoken // Add the CSRF token to the request header
            },
            body: JSON.stringify({ log_data: logData }) // Send log data as request body
        });

        const data = await response.json(); // Attempt to parse JSON response

        if (data.status === 'error' || data.status === 'warning') {
            document.getElementById('notification').textContent = `Warning: ${data.message}`;
            document.getElementById('output').textContent = JSON.stringify(data.result, null, 4);
        } else {
            document.getElementById('notification').textContent = '';
            document.getElementById('output').textContent = JSON.stringify(data.result, null, 4);
        }
    } catch (error) {
        document.getElementById('notification').textContent = `Error: ${error.message}`;
    }
}
