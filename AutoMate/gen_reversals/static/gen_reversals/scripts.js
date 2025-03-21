// Initialize CodeMirror
var inputEditor = CodeMirror(document.getElementById('input-editor'), {
    lineNumbers: true,
    mode: "javascript",
    theme: "default",
    value: ""
  });
  
  function resizeEditor() {
    const containerHeight = document.getElementById('input-editor').parentElement.clientHeight;
    inputEditor.setSize("100%", containerHeight - 40);
  }
  
  window.addEventListener('resize', resizeEditor);
  resizeEditor();
  
  inputEditor.on("change", function(cm) {
    document.getElementById('output-display').innerText = cm.getValue();
  });
  
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
  