document.addEventListener("DOMContentLoaded", function() {
    // Load saved data from localStorage on page load
    const savedLogData = localStorage.getItem('splunkLogs');
    if (savedLogData) {
        document.getElementById('splunkLogs').value = savedLogData;
    }

    // Save data to localStorage when input changes
    document.getElementById('splunkLogs').addEventListener('input', function() {
        localStorage.setItem('splunkLogs', this.value);
    });
});

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

const csrftoken = getCookie('csrftoken'); // Get CSRF token from cookies

async function parseLogsToJSON() {
    try {
        const logData = document.getElementById('splunkLogs').value.trim(); // Fetch and trim the log data

        if (!logData) {
            document.getElementById('notification').textContent = "Please provide log data to parse.";
            return;
        }

        // Debug: Log the data before sending it
        console.log("Sending log data:", logData);

        const response = await fetch('/splunkparser/parse_logs/', {  // Make sure this URL matches your Django URL pattern
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrftoken
            },
            body: JSON.stringify({ log_data: logData }) // Send log data as JSON
        });

        const data = await response.json();

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

function parseLogsToYAML() {
    const output = document.getElementById('output').textContent;
    try {
        const yaml = jsyaml.dump(JSON.parse(output)); // Convert JSON to YAML
        document.getElementById('output').textContent = yaml;
    } catch (error) {
        document.getElementById('notification').textContent = `Error: ${error.message}`;
    }
}

function copyOutput() {
    const output = document.getElementById('output').textContent;
    const copyButton = document.getElementById('copyButton');

    navigator.clipboard.writeText(output).then(() => {
        // Change button text and color
        copyButton.textContent = 'Copied!';
        copyButton.classList.remove('btn-info');
        copyButton.classList.add('btn-success');

        // Revert back after 1 second
        setTimeout(() => {
            copyButton.textContent = 'Copy Output';
            copyButton.classList.remove('btn-success');
            copyButton.classList.add('btn-info');
        }, 1000);
    }).catch(err => {
        document.getElementById('notification').textContent = `Failed to copy: ${err.message}`;
    });
}
