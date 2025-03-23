// ✅ CSRF Helper Function
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
      const cookies = document.cookie.split(';');
      for (let cookie of cookies) {
        cookie = cookie.trim();
        if (cookie.startsWith(name + '=')) {
          cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
          break;
        }
      }
    }
    return cookieValue;
  }
  
  const csrftoken = getCookie('csrftoken');
  
  // ✅ Global Variables
  let editor;
  let defaultContent = `Paste your Splunk logs here...`;
  
  // ✅ Initialize App
  document.addEventListener("DOMContentLoaded", () => {
    initMonacoEditor();
    setupOutputSelectionListener();
  
    // Button Event Listeners (optional, or use inline onclick in HTML)
    document.getElementById('copyButton').addEventListener('click', copyOutput);
    document.getElementById('defaultButton').addEventListener('click', setDefault);
  });
  
  // ✅ Initialize Monaco Editor & Restore Saved Logs
  function initMonacoEditor() {
    require.config({ paths: { 'vs': 'https://cdn.jsdelivr.net/npm/monaco-editor@0.34.1/min/vs' } });
  
    require(['vs/editor/editor.main'], () => {
      editor = monaco.editor.create(document.getElementById('editor'), {
        value: defaultContent,
        language: 'plaintext',
        theme: 'vs-dark',
        automaticLayout: true
      });
  
      // Load from localStorage (if available)
      const savedLogs = localStorage.getItem('splunkLogs');
      if (savedLogs) {
        editor.setValue(savedLogs);
      }
  
      // On editor content change: Save to localStorage
      editor.onDidChangeModelContent(() => {
        localStorage.setItem('splunkLogs', editor.getValue());
      });
  
      // On editor selection change: Update selected length status bar
      editor.onDidChangeCursorSelection(updateEditorSelection);
    });
  }
  
  // ✅ Update Selection Length in Status Bar (Editor)
  function updateEditorSelection() {
    if (!editor) return;
    const selection = editor.getSelection();
    const selectedText = editor.getModel().getValueInRange(selection);
    document.getElementById('editorSelectionCount').innerText = selectedText.length;
  }
  
  // ✅ Output Selection Listener (Output Area)
  function setupOutputSelectionListener() {
    const outputContent = document.getElementById('outputArea');
    const outputSelectionCount = document.getElementById('outputSelectionCount');
  
    outputContent.addEventListener('mouseup', updateOutputSelection);
    outputContent.addEventListener('keyup', updateOutputSelection);
  
    function updateOutputSelection() {
      const selectedText = window.getSelection().toString();
      outputSelectionCount.innerText = selectedText.length;
    }
  }
  
  // ✅ Parse Logs to JSON
  async function parseLogsToJSON() {
    const logData = editor.getValue().trim();
    if (!logData) {
      notify("Please provide log data to parse.");
      return;
    }
  
    try {
      const data = await sendLogsToBackend(logData);
  
      if (data.status === 'error' || !data.result) {
        notify(`❌ Error: ${data.message}`);
        return;
      }
  
      const jsonOutput = JSON.stringify(data.result, null, 2);
      displayOutput(jsonOutput, 'language-json');
    } catch (error) {
      notify(`❌ Error: ${error.message}`);
    }
  }
  
  // ✅ Parse Logs to YAML
  async function parseLogsToYAML() {
    const logData = editor.getValue().trim();
    if (!logData) {
      notify("Please provide log data to parse.");
      return;
    }
  
    try {
      const data = await sendLogsToBackend(logData);
  
      if (data.status === 'error' || !data.result) {
        notify(`❌ Error: ${data.message}`);
        return;
      }
  
      const jsonData = data.result;
      let sortedJsonData = {};
  
      // Keep MTI on top if available
      if (jsonData && jsonData.MTI) {
        sortedJsonData.MTI = jsonData.MTI;
        for (let key in jsonData) {
          if (key !== 'MTI') sortedJsonData[key] = jsonData[key];
        }
      } else {
        sortedJsonData = jsonData;
      }
  
      let yamlOutput = jsyaml.dump(sortedJsonData, {
        quotingType: '"',
        forceQuotes: true,
        sortKeys: false
      });
  
      // Clean YAML: Remove quotes around keys
      yamlOutput = yamlOutput.replace(/"([^"]+)":/g, '$1:');
  
      displayOutput(yamlOutput, 'language-yaml');
    } catch (error) {
      notify(`❌ Error: ${error.message}`);
    }
  }
  
  // ✅ Send Logs to Django Backend Parser API
  async function sendLogsToBackend(logData) {
    const response = await fetch('/splunkparser/parse/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrftoken
      },
      body: JSON.stringify({ log_data: logData })
    });
  
    if (!response.ok) {
      throw new Error(`Server Error: ${response.status}`);
    }
  
    return await response.json();
  }
  
  // ✅ Display Output in Output Area
  function displayOutput(content, languageClass) {
    const output = document.getElementById('outputArea');
  
    output.textContent = content;
    output.className = languageClass;
  
    Prism.highlightElement(output);
  
    notify(""); // Clear previous notifications
  }
  
  // ✅ Copy Output to Clipboard
  function copyOutput() {
    const output = document.getElementById('outputArea').textContent;
    const copyButton = document.getElementById('copyButton');
  
    navigator.clipboard.writeText(output)
      .then(() => {
        copyButton.textContent = 'Copied!';
        copyButton.classList.add('copied');
  
        setTimeout(() => {
          copyButton.textContent = 'Copy Output';
          copyButton.classList.remove('copied');
        }, 1000);
      })
      .catch(err => {
        notify(`❌ Failed to copy: ${err.message}`);
      });
  }
  
  // ✅ Reset to Default Content
  function setDefault() {
    if (!editor) return;
    editor.setValue(defaultContent);
    displayOutput('', ''); // Clear output
    notify(""); // Clear previous notifications
  
    const defaultBtn = document.getElementById('defaultButton');
    defaultBtn.textContent = 'Added!';
    defaultBtn.classList.add('added');
  
    setTimeout(() => {
      defaultBtn.textContent = 'Set Default';
      defaultBtn.classList.remove('added');
    }, 1000);
  }
  
  // ✅ Open Config Editor (Settings Page)
  function openConfig() {
    window.location.href = '/splunkparser/settings/';
  }
  
  // ✅ Notification Helper
  function notify(message) {
    const notification = document.getElementById('notification');
    if (notification) {
      notification.textContent = message;
    }
  }
  