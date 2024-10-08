// Get DOM elements
const dropZone = document.getElementById('drop-zone');
const fileInput = document.getElementById('file-input');
const form = document.getElementById('file-upload-form');

// Prevent default behavior for dragover and drop events
dropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    e.stopPropagation();
    dropZone.classList.add('dragover');
});

dropZone.addEventListener('dragleave', (e) => {
    e.preventDefault();
    e.stopPropagation();
    dropZone.classList.remove('dragover');
});

// Handle drop event
dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    e.stopPropagation();
    dropZone.classList.remove('dragover');
    
    // Handle dropped files
    if (e.dataTransfer.files.length > 0) {
        fileInput.files = e.dataTransfer.files;  // Attach the dropped file to the input
        form.submit();  // Automatically submit the form to start conversion
    }
});

// Handle click event to trigger file input
dropZone.addEventListener('click', () => {
    fileInput.click();  // Open file browser on click
});

// Handle manual file input change
fileInput.addEventListener('change', () => {
    form.submit();  // Automatically submit the form when a file is chosen
});
