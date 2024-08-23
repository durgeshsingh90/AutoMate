document.addEventListener('DOMContentLoaded', function() {
    var editor = ace.edit("editor");
    editor.setTheme("ace/theme/github");
    editor.session.setMode("ace/mode/yaml");
    editor.setOptions({
        maxLines: 30,
        minLines: 30,
        wrap: true
    });

    var form = document.getElementById('transaction-form');
    var errorContainer = document.getElementById('error-container');
    var dataField = document.getElementById('data');

    function addWarning(message, row) {
        var warningElement = document.createElement("div");
        warningElement.className = "warning-message";
        warningElement.textContent = message;
        errorContainer.appendChild(warningElement);

        editor.session.addMarker(new ace.Range(row, 0, row, 1), "ace_warning-line", "fullLine");
    }

    function addError(message, row) {
        var errorElement = document.createElement("div");
        errorElement.className = "error-message";
        errorElement.textContent = message;
        errorContainer.appendChild(errorElement);

        editor.session.addMarker(new ace.Range(row, 0, row, 1), "ace_error-line", "fullLine");
    }

    form.addEventListener('submit', function(event) {
        var valid = true;
        errorContainer.innerHTML = ''; // Clear previous messages
        editor.session.clearAnnotations();

        var data = editor.getValue();
        try {
            var parsedData = jsyaml.load(data);
        } catch (e) {
            valid = false;
            addError('Invalid YAML format: ' + e.message, e.mark.line);
            // Still allow form submission, so no event.preventDefault()
            return;
        }

        var lengthCriteria = {
            'mti': [4, 4],
            'DE002': [16, 19],
            'DE003': [6, 6],
            'DE004': [1, 12],
            'DE007': [10, 10],
            'DE011': [6, 6],
            'DE012': [6, 6],
            'DE013': [4, 4],
            'DE014': [4, 4],
            'DE018': [4, 4],
            'DE019': [3, 3],
            'DE022': [3, 3],
            'DE023': [3, 3],
            'DE025': [2, 2],
            'DE032': [2, 11],
            'DE035': [37, 37],
            'DE037': [12, 12],
            'DE041': [8, 8],
            'DE042': [15, 15],
            'DE043': [1, 40],
            'DE049': [3, 3],
            'DE055': [1, 255],
            'DE060': {
                '37': [1, 30],
                '53': [3, 3]
            }
        };

        Object.entries(parsedData.data_elements).forEach(([key, value], rowIndex) => {
            if (lengthCriteria.hasOwnProperty(key)) {
                var criteria = lengthCriteria[key];

                if (typeof criteria === 'object' && !Array.isArray(criteria)) {
                    // Nested object validation (e.g., DE060)
                    Object.entries(value).forEach(([subKey, subValue]) => {
                        if (criteria.hasOwnProperty(subKey)) {
                            var subCriteria = criteria[subKey];
                            if (subValue.length < subCriteria[0] || subValue.length > subCriteria[1]) {
                                valid = false;
                                addWarning(`${key}.${subKey} length should be between ${subCriteria[0]} and ${subCriteria[1]} characters.`, rowIndex);
                            }
                        }
                    });
                } else {
                    // Simple value validation
                    if (value.length < criteria[0] || value.length > criteria[1]) {
                        valid = false;
                        addWarning(`${key} length should be between ${criteria[0]} and ${criteria[1]} characters.`, rowIndex);
                    }
                }
            }
        });

        // Update hidden textarea with editor content
        dataField.value = data;
    });
});
