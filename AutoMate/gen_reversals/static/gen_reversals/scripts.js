require.config({ paths: { 'vs': 'https://cdn.jsdelivr.net/npm/monaco-editor@0.33.0/min/vs' } });

let inputEditor, outputEditor;
let currentTheme = 'vs-light';

require(['vs/editor/editor.main'], function () {
  inputEditor = monaco.editor.create(document.getElementById('input-editor'), {
    value: '',
    language: 'json',
    theme: currentTheme,
    automaticLayout: true,
    minimap: { enabled: false }
  });

  outputEditor = monaco.editor.create(document.getElementById('output-editor'), {
    value: '',
    language: 'json',
    theme: currentTheme,
    readOnly: true,
    automaticLayout: true,
    minimap: { enabled: false }
  });

  inputEditor.onDidChangeModelContent(() => {
    const rawInput = inputEditor.getValue();
    updateJsonStatus(rawInput);
  });
});

function toggleTheme() {
  currentTheme = currentTheme === 'vs-light' ? 'vs-dark' : 'vs-light';
  monaco.editor.setTheme(currentTheme);
}

function updateJsonStatus(text) {
  const model = inputEditor.getModel();
  const statusElement = document.getElementById('json-status');

  try {
    JSON.parse(text);
    monaco.editor.setModelMarkers(model, 'json', []);
    statusElement.innerText = "Status: ✅ Valid JSON";
    statusElement.style.color = "limegreen";
  } catch (error) {
    monaco.editor.setModelMarkers(model, 'json', [{
      startLineNumber: 1,
      startColumn: 1,
      endLineNumber: 1,
      endColumn: 1,
      message: "Invalid JSON: " + error.message,
      severity: monaco.MarkerSeverity.Error
    }]);
    statusElement.innerText = "Status: ❌ Invalid JSON";
    statusElement.style.color = "red";
  }
}

function cleanData() {
  const rawText = inputEditor.getValue();
  const cleanedJsonBlocks = extractJsonBlocks(rawText);

  if (cleanedJsonBlocks.length === 0) {
    alert("❌ No JSON blocks found.");
    inputEditor.setValue(""); // clear input editor
    return;
  }

  const jsonObjects = cleanedJsonBlocks.map(jsonStr => {
    try {
      return JSON.parse(jsonStr);
    } catch (e) {
      console.warn("Skipped invalid JSON block during parsing:", jsonStr);
      return null;
    }
  }).filter(obj => obj !== null);

  const requests100 = [];
  const responses110 = [];

  jsonObjects.forEach(obj => {
    const mti = obj.mti;
    const de037 = obj?.d0t0_elements?.DE037 || obj?.d0t0_elements?.DE037?.trim();

    if (!de037) {
      console.warn("Skipped message without DE037:", obj);
      return;
    }

    if (mti === 100 || mti === "100") {
      requests100.push({ rrn: de037, message: obj });
    } else if (mti === 110 || mti === "110") {
      responses110.push({ rrn: de037, message: obj });
    }
  });

  const groupedMessages = [];

  requests100.forEach((request, index) => {
    const rrn = request.rrn;
    const matchingResponse = responses110.find(response => response.rrn === rrn);

    const pair = {};
    pair[`request${index + 1}`] = request.message;
    pair[`response${index + 1}`] = matchingResponse ? matchingResponse.message : null;

    groupedMessages.push(pair);
  });

  const finalJsonString = JSON.stringify(groupedMessages, null, 4);

  inputEditor.setValue(finalJsonString);
}

function copyOutput() {
  const copyBtn = document.getElementById('copyBtn');
  const outputText = outputEditor.getValue();

  navigator.clipboard.writeText(outputText)
    .then(() => {
      copyBtn.innerText = "Copied!";
      copyBtn.classList.add("copied");

      setTimeout(() => {
        copyBtn.innerText = "Copy Output";
        copyBtn.classList.remove("copied");
      }, 1000);
    })
    .catch(err => {
      console.error('❌ Failed to copy:', err);
    });
}

function handleAction(actionName) {
  console.log(`${actionName} button clicked!`);

  const outputText = outputEditor.getValue();
  const updatedOutput = `${actionName} action triggered!\n\n` + outputText;

  outputEditor.setValue(updatedOutput);
}

function extractJsonBlocks(text) {
  const blocks = [];
  let braceCount = 0;
  let startIndex = -1;

  for (let i = 0; i < text.length; i++) {
    const char = text[i];

    if (char === '{') {
      if (braceCount === 0) {
        startIndex = i;
      }
      braceCount++;
    } else if (char === '}') {
      braceCount--;
      if (braceCount === 0 && startIndex !== -1) {
        const jsonBlock = text.slice(startIndex, i + 1);
        try {
          JSON.parse(jsonBlock);
          blocks.push(jsonBlock);
        } catch (e) {
          console.warn("Skipped invalid JSON block:", jsonBlock);
        }
        startIndex = -1;
      }
    }
  }

  return blocks;
}
