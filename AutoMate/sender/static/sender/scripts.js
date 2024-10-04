let currentFile = '';

// Function to load all JSON files dynamically (including folder structure)
function loadJsonFiles() {
    fetch('/sender/get-json-files/')
    .then(response => response.json())
    .then(folderStructure => {
        const fileListDiv = document.getElementById('fileList');
        fileListDiv.innerHTML = ''; // Clear the list

        // Utility function to create valid IDs from folder and file names
        function sanitizeId(name) {
            // Replace non-alphanumeric characters with underscores
            let sanitized = name.replace(/[^a-zA-Z0-9-_]/g, '_');

            // If the name starts with a number, prepend an underscore to make it a valid HTML ID
            if (/^\d/.test(sanitized)) {
                sanitized = '_' + sanitized;
            }

            return sanitized;
        }

        // Recursive function to create folder tree structure
// Recursive function to create folder tree structure
// Recursive function to create folder tree structure
function createFolderTree(folder, parentElement, parentId, currentPath = '', level = 0) {
    Object.keys(folder).forEach((key) => {
        const sanitizedId = sanitizeId(parentId + key);  // Valid HTML ID
        const newPath = currentPath ? `${currentPath}/${key}` : key;  // Keep the folder structure for file loading

        const indent = '&nbsp;'.repeat(level * 4);

        if (folder[key] === null) {
            // It's a file, create a draggable file link with indentation
            const listItem = document.createElement('div');
            listItem.className = 'list-group-item';
            listItem.innerHTML = `${indent}📄 ${key}`;
            makeFileDraggable(listItem, newPath);  // Make file draggable
            parentElement.appendChild(listItem);
        } else {
            // It's a folder, create a droppable folder with indentation
            const folderItem = document.createElement('div');
            folderItem.className = 'folder-item';
            folderItem.innerHTML = `
                <div data-bs-toggle="collapse" href="#${sanitizedId}" style="cursor: pointer;">
                    ${indent}📁 <strong>${key}</strong>
                </div>
                <div id="${sanitizedId}" class="collapse"></div>
            `;
            makeFolderDroppable(folderItem, newPath);  // Make folder droppable
            parentElement.appendChild(folderItem);

            // Recursively create the folder structure
            createFolderTree(folder[key], folderItem.querySelector(`#${sanitizedId}`), sanitizedId + '-', newPath, level + 1);
        }
    });
}



        createFolderTree(folderStructure, fileListDiv, '');
    })
    .catch(error => {
        alert('Error loading files: ' + error.message);
    });
}

// Load JSON for editing
// Load JSON for editing
function loadFile(filename, fullPath) {
    // Construct the file path from the actual folder structure, without sanitizing
    const filePath = `/static/sender/testcases/${fullPath}`;
    console.log('Fetching file from:', filePath);  // Log the file path to debug

    fetch(filePath)
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();  // Expect the response to be JSON
    })
    .then(content => {
        currentFile = filename;
        const editor = document.getElementById('jsonEditor');
        editor.value = JSON.stringify(content, null, 2); // Format JSON for easy editing
        editor.disabled = false;
        document.getElementById('saveBtn').disabled = false; // Enable save button
    })
    .catch(error => {
        console.error('Error loading file:', error);  // Log the error for debugging
        alert('Error loading file: ' + error.message);
    });
}



// Save edited JSON file back to the server
document.getElementById('saveBtn').addEventListener('click', function() {
    const editor = document.getElementById('jsonEditor');
    let updatedContent;

    try {
        updatedContent = JSON.parse(editor.value); // Validate JSON format
    } catch (error) {
        alert('Invalid JSON format: ' + error.message);
        return;
    }

    // Send the updated JSON back to the server
    fetch(`/sender/save-json/${currentFile}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken'),  // Django's CSRF protection
        },
        body: JSON.stringify(updatedContent)
    })
    .then(response => response.json())
    .then(data => {
        alert(data.message);
    })
    .catch(error => {
        alert('Error saving file: ' + error.message);
    });
});

// CSRF token function (for Django)
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '='))
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        }
    }
    return cookieValue;
}

// Automatically load JSON files when the page loads
window.onload = function() {
    loadJsonFiles();
};

// Handle new folder creation
document.getElementById('newFolderBtn').addEventListener('click', function() {
    const folderName = prompt('Enter new folder name:');
    if (folderName) {
        // Send the new folder name to the back-end to create the folder
        fetch('/sender/create-folder/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken'),  // CSRF token for Django
            },
            body: JSON.stringify({ folderName })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('Folder created successfully!');
                loadJsonFiles();  // Reload the file explorer to show the new folder
            } else {
                alert('Error creating folder: ' + data.message);
            }
        })
        .catch(error => {
            alert('Error: ' + error.message);
        });
    }
});

// Add draggable attribute to files and handle drag events
function makeFileDraggable(fileElement, filePath) {
    fileElement.setAttribute('draggable', true);
    fileElement.addEventListener('dragstart', (event) => {
        event.dataTransfer.setData('filePath', filePath);  // Store the file path in the drag event
    });
}

// Make folders droppable to accept files
function makeFolderDroppable(folderElement, folderPath) {
    folderElement.addEventListener('dragover', (event) => {
        event.preventDefault();  // Allow dropping
    });

    folderElement.addEventListener('drop', (event) => {
        event.preventDefault();
        const draggedFilePath = event.dataTransfer.getData('filePath');  // Get the dragged file path
        if (draggedFilePath) {
            moveFile(draggedFilePath, folderPath);  // Move the file to the new folder
        }
    });
}

// Function to move the file to a new folder
function moveFile(filePath, targetFolderPath) {
    fetch('/sender/move-file/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken'),
        },
        body: JSON.stringify({ filePath, targetFolderPath })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('File moved successfully!');
            loadJsonFiles();  // Reload the file explorer
        } else {
            alert('Error moving file: ' + data.message);
        }
    })
    .catch(error => {
        alert('Error: ' + error.message);
    });
}
