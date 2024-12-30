
document.addEventListener('DOMContentLoaded', () => {
    loadDbConnections();
    document.getElementById('search-bar').addEventListener('input', filterTableList);
});

async function loadDbConnections() {
    const response = await fetch('/sql_db/get_db_connections/');
    const dbConnections = await response.json();
    const dbSelector = document.getElementById('db-selector');
    
    dbConnections.forEach(dbConn => {
        const option = document.createElement('option');
        option.value = dbConn;
        option.textContent = dbConn;
        dbSelector.appendChild(option);
    });
}

async function loadTableList() {
    const dbKey = document.getElementById('db-selector').value;
    if (!dbKey) return;

    const response = await fetch(`/sql_db/list_tables/?db_key=${dbKey}`);
    const data = await response.json();

    if (data.error) {
        alert(data.error);
        return;
    }

    renderTableList(data.tables);
}

async function refreshTableList() {
    const dbKey = document.getElementById('db-selector').value;
    if (!dbKey) return;

    const loadingIcon = document.querySelector('.loading-icon');
    const refreshIcon = document.querySelector('.refresh-icon');

    loadingIcon.classList.remove('hidden');
    refreshIcon.classList.add('hidden');

    try {
        const response = await fetch(`/sql_db/refresh_list_tables/?db_key=${dbKey}`);
        const data = await response.json();

        if (data.error) {
            alert(data.error);
            return;
        }

        renderTableList(data.tables); // Re-render table list
        alert('Table list refreshed!');
    } catch (error) {
        console.error('Error refreshing table list:', error);
        alert('Failed to refresh table list. Check the console for details.');
    } finally {
        loadingIcon.classList.add('hidden');
        refreshIcon.classList.remove('hidden');
    }
}

function renderTableList(tables) {
    const explorerList = document.getElementById('explorer-list');
    explorerList.innerHTML = '';

    tables.forEach(tableName => {
        const li = createTableElement(tableName);
        explorerList.appendChild(li);
    });
}

function createTableElement(tableName) {
    const li = document.createElement('li');
    li.className = 'folder-icon';

    const container = document.createElement('div');
    container.style.display = 'flex';
    container.style.alignItems = 'center'; // Align items vertically
    container.style.justifyContent = 'space-between'; // Space between name and refresh icon
    container.style.gap = '8px'; // Optional: Add some spacing between items

    const nameContainer = document.createElement('div');
    nameContainer.style.display = 'flex';
    nameContainer.style.alignItems = 'center'; // Align icon and text vertically
    nameContainer.style.gap = '8px'; // Space between icon and name

    const folderIcon = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    folderIcon.setAttribute("width", "16");
    folderIcon.setAttribute("height", "16");
    folderIcon.setAttribute("fill", "currentColor");
    folderIcon.setAttribute("class", "bi bi-folder");
    folderIcon.setAttribute("viewBox", "0 0 16 16");
    folderIcon.innerHTML = `
        <path d="M.54 3.87.5 3a2 2 0 0 1 2-2h3.672a2 2 0 0 1 1.414.586l.828.828A2 2 0 0 0 9.828 3h3.982a2 2 0 0 1 1.992 2.181l-.637 7A2 2 0 0 1 13.174 14H2.826a2 2 0 0 1-1.991-1.819l-.637-7a2 2 0 0 1 .342-1.31zM2.19 4a1 1 0 0 0-.996 1.09l.637 7a1 1 0 0 0 .995.91h10.348a1 1 0 0 0 .995-.91l.637-7A1 1 0 0 0 13.81 4zm4.69-1.707A1 1 0 0 0 6.172 2H2.5a1 1 0 0 0-1 .981l.006.139q.323-.119.684-.12h5.396z"/>
    `;

    const nameSpan = document.createElement('span');
    nameSpan.textContent = tableName;

    nameContainer.appendChild(folderIcon);
    nameContainer.appendChild(nameSpan);

    const refreshIcon = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    refreshIcon.setAttribute("width", "16");
    refreshIcon.setAttribute("height", "16");
    refreshIcon.setAttribute("fill", "currentColor");
    refreshIcon.setAttribute("class", "bi bi-arrow-clockwise refresh-icon");
    refreshIcon.setAttribute("viewBox", "0 0 16 16");
    refreshIcon.innerHTML = `
        <path fill-rule="evenodd" d="M8 3a5 5 0 1 0 4.546 2.914.5.5 0 0 1 .908-.417A6 6 0 1 1 8 2z"/>
        <path d="M8 4.466V.534a.25.25 0 0 1 .41-.192l2.36 1.966c.12.1.12.284 0 .384L8.41 4.658A.25.25 0 0 1 8 4.466"/>
    `;
    refreshIcon.style.cursor = 'pointer';

    const loadingIcon = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    loadingIcon.setAttribute("width", "16");
    loadingIcon.setAttribute("height", "16");
    loadingIcon.setAttribute("fill", "currentColor");
    loadingIcon.setAttribute("class", "bi bi-database-down loading-icon hidden");
    loadingIcon.setAttribute("viewBox", "0 0 16 16");
    loadingIcon.innerHTML = `
        <path d="M12.5 9a3.5 3.5 0 1 1 0 7 3.5 3.5 0 0 1 0-7m.354 5.854 1.5-1.5a.5.5 0 0 0-.708-.708l-.646.647V10.5a.5.5 0 0 0-1 0v2.793l-.646-.647a.5.5 0 0 0-.708.708l1.5 1.5a.5.5 0 0 0 .708 0"/>
        <path d="M12.096 6.223A5 5 0 0 0 13 5.698V7c0 .289-.213.654-.753 1.007a4.5 4.5 0 0 1 1.753.25V4c0-1.007-.875-1.755-1.904-2.223C11.022 1.289 9.573 1 8 1s-3.022.289-4.096.777C2.875 2.245 2 2.993 2 4v9c0 1.007.875 1.755 1.904 2.223C4.978 15.71 6.427 16
    `;

    refreshIcon.addEventListener("click", async (event) => {
        event.stopPropagation();

        refreshIcon.classList.add('hidden');
        loadingIcon.classList.remove('hidden');

        try {
            await refreshTableData(tableName);
        } finally {
            refreshIcon.classList.remove('hidden');
            loadingIcon.classList.add('hidden');
        }
    });

    container.appendChild(nameContainer);
    container.appendChild(refreshIcon);
    container.appendChild(loadingIcon);

    li.appendChild(container);

    li.addEventListener('click', () => loadTableFiles(tableName, li));

    return li;
}

async function refreshTableData(tableName) {
    const dbKey = document.getElementById('db-selector').value;
    if (!dbKey) return;

    try {
        const response = await fetch(`/sql_db/refresh_select_all_from_table/${tableName}/?db_key=${dbKey}`);
        const data = await response.json();

        if (data.error) {
            alert(data.error);
            return;
        }

        alert(data.message);
        loadTableFiles(tableName);
    } catch (error) {
        console.error('Error refreshing table data:', error);
        alert('Failed to refresh table data. Check the console for details.');
    }
}

async function loadTableFiles(tableName, tableElement, forceRefresh = false) {
    const existingFileList = tableElement.querySelector('.file-list');
    if (existingFileList && !forceRefresh) {
        existingFileList.classList.toggle('hidden');
        return;
    }

    const dbKey = document.getElementById('db-selector').value;
    if (!dbKey) return;

    const response = await fetch(`/sql_db/select_all_from_table/${tableName}/?db_key=${dbKey}`);
    const data = await response.json();

    if (data.error) {
        alert(data.error);
        return;
    }

    if (existingFileList) {
        tableElement.removeChild(existingFileList);
    }

    const fileList = document.createElement('ul');
    fileList.className = 'file-list';

    if (data.files && data.files.length > 0) {
        data.files.forEach(fileName => {
            const fileItem = document.createElement('li');
            fileItem.className = 'file-icon';

            const fileIcon = document.createElementNS("http://www.w3.org/2000/svg", "svg");
            fileIcon.setAttribute("width", "16");
            fileIcon.setAttribute("height", "16");
            fileIcon.setAttribute("fill", "currentColor");
            fileIcon.setAttribute("class", "bi bi-file-earmark");
            fileIcon.setAttribute("viewBox", "0 0 16 16");
            fileIcon.innerHTML = `
                <path d="M14 4.5V14a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V2a2 2 0 0 1 2-2h5.5zm-3 0A1.5 1.5 0 0 1 9.5 3V1H4a1 1 0 0 0-1 1v12a1 1 0 0 0 1 1h8a1 1 0 0 0 1-1V4.5z"/>
            `;

            fileItem.appendChild(fileIcon);
            fileItem.appendChild(document.createTextNode(` ${fileName}`));
            fileList.appendChild(fileItem);
        });
    } else {
        const noFiles = document.createElement('li');
        noFiles.textContent = 'No files found.';
        noFiles.style.color = '#888';
        fileList.appendChild(noFiles);
    }

    tableElement.appendChild(fileList);
}
function filterTableList(event) {
    const filterText = event.target.value.toLowerCase();
    const tableListItems = document.querySelectorAll('#explorer-list li');

    tableListItems.forEach(item => {
        const tableName = item.querySelector('span').textContent.toLowerCase();
        if (tableName.includes(filterText)) {
            item.style.display = '';
        } else {
            item.style.display = 'none';
        }
    });
}
