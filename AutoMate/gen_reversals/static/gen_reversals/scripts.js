var inputEditor = CodeMirror(document.getElementById('input-editor'), {
    lineNumbers: true,
    mode: "application/json",
    theme: "default",
    value: ""
  });
  
  function resizeEditor() {
    const containerHeight = document.getElementById('input-editor').parentElement.clientHeight;
    inputEditor.setSize("100%", containerHeight - 40);
  }
  
  window.addEventListener('resize', resizeEditor);
  resizeEditor();
  
  inputEditor.on("change", function (cm) {
    const rawInput = cm.getValue();
    processInputDataPreserveFormat(rawInput);
  });
  
  function processInputDataPreserveFormat(rawText) {
    const outputBox = document.getElementById('output-display');
  
    // Extract JSON-like blocks from raw text
    const jsonRegex = /{[\s\S]*?}/g;  // Captures multi-line JSON blocks
    const jsonMatches = rawText.match(jsonRegex);
  
    if (!jsonMatches) {
      outputBox.innerText = "❌ No JSON data found.";
      return;
    }
  
    let mti100Messages = [];
    let mti110Messages = [];
  
    jsonMatches.forEach(jsonStr => {
      try {
        const jsonData = JSON.parse(jsonStr);
  
        if (jsonData.mti === "100") {
          mti100Messages.push({
            rrn: jsonData.DE037 || 'NO_DE037',
            raw: jsonStr
          });
        } else if (jsonData.mti === "110") {
          mti110Messages.push({
            rrn: jsonData.DE037 || 'NO_DE037',
            raw: jsonStr
          });
        }
  
      } catch (error) {
        // Skip invalid JSON blocks
        console.warn("Invalid JSON block skipped:", jsonStr);
      }
    });
  
    // Validation Checks
    if (mti100Messages.length === 0 || mti110Messages.length === 0) {
      outputBox.innerText = "❌ Missing MTI 100 or MTI 110 messages.";
      return;
    }
  
    if (mti100Messages.length !== mti110Messages.length) {
      outputBox.innerText = `❌ MTI 100 count (${mti100Messages.length}) does not match MTI 110 count (${mti110Messages.length}).`;
      return;
    }
  
    // Group by DE037
    let groupedResults = '';
  
    mti100Messages.forEach(msg100 => {
      const rrn100 = msg100.rrn;
  
      const matching110 = mti110Messages.find(msg110 => msg110.rrn === rrn100);
  
      if (matching110) {
        groupedResults += `------ DE037: ${rrn100} ------\n`;
        groupedResults += `${msg100.raw}\n`;
        groupedResults += `${matching110.raw}\n\n`;
      } else {
        groupedResults += `------ DE037: ${rrn100} (No matching MTI 110) ------\n`;
        groupedResults += `${msg100.raw}\n\n`;
      }
    });
  
    // Output untouched original JSON blocks grouped logically
    outputBox.innerText = groupedResults.trim();
  }
  
  function copyOutput() {
    const copyBtn = document.getElementById('copyBtn');
    const outputText = document.getElementById('output-display').innerText;
  
    navigator.clipboard.writeText(outputText)
      .then(() => {
        copyBtn.innerText = "Copied!";
        copyBtn.classList.add("copied");
  
        setTimeout(() => {
          copyBtn.innerText = "Copy";
          copyBtn.classList.remove("copied");
        }, 2000);
      });
  }
  
  function handleAction(actionName) {
    console.log(actionName + " button clicked");
  
    const outputBox = document.getElementById('output-display');
    outputBox.innerText = `${actionName} action triggered!\n\n` + outputBox.innerText;
  }
  