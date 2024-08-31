document.addEventListener("DOMContentLoaded", function () {
    // Load saved data from localStorage on page load
    const savedLogData = localStorage.getItem('splunkLogs');
    if (savedLogData) {
        document.getElementById('splunkLogs').value = savedLogData;
    }

    // Save data to localStorage when input changes
    document.getElementById('splunkLogs').addEventListener('input', function () {
        localStorage.setItem('splunkLogs', this.value);
    });

    // Event listener for text selection
    document.addEventListener('selectionchange', function () {
        const selectedText = window.getSelection().toString();
        const selectedTextLength = selectedText.length;
        document.getElementById('status-bar').textContent = `Selected Text Length: ${selectedTextLength}`;
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
    const logData = document.getElementById('splunkLogs').value.trim(); // Fetch and trim the log data

    if (!logData) {
        document.getElementById('notification').textContent = "Please provide log data to parse.";
        return false; // Return false to indicate no parsing was done
    }

    try {
        console.log("Sending log data:", logData);

        const response = await fetch('/splunkparser/parse_logs/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrftoken
            },
            body: JSON.stringify({ log_data: logData })
        });

        const data = await response.json();

        if (data.status === 'error' || data.status === 'warning') {
            document.getElementById('notification').textContent = `Warning: ${data.message}`;
            document.getElementById('output').textContent = JSON.stringify(data.result, null, 4);
        } else {
            document.getElementById('notification').textContent = '';
            document.getElementById('output').textContent = JSON.stringify(data.result, null, 4);
        }
        return true;
    } catch (error) {
        document.getElementById('notification').textContent = `Error: ${error.message}`;
        return false;
    }
}

async function parseLogsToYAML() {
    const output = document.getElementById('output').textContent.trim();
    if (!output) {
        const jsonParsed = await parseLogsToJSON();
        if (!jsonParsed) {
            return;
        }
    }

    try {
        const jsonData = JSON.parse(document.getElementById('output').textContent);

        // Ensure MTI is always on top
        const sortedJsonData = { MTI: jsonData.MTI, ...jsonData };
        delete sortedJsonData.MTI;

        let yaml = jsyaml.dump(sortedJsonData, {
            quotingType: '"', 
            forceQuotes: true,
            sortKeys: false, 
        });

        yaml = yaml.replace(/"([^"]+)":/g, '$1:');

        document.getElementById('output').textContent = yaml;
        document.getElementById('notification').textContent = "";
    } catch (error) {
        document.getElementById('notification').textContent = `Error: Invalid JSON output. Please parse to JSON first.`;
    }
}

function copyOutput() {
    const output = document.getElementById('output').textContent;
    const copyButton = document.getElementById('copyButton');

    navigator.clipboard.writeText(output).then(() => {
        copyButton.textContent = 'Copied!';
        copyButton.classList.remove('btn-info');
        copyButton.classList.add('btn-success');

        setTimeout(() => {
            copyButton.textContent = 'Copy Output';
            copyButton.classList.remove('btn-success');
            copyButton.classList.add('btn-info');
        }, 1000);
    }).catch(err => {
        document.getElementById('notification').textContent = `Failed to copy: ${err.message}`;
    });
}
