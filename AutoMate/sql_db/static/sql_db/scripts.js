function updateTables() {
    $.ajax({
        url: updateTableNamesUrl, // Pass URL from template
        type: 'GET',
        success: function(response) {
            var tableNames = response.table_names;
            var fetchedContainer = document.getElementById('fetched-tables-list');
            var unfetchedContainer = document.getElementById('unfetched-tables-list');
            fetchedContainer.innerHTML = '';
            unfetchedContainer.innerHTML = '';
            tableNames.forEach(function(tableName) {
                var item = document.createElement('button');
                item.type = 'button';
                item.className = 'btn btn-secondary btn-table';
                item.textContent = tableName;
                if (fetchedContainer.querySelector(`button:contains('${tableName}')`)) {
                    item.setAttribute('onclick', `showTableData('${tableName}')`);
                    item.setAttribute('oncontextmenu', `deleteTableData(event, '${tableName}')`);
                    fetchedContainer.appendChild(item);
                } else {
                    item.setAttribute('ondblclick', `getAndFetchTableData('${tableName}')`);
                    unfetchedContainer.appendChild(item);
                }
            });
        },
        error: function() {
            alert("An error occurred while updating table names.");
        }
    });
}

function showTableData(tableName) {
    $.ajax({
        url: fetchTableDataUrl.replace('TABLE_NAME_PLACEHOLDER', tableName), // Pass URL from template
        type: 'GET',
        success: function(response) {
            var dataContainer = document.getElementById('table-data');
            dataContainer.innerHTML = `<h3>Data for ${response.table_name}</h3>`;
            var table = document.createElement('table');
            table.className = 'table table-striped';
            var thead = document.createElement('thead');
            var headersRow = document.createElement('tr');
            Object.keys(response.data[0]).forEach(function(header) {
                var th = document.createElement('th');
                th.textContent = header;
                headersRow.appendChild(th);
            });
            thead.appendChild(headersRow);
            table.appendChild(thead);
            var tbody = document.createElement('tbody');
            response.data.forEach(function(row) {
                var tr = document.createElement('tr');
                Object.values(row).forEach(function(cell) {
                    var td = document.createElement('td');
                    td.textContent = cell;
                    tr.appendChild(td);
                });
                tbody.appendChild(tr);
            });
            table.appendChild(tbody);
            dataContainer.appendChild(table);
        },
        error: function() {
            alert("An error occurred while loading table data.");
        }
    });
}

function getAndFetchTableData(tableName) {
    if (confirm(`Do you want to fetch data for table ${tableName} and save it?`)) {
        $.ajax({
            url: fetchTableDataUrl.replace('TABLE_NAME_PLACEHOLDER', tableName), // Pass URL from template
            type: 'GET',
            success: function(response) {
                alert(`Data for table ${response.table_name} fetched and saved successfully.`);
                location.reload(); // Reload the page after fetching data
            },
            error: function() {
                alert("An error occurred while fetching and saving table data.");
            }
        });
    }
}


function deleteTableData(event, tableName) {
    event.preventDefault();
    if (confirm(`Do you want to delete the data for table ${tableName}?`)) {
        $.ajax({
            url: deleteTableDataUrl.replace('TABLE_NAME_PLACEHOLDER', tableName), // Pass URL from template
            type: 'GET',
            success: function(response) {
                alert(`Data for table ${response.table_name} deleted successfully.`);
                location.reload(); // Reload the page after deleting data
            },
            error: function() {
                alert("An error occurred while deleting table data.");
            }
        });
    }
}
