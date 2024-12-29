let tables = [];

function showServerFiles(server) {
    document.getElementById('serverFilesView').style.display = 'block';
    document.getElementById('serverTitle').innerText = `Files for ${server}`;
    listTables(server);
}

function listTables(server) {
    fetch(`/sql_db/list_tables/?db_key=${server}`)
        .then(response => response.json())
        .then(data => {
            let resultDiv = document.getElementById('fileList');
            if (data.error) {
                resultDiv.innerHTML = `<div style="color: red;">Error: ${data.error}</div>`;
            } else {
                tables = data.tables;
                resultDiv.innerHTML = `<pre>${data.tables.join('\n')}</pre>`;
                populateTableSelect(tables);
            }
        })
        .catch(error => {
            console.error('Error:', error);
        });
}

function filterTables() {
    let searchInput = document.getElementById('tableSearch').value.toLowerCase();
    let filteredTables = tables.filter(table => table.toLowerCase().includes(searchInput));
    populateTableSelect(filteredTables);
}

function populateTableSelect(tableList) {
    let tableSelect = document.getElementById('tableSelect');
    tableSelect.innerHTML = `<option value="">Select a table</option>`;
    tableList.forEach(table => {
        let option = document.createElement('option');
        option.value = table;
        option.textContent = table;
        tableSelect.appendChild(option);
    });
}

function selectTable() {
    let tableName = document.getElementById('tableSelect').value;
    let server = document.getElementById('serverTitle').innerText.replace('Files for ', '');
    if (!tableName) {
        alert('Please select a table.');
        return;
    }
    if (!server) {
        alert('Please select a server.');
        return;
    }

    fetch(`/sql_db/select_all_from_table/${tableName}/?db_key=${server}`)
        .then(response => response.blob())
        .then(blob => {
            const url = window.URL.createObjectURL(blob);

            const contentDisposition = response.headers.get('Content-Disposition');
            let filename = '';
            if (contentDisposition && contentDisposition.indexOf('attachment') !== -1) {
                const matches = /filename="([^']+)"*/.exec(contentDisposition);
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
}
