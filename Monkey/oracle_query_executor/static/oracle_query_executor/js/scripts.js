
let editor;
let currentPage = 1;
const itemsPerPage = 50;

require.config({ paths: { 'vs': 'https://cdn.jsdelivr.net/npm/monaco-editor@0.28.1/min/vs' }});
require(['vs/editor/editor.main'], function() {
    editor = monaco.editor.create(document.getElementById('editor'), {
        value: '',
        language: 'yaml', // default language is yaml
        theme: 'vs-dark',
        automaticLayout: true
    });

    const savedDbKey = localStorage.getItem("db_key");
    const savedQuerySets = localStorage.getItem("query_sets");
    const savedFormat = localStorage.getItem("format");

    if (savedDbKey) {
        document.getElementById("db_key").value = savedDbKey;
    }
    if (savedQuerySets) {
        editor.setValue(savedQuerySets);
    }
    if (savedFormat) {
        document.getElementById("format_selector").value = savedFormat;
    }

    document.getElementById("format_selector").addEventListener("change", function() {
        const format = this.value;
        setDefaultQuerySets(format);
    });

    document.getElementById("editor").addEventListener("dblclick", function() {
        if (!editor.getValue().trim()) {
            setDefaultQuerySets(document.getElementById("format_selector").value);
        }
    });

    document.getElementById("export-options").addEventListener("change", function() {
        const selectedOption = this.value;
        exportResult(selectedOption);
        this.selectedIndex = 0; // Reset dropdown after selection
    });

    document.getElementById("raw-button").onclick = function() {
        document.getElementById("result").style.display = "block";
        document.getElementById("table-container").style.display = "none";
    };

    document.getElementById("column-button").onclick = function() {
        document.getElementById("result").style.display = "none";
        document.getElementById("table-container").style.display = "block";
    };

    document.getElementById("column-button").onclick();

    document.getElementById("new-tab-button").onclick = function() {
        const result = document.getElementById("result").textContent;
        const tableContent = document.getElementById("table-container").innerHTML;

        const resultWindow = window.open("", "_blank");
        resultWindow.document.open();
        resultWindow.document.write(`
            <html>
            <head>
                <title>Query Result</title>
                <style>
                    .view-buttons {
                        margin-bottom: 10px;
                    }
                    .table-container {
                        overflow-x: auto;
                        margin-top: 20px;
                    }
                    table {
                        width: 100%;
                        border-collapse: collapse;
                        margin-bottom: 20px;
                    }
                    th, td {
                        border: 1px solid #ccc;
                        padding: 8px;
                        text-align: left;
                    }
                    th {
                        background-color: #f4f4f4;
                    }
                    pre {
                        white-space: pre-wrap;
                        word-wrap: break-word;
                    }
                </style>
            </head>
            <body>
                <div class="view-buttons">
                    <button type="button" onclick="toggleView('column')">Column View</button>
                    <button type="button" onclick="toggleView('raw')">Raw JSON View</button>
                </div>
                <h2>Result</h2>
                <pre id="result">${result}</pre>
                <div id="table-container" class="table-container">${tableContent}</div>
                <script>
                    function toggleView(view) {
                        if (view === 'column') {
                            document.getElementById('result').style.display = 'none';
                            document.getElementById('table-container').style.display = 'block';
                        } else {
                            document.getElementById('result').style.display = 'block';
                            document.getElementById('table-container').style.display = 'none';
                        }
                    }
                    toggleView('column');
                </script>
            </body>
            </html>
        `);
        resultWindow.document.close();
    };

    document.getElementById("prev-page").onclick = function() {
        if (currentPage > 1) {
            currentPage--;
            updateQueryHistoryList();
        }
    };

    document.getElementById("next-page").onclick = function() {
        currentPage++;
        updateQueryHistoryList();
    };

    document.getElementById("save-script-button").onclick = showSaveScriptPrompt;

    document.getElementById("query-form").addEventListener("submit", executeQuery);
    document.getElementById("get-count-button").addEventListener("click", getCount);

    // Load saved scripts to the dropdown initially
    loadSavedScripts();
    updateQueryHistoryList();
});

function setDefaultQuerySets(format) {
    if (format === 'yaml') {
        editor.setValue(`query_set_1:
  - select * from oasis77.card_scheme
query_set_2:
  - select * from oasis77.institution`);
    } else if (format === 'json') {
        editor.setValue(`{
    "query_set_1": [
        "select * from oasis77.card_scheme"
    ],
    "query_set_2": [
        "select * from oasis77.institution"
    ]
}`);
    } else {
        editor.setValue("select * from oasis77.card_scheme");
    }
}

function renderTable(data) {
    const tableContainer = document.getElementById("table-container");
    tableContainer.innerHTML = "";

    data.forEach((resultData, index) => {
        if (resultData.error) {
            const errorDiv = document.createElement("div");
            errorDiv.textContent = `Query ${index + 1} Error: ${resultData.error}`;
            tableContainer.appendChild(errorDiv);
            return;
        }

        const tableDiv = document.createElement("div");
        tableDiv.classList.add("table-result");

        const queryTitle = document.createElement("h3");
        queryTitle.textContent = `Query ${index + 1}: ${resultData.query}`;
        tableDiv.appendChild(queryTitle);

        if (!resultData.result || !resultData.result.data || resultData.result.data.length === 0) {
            const noDataDiv = document.createElement("div");
            noDataDiv.textContent = "No data available";
            tableDiv.appendChild(noDataDiv);
        } else {
            const table = document.createElement("table");
            table.classList.add("result-table");

            // Creating table headings
            const thead = document.createElement("thead");
            const headerRow = document.createElement("tr");
            Object.keys(resultData.result.data[0]).forEach(column => {
                const th = document.createElement("th");
                th.textContent = column;
                th.style.position = "sticky"; // Make header sticky
                th.style.top = "0"; // Stick to the top of the container
                headerRow.appendChild(th);
            });
            thead.appendChild(headerRow);
            table.appendChild(thead);

            // Creating table body
            const tbody = document.createElement("tbody");
            resultData.result.data.forEach(row => {
                const tr = document.createElement("tr");
                Object.keys(row).forEach(column => {
                    const td = document.createElement("td");
                    td.textContent = row[column];
                    tr.appendChild(td);
                });
                tbody.appendChild(tr);
            });
            table.appendChild(tbody);

            tableDiv.appendChild(table);
        }

        tableContainer.appendChild(tableDiv);
    });
}

async function executeQuery(event) {
    event.preventDefault();

    const dbKey = document.getElementById("db_key").value;
    localStorage.setItem("db_key", dbKey);

    const format = document.getElementById("format_selector").value;
    const querySetsText = editor.getValue().trim();

    localStorage.setItem("query_sets", querySetsText);
    localStorage.setItem("format", format);

    let querySets;
    try {
        if (format === 'yaml') {
            querySets = jsyaml.load(querySetsText);
        } else if (format === 'json') {
            querySets = JSON.parse(querySetsText);
        } else {
            querySets = { "query": [querySetsText] };
        }
    } catch (error) {
        alert("Invalid " + format.toUpperCase() + " format: " + error.message);
        return;
    }

    const outputTypes = Array.from(document.querySelectorAll('input[name="output_types"]:checked')).map(el => el.value);

    const payload = {
        db_key: dbKey,
        query_sets: Object.values(querySets).map(queries => queries.map(query => query.trim())),
        output_types: outputTypes,
        query_sets_text: querySetsText,
        format: format
    };

    const response = await fetch('/oracle_query_executor/execute_queries/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
    });

    const result = await response.json();

    document.getElementById("result").textContent = JSON.stringify(result, null, 4);
    renderTable(result.results);

    saveQueryHistory(querySetsText, format);
}

async function getCount(event) {
    event.preventDefault();

    const dbKey = document.getElementById("db_key").value;
    const format = document.getElementById("format_selector").value;
    const querySetsText = editor.getValue().trim();

    localStorage.setItem("query_sets", querySetsText);
    localStorage.setItem("format", format);

    let wrappedQuerySets;
    try {
        if (format === 'yaml') {
            const querySets = jsyaml.load(querySetsText);
            wrappedQuerySets = Object.values(querySets).map(queries => queries.map(query => `SELECT COUNT(*) FROM (${query.trim()})`));
        } else if (format === 'json') {
            const querySets = JSON.parse(querySetsText);
            wrappedQuerySets = Object.values(querySets).map(queries => queries.map(query => `SELECT COUNT(*) FROM (${query.trim()})`));
        } else if (format === 'sql') {
            wrappedQuerySets = [[`SELECT COUNT(*) FROM (${querySetsText.trim()})`]];
        }
    } catch (error) {
        alert("Invalid " + format.toUpperCase() + " format: " + error.message);
        return;
    }

    const payload = {
        db_key: dbKey,
        query_sets: wrappedQuerySets,
        query_sets_text: querySetsText,
        format: format
    };

    const response = await fetch('/oracle_query_executor/execute_queries/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
    });

    const result = await response.json();

    document.getElementById("result").textContent = JSON.stringify(result, null, 4);
    renderTable(result.results);
}

function saveQueryHistory(queryText, format) {
    const entry = {
        timestamp: new Date().toISOString(),
        format: format,
        query: queryText
    };

    let history = JSON.parse(localStorage.getItem("query_history") || "[]");

    // limit the history to the last 5000 queries
    if (history.length >= 5000) {
        history = history.slice(1);
    }

    history.push(entry);
    localStorage.setItem("query_history", JSON.stringify(history));
    updateQueryHistoryList();
}

function updateQueryHistoryList() {
    const historyListDiv = document.getElementById("history_list");
    historyListDiv.innerHTML = "";
    
    const history = JSON.parse(localStorage.getItem("query_history") || "[]");
    const startIdx = (currentPage - 1) * itemsPerPage;
    const endIdx = Math.min(startIdx + itemsPerPage, history.length);
    const paginatedHistory = history.slice(startIdx, endIdx);

    paginatedHistory.forEach((entry, index) => {
        const div = document.createElement("div");
        div.classList.add("query-history-item");
        div.innerHTML = `
            <div>
                <span class="query-sequence">Query ${startIdx + index + 1}</span>
                <span class="timestamp">${new Date(entry.timestamp).toLocaleString()}</span>
            </div>
            <pre>${entry.query.slice(0, 100)}...</pre>
            <button class="add-button">Add</button>
        `;

        const addButton = div.querySelector(".add-button");
        addButton.onclick = () => {
            editor.setValue(entry.query);
            document.getElementById("format_selector").value = entry.format;
            localStorage.setItem("query_sets", entry.query);
            localStorage.setItem("format", entry.format);
        };
        historyListDiv.appendChild(div);
    });

    document.getElementById("prev-page").disabled = startIdx === 0;
    document.getElementById("next-page").disabled = endIdx >= history.length;
}

function exportResult(format) {
    const resultData = JSON.parse(document.getElementById('result').textContent);
    if (!resultData || !resultData.results) {
        alert('No results to export.');
        return;
    }

    const files = [];
    resultData.results.forEach((res, idx) => {
        const tableName = res.query.split()[3].split('.')[1];
        let fileContent;
        if (format === 'json') {
            fileContent = JSON.stringify(res.result.data, null, 4);
        } else if (format === 'sql') {
            fileContent = res.result.insert_statements.join('\n');
        } else {
            alert('Unsupported export format.');
            return;
        }
        const blob = new Blob([fileContent], { type: 'text/plain;charset=utf-8;' });
        files.push({ name: `${tableName}_${idx}.${format}`, blob });
    });

    if (files.length > 1 && window.JSZip) {
        const zip = new JSZip();
        files.forEach(file => {
            zip.file(file.name, file.blob);
        });
        zip.generateAsync({ type: 'blob' }).then(content => {
            const link = document.createElement('a');
            link.href = URL.createObjectURL(content);
            link.download = 'results.zip';
            link.click();
        });
    } else {
        files.forEach(file => {
            const link = document.createElement('a');
            link.href = URL.createObjectURL(file.blob);
            link.download = file.name;
            link.click();
        });
    }
}

function showSaveScriptPrompt() {
    const name = prompt("Enter script name:");
    if (name !== null && name.trim() !== "") {
        const description = prompt("Enter script description (Optional):");
        saveScript(name.trim(), description ? description.trim() : "");
    }
}

function saveScript(name, description) {
    const content = editor.getValue();
    const format = document.getElementById("format_selector").value;
  
    const payload = {
        name: name,
        description: description,
        content: content,
        format: format
    };

    fetch('/oracle_query_executor/save_script/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
    })
    .then(response => response.json())
    .then(data => {
        alert("Script saved successfully.");
        loadSavedScripts();
    })
    .catch(error => {
        console.error("Error saving script:", error);
        alert("Error saving script.");
    });
}

function loadSavedScripts() {
    fetch('/oracle_query_executor/load_scripts/')
    .then(response => response.json())
    .then(data => {
        const loadScriptDropdown = document.getElementById("load-script-dropdown");
        loadScriptDropdown.innerHTML = `<option value="" disabled selected>Load Script</option>`;

        data.forEach(script => {
            const option = document.createElement("option");
            option.value = script.name;
            option.textContent = script.name;
            option.dataset.description = script.description;
            option.dataset.content = script.content;
            option.dataset.format = script.format;
            loadScriptDropdown.appendChild(option);
        });

        loadScriptDropdown.onchange = function() {
            const selectedOption = loadScriptDropdown.selectedOptions[0];
            editor.setValue(selectedOption.dataset.content);
            document.getElementById("format_selector").value = selectedOption.dataset.format;
            localStorage.setItem("query_sets", selectedOption.dataset.content);
            localStorage.setItem("format", selectedOption.dataset.format);
        };
    })
    .catch(error => {
        console.error("Error loading scripts:", error);
        alert("Error loading scripts.");
    });
}
