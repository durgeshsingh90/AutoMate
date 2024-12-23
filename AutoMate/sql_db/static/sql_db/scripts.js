const tables = [];
let selectedTables = [];

function showServerFiles(server) {
    document.getElementById('serverFilesView').style.display = 'block';
    document.getElementById('serverTitle').innerText = `Files for ${server}`;
    listTables(server);
}

function listTables(server) {
    fetch(`/sql_db/list_tables/?db_key=${server}`)
        .then(response => response.json())
        .then(data => {
            let resultDiv = document.getElementById('tableButtons');
            if (data.error) {
                resultDiv.innerHTML = `<div style="color: red;">Error: ${data.error}</div>`;
            } else {
                selectedTables = [];
                tables.length = 0;
                tables.push(...data.tables);
                filterTables();
            }
        })
        .catch(error => {
            console.error('Error:', error);
        });
}

function filterTables() {
    let searchInput = document.getElementById('tableSearch').value.toLowerCase();
    let filteredTables = tables.filter(table => table.toLowerCase().includes(searchInput));
    populateTableButtons(filteredTables);
}

function populateTableButtons(tableList) {
    let tableButtonsDiv = document.getElementById('tableButtons');
    tableButtonsDiv.innerHTML = '';
    tableList.forEach(table => {
        let button = document.createElement('button');
        button.textContent = table;
        button.onclick = () => toggleTableSelection(table);
        tableButtonsDiv.appendChild(button);
    });
}

function toggleTableSelection(table) {
    const index = selectedTables.indexOf(table);
    if (index >= 0) {
        selectedTables.splice(index, 1);
    } else {
        selectedTables.push(table);
    }
    updateTableSelection();
}

function updateTableSelection() {
    const tableButtons = document.querySelectorAll('.table-buttons button');
    tableButtons.forEach(button => {
        if (selectedTables.includes(button.textContent)) {
            button.style.backgroundColor = '#cccccc';
        } else {
            button.style.backgroundColor = '#f4f4f4';
        }
    });
}

function downloadSelectedTables() {
    let server = document.getElementById('serverTitle').innerText.replace('Files for ', '');
    if (selectedTables.length === 0) {
        alert('Please select at least one table.');
        return;
    }
    if (!server) {
        alert('Please select a server.');
        return;
    }

    selectedTables.forEach(tableName => {
        fetch(`/sql_db/select_all_from_table/${tableName}/?db_key=${server}`)
            .then(response => response.blob())
            .then(blob => {
                const url = window.URL.createObjectURL(blob);

                // Verify if the filename meets the criteria
                const contentDisposition = response.headers.get('Content-Disposition');
                let filename = '';
                if (contentDisposition && contentDisposition.indexOf('attachment') !== -1) {
                    const matches = /filename="([^']+)"/.exec(contentDisposition);
                    if (matches != null && matches[1]) filename = matches[1];
                }

                if (filename.startsWith(`${server}_`) && filename.endsWith('.log')) {
                    const link = document.createElement('a');
                    link.href = url;
                    link.setAttribute('download', filename);
                    document.body.appendChild(link);
                    link.click();
                    link.parentNode.removeChild(link);
                } else {
                    console.warn('Unwanted file prompt prevented:', filename);
                }
            })
            .catch(error => {
                console.error('Error:', error);
            });
    });
}
