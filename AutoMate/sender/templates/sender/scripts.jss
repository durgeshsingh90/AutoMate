var editor = ace.edit("editor");
editor.setTheme("ace/theme/monokai");
editor.session.setMode("ace/mode/yaml");
editor.setShowPrintMargin(false);
editor.setShowInvisibles(false);
editor.setDisplayIndentGuides(false);
editor.setOptions({
    enableBasicAutocompletion: true,
    enableLiveAutocompletion: true,
    enableSnippets: true,
    showLineNumbers: true,
    tabSize: 2
});

var lengthRequirements = {
    'mti': { min: 4, max: 4 },
    'BM002': { min: 16, max: 16 },
    'BM003': { min: 6, max: 6 },
    'BM004': { min: 1, max: 12 },
    'BM007': { min: 10, max: 10 },
    'BM011': { min: 6, max: 6 },
    'BM012': { min: 6, max: 6 },
    'BM013': { min: 4, max: 4 },
    'BM014': { min: 4, max: 4 },
    'BM018': { min: 4, max: 4 },
    'BM019': { min: 3, max: 3 },
    'BM022': { min: 3, max: 3 },
    'BM023': { min: 3, max: 3 },
    'BM025': { min: 2, max: 2 },
    'BM032': { min: 6, max: 6 },
    'BM035': { min: 37, max: 37 },
    'BM037': { min: 12, max: 12 },
    'BM041': { min: 8, max: 8 },
    'BM042': { min: 15, max: 15 },
    'BM043': { min: 1, max: 40 },
    'BM049': { min: 3, max: 3 },
    'BM055': { min: 1, max: 100 },
    'BM060': { // Custom validation for BM060 subfields
        subfields: {
            '37': { min: 29, max: 29 },
            '53': { min: 3, max: 3 }
        }
    }
};

function updateStatusBar() {
    var lengthInfo = document.getElementById('lengthInfo');
    var linesInfo = document.getElementById('linesInfo');
    var lnColInfo = document.getElementById('lnColInfo');
    var selInfo = document.getElementById('selInfo');
    var posInfo = document.getElementById('posInfo');

    var session = editor.getSession();
    var content = editor.getValue();
    var cursor = editor.getCursorPosition();
    var selectionRange = editor.getSelectionRange();

    lengthInfo.textContent = `Length: ${content.length}`;
    linesInfo.textContent = `Lines: ${session.getLength()}`;
    lnColInfo.textContent = `Ln: ${cursor.row + 1}, Col: ${cursor.column + 1}`;
    selInfo.textContent = `Sel: ${Math.abs(selectionRange.end.row - selectionRange.start.row) + Math.abs(selectionRange.end.column - selectionRange.start.column)}`;
    posInfo.textContent = `Pos: ${editor.getSelection().getCursor().column}`;
}

document.getElementById('wordWrapToggle').addEventListener('change', function(event) {
    var isChecked = event.target.checked;
    editor.getSession().setUseWrapMode(isChecked);
});

document.getElementById('prettyButton').addEventListener('click', function() {
    var content = editor.getValue();
    try {
        if (content.trim().startsWith('{') || content.trim().startsWith('[')) {
            // Beautify JSON
            var beautified = js_beautify(content, { indent_size: 2 });
            editor.setValue(beautified, -1);
        } else {
            // Beautify YAML
            var yamlData = jsyaml.load(content);
            var beautifiedYaml = jsyaml.dump(yamlData, { indent: 2 });
            editor.setValue(beautifiedYaml, -1);
        }
    } catch (e) {
        console.error('Error beautifying content:', e.message);
    }
});

function findLineNumber(content, key) {
    var lines = content.split('\n');
    for (var i = 0; i < lines.length; i++) {
        var trimmedLine = lines[i].trim();
        if (trimmedLine.startsWith(key + ':') || trimmedLine.startsWith('"' + key + '":') || trimmedLine.startsWith("'" + key + "':")) {
            return i;
        }
    }
    return -1;
}

function validateContent(content, data) {
    var annotations = [];
    for (var key in data) {
        if (data.hasOwnProperty(key) && lengthRequirements[key]) {
            if (key === 'BM060' && typeof data[key] === 'object') {
                // Validate BM060 subfields
                for (var subKey in data[key]) {
                    if (data[key].hasOwnProperty(subKey) && lengthRequirements[key].subfields[subKey]) {
                        var value = data[key][subKey];
                        var { min, max } = lengthRequirements[key].subfields[subKey];
                        if (value.length < min || value.length > max) {
                            var lineNumber = findLineNumber(content, subKey);
                            annotations.push({
                                row: lineNumber,
                                column: 0,
                                text: `Warning: The value of BM060 subfield ${subKey} should be between ${min} and ${max} characters long.`,
                                type: "warning"
                            });
                        }
                    }
                }
            } else {
                var value = data[key];
                var { min, max } = lengthRequirements[key];
                if (value.length < min || value.length > max) {
                    var lineNumber = findLineNumber(content, key);
                    annotations.push({
                        row: lineNumber,
                        column: 0,
                        text: `Warning: The value of ${key} should be between ${min} and ${max} characters long.`,
                        type: "warning"
                    });
                }
            }
        }
    }
    return annotations;
}

function debounce(func, wait) {
    var timeout;
    return function() {
        var context = this, args = arguments;
        clearTimeout(timeout);
        timeout = setTimeout(function() {
            func.apply(context, args);
        }, wait);
    };
}

var validateEditorContent = debounce(function() {
    var content = editor.getValue();
    var annotations = [];
    try {
        if (content.trim()) {
            if (content.trim().startsWith('{') || content.trim().startsWith('[')) {
                var jsonData = JSON.parse(content);
                editor.getSession().setMode("ace/mode/json");
                annotations = validateContent(content, jsonData);
            } else {
                var yamlData = jsyaml.load(content);
                editor.getSession().setMode("ace/mode/yaml");
                annotations = validateContent(content, yamlData);
            }
        }
    } catch (e) {
        var errorMessage = e.message;
        var lineNumberMatch = errorMessage.match(/at line (\d+)/i);
        if (lineNumberMatch) {
            var lineNumber = parseInt(lineNumberMatch[1]) - 1;
            annotations.push({
                row: lineNumber,
                column: 0,
                text: errorMessage,
                type: "error"
            });
        } else {
            annotations.push({
                row: 0,
                column: 0,
                text: errorMessage,
                type: "error"
            });
        }
    }
    // Apply annotations after a delay to ensure stability
    setTimeout(function() {
        editor.getSession().setAnnotations(annotations);
    }, 0);
    updateStatusBar();
    saveEditorContent();
}, 500);

editor.getSession().on('change', validateEditorContent);

editor.selection.on('changeCursor', updateStatusBar);
editor.selection.on('changeSelection', updateStatusBar);

// Initial status bar update
updateStatusBar();

// File management
const fileStructure = JSON.parse(localStorage.getItem('fileStructure')) || [];

function saveFileStructure() {
    localStorage.setItem('fileStructure', JSON.stringify(fileStructure));
}

function saveEditorContent() {
    localStorage.setItem('editorContent', editor.getValue());
}

function loadEditorContent() {
    const content = localStorage.getItem('editorContent');
    if (content) {
        editor.setValue(content, -1);
    }
}

function refreshExplorer() {
    const explorer = document.getElementById('explorer');
    explorer.innerHTML = '';
    fileStructure.forEach((group, groupIndex) => {
        const groupItem = document.createElement('div');
        groupItem.className = 'group-item';
        const groupTitle = document.createElement('h6');
        groupTitle.innerHTML = `
            <span>${group.name}</span>
            <span>
                <i class="fas fa-chevron-down toggle-button"></i>
                <i class="fas fa-trash-alt delete-group ml-2"></i>
            </span>
        `;
        groupTitle.querySelector('.toggle-button').addEventListener('click', function() {
            const files = groupItem.querySelectorAll('.file-item');
            files.forEach(file => file.classList.toggle('hidden'));
            this.classList.toggle('fa-chevron-down');
            this.classList.toggle('fa-chevron-right');
        });
        groupTitle.querySelector('.delete-group').addEventListener('click', function() {
            if (confirm('Are you sure you want to delete this group?')) {
                fileStructure.splice(groupIndex, 1);
                saveFileStructure();
                refreshExplorer();
            }
        });
        groupItem.appendChild(groupTitle);

        group.files.forEach((file, fileIndex) => {
            const fileItem = document.createElement('div');
            fileItem.className = 'file-item';
            fileItem.innerHTML = `
                <span>${file.name}</span>
                <i class="fas fa-trash-alt delete-file"></i>
            `;
            fileItem.querySelector('.delete-file').addEventListener('click', function() {
                if (confirm('Are you sure you want to delete this file?')) {
                    group.files.splice(fileIndex, 1);
                    saveFileStructure();
                    refreshExplorer();
                }
            });
            fileItem.dataset.groupIndex = groupIndex;
            fileItem.dataset.fileIndex = fileIndex;
            fileItem.addEventListener('click', () => {
                document.querySelectorAll('.file-item').forEach(item => item.classList.remove('active'));
                fileItem.classList.add('active');
                editor.setValue(file.content, -1);
                saveEditorContent();
            });
            groupItem.appendChild(fileItem);
        });

        explorer.appendChild(groupItem);
    });
}

document.getElementById('saveButton').addEventListener('click', function() {
    const content = editor.getValue();
    const groupName = document.getElementById('groupName').value.trim();
    const testCaseName = document.getElementById('testCaseName').value.trim();
    if (groupName && testCaseName) {
        let group = fileStructure.find(g => g.name === groupName);
        if (!group) {
            group = { name: groupName, files: [] };
            fileStructure.push(group);
        }
        const file = { name: testCaseName, content: content };
        group.files.push(file);
        saveFileStructure();
        refreshExplorer();
    } else {
        alert('Please enter both group name and test case name.');
    }
});

document.getElementById('createGroupButton').addEventListener('click', function() {
    const groupName = document.getElementById('groupName').value.trim();
    if (groupName) {
        let group = fileStructure.find(g => g.name === groupName);
        if (!group) {
            fileStructure.push({ name: groupName, files: [] });
            saveFileStructure();
            refreshExplorer();
        } else {
            alert('Group already exists.');
        }
    } else {
        alert('Please enter a group name.');
    }
});

document.getElementById('groupByBM032Button').addEventListener('click', function() {
    const bm032Groups = {};

    fileStructure.forEach(group => {
        group.files.forEach(file => {
            const content = file.content;
            let parsedContent;
            try {
                parsedContent = content.trim().startsWith('{') ? JSON.parse(content) : jsyaml.load(content);
            } catch (e) {
                return;
            }
            const bm032Value = parsedContent.BM032;
            if (bm032Value) {
                if (!bm032Groups[bm032Value]) {
                    bm032Groups[bm032Value] = [];
                }
                bm032Groups[bm032Value].push({ name: file.name, content: file.content });
            }
        });
    });

    fileStructure.length = 0;
    for (const bm032Value in bm032Groups) {
        fileStructure.push({ name: `BM032: ${bm032Value}`, files: bm032Groups[bm032Value] });
    }

    saveFileStructure();
    refreshExplorer();
});

document.getElementById('importButton').addEventListener('change', function(event) {
    const file = event.target.files[0];
    if (file) {
        const reader = new FileReader();
        reader.onload = function(e) {
            const content = e.target.result;
            const groupName = document.getElementById('groupName').value.trim() || file.name.split('.')[0];
            const testCaseName = document.getElementById('testCaseName').value.trim() || file.name;
            if (groupName && testCaseName) {
                let group = fileStructure.find(g => g.name === groupName);
                if (!group) {
                    group = { name: groupName, files: [] };
                    fileStructure.push(group);
                }
                const importedFile = { name: testCaseName, content: content };
                group.files.push(importedFile);
                saveFileStructure();
                refreshExplorer();
            } else {
                alert('Please enter both group name and test case name.');
            }
        };
        reader.readAsText(file);
    }
});

document.getElementById('exportButton').addEventListener('click', function() {
    const content = editor.getValue();
    const fileName = document.getElementById('testCaseName').value.trim() || 'test_case_export.json';
    if (fileName) {
        const blob = new Blob([content], { type: "application/json;charset=utf-8" });
        const link = document.createElement("a");
        link.href = URL.createObjectURL(blob);
        link.download = fileName;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }
});

document.getElementById('saveToFileButton').addEventListener('click', function() {
    const blob = new Blob([JSON.stringify(fileStructure)], { type: "application/json;charset=utf-8" });
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = "test_cases.json";
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
});

document.getElementById('loadFromFileButton').addEventListener('click', function() {
    document.getElementById('loadFileInput').click();
});

document.getElementById('loadFileInput').addEventListener('change', function(event) {
    const file = event.target.files[0];
    if (file) {
        const reader = new FileReader();
        reader.onload = function(e) {
            const content = e.target.result;
            try {
                const loadedFileStructure = JSON.parse(content);
                fileStructure.length = 0;
                Array.prototype.push.apply(fileStructure, loadedFileStructure);
                saveFileStructure();
                refreshExplorer();
            } catch (err) {
                alert('Error loading file: ' + err.message);
            }
        };
        reader.readAsText(file);
    }
});

// Save with Ctrl + S
document.addEventListener('keydown', function(event) {
    if ((event.ctrlKey || event.metaKey) && event.key === 's') {
        event.preventDefault();
        document.getElementById('saveButton').click();
    }
});

document.getElementById('collapseAllButton').addEventListener('click', function() {
    document.querySelectorAll('.group-item .file-item').forEach(file => file.classList.add('hidden'));
    document.querySelectorAll('.toggle-button').forEach(button => {
        button.classList.remove('fa-chevron-down');
        button.classList.add('fa-chevron-right');
    });
});

document.getElementById('expandAllButton').addEventListener('click', function() {
    document.querySelectorAll('.group-item .file-item').forEach(file => file.classList.remove('hidden'));
    document.querySelectorAll('.toggle-button').forEach(button => {
        button.classList.remove('fa-chevron-right');
        button.classList.add('fa-chevron-down');
    });
});

// Load initial data
loadEditorContent();
refreshExplorer();
