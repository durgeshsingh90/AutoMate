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

        // Update the existing status bar instead of creating a new one
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
    const logData = document.getElementById('splunkLogs').value.trim(); 

    if (!logData) {
        document.getElementById('notification').textContent = "Please provide log data to parse.";
        return false;
    }

    try {
        const response = await fetch('/splunkparser/parse_logs/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrftoken
            },
            body: JSON.stringify({ log_data: logData })
        });

        const data = await response.json();

        document.getElementById('output').textContent = JSON.stringify(data.result, null, 4);

        // Change class to JSON for color coding
        document.getElementById('output').className = 'output-area border p-3 bg-light language-json';
        
        // Highlight syntax
        Prism.highlightElement(document.getElementById('output'));

        return true;
    } catch (error) {
        document.getElementById('notification').textContent = `Error: ${error.message}`;
        return false;
    }
}


async function parseLogsToYAML() {
    // Fetch the current content of the text box
    const logData = document.getElementById('splunkLogs').value.trim();
    
    // Ensure there is input data to parse
    if (!logData) {
        document.getElementById('notification').textContent = "Please provide log data to parse.";
        return;
    }

    try {
        // Parse the logs to JSON first to get the latest data
        const response = await fetch('/splunkparser/parse_logs/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrftoken
            },
            body: JSON.stringify({ log_data: logData })
        });

        const data = await response.json();

        // Check if there's an error in the response
        if (data.status === 'error' || data.status === 'warning') {
            document.getElementById('notification').textContent = `Warning: ${data.message}`;
            document.getElementById('output').textContent = JSON.stringify(data.result, null, 4);
            return;
        }

        const jsonData = data.result;

        // Debugging: Log the JSON data to verify MTI existence
        console.log("Parsed JSON Data:", jsonData);

        // Ensure MTI is on top by creating a new object and preserving the order
        let sortedJsonData = {};

        if (jsonData && jsonData.MTI) {
            // Add MTI first
            sortedJsonData.MTI = jsonData.MTI;
            // Copy the remaining properties except MTI
            Object.keys(jsonData).forEach((key) => {
                if (key !== 'MTI') {
                    sortedJsonData[key] = jsonData[key];
                }
            });
        } else {
            // If MTI does not exist, use the original data
            sortedJsonData = jsonData;
        }

        // Debugging: Log the sorted JSON data to verify MTI is on top
        console.log("Sorted JSON Data for YAML:", sortedJsonData);

        // Convert to YAML
        let yaml = jsyaml.dump(sortedJsonData, {
            quotingType: '"',
            forceQuotes: true,
            sortKeys: false,
        });

        // Remove unnecessary quotes around keys
        yaml = yaml.replace(/"([^"]+)":/g, '$1:');

        // Debugging: Log the final YAML to verify the output
        console.log("Final YAML Output:", yaml);

        // Display YAML output
        document.getElementById('output').textContent = yaml;

        // Change class to YAML for color coding
        document.getElementById('output').className = 'output-area border p-3 bg-light language-yaml';

        // Highlight syntax
        Prism.highlightElement(document.getElementById('output'));

        document.getElementById('notification').textContent = "";

    } catch (error) {
        document.getElementById('notification').textContent = `Error: ${error.message}`;
        console.error("Error parsing to YAML:", error);
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
