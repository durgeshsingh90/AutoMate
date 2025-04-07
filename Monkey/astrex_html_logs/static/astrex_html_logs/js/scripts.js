let file = null;
let de032_counts = {};
let startTime;
let loadingTimerInterval;
let loadingTimeout;

document.getElementById('htmlLogFile').addEventListener('change', function(e) {
  file = e.target.files[0];
  document.getElementById('uploadedFileName').textContent = file ? file.name : '';
document.getElementById('copyFileNameBtn').style.display = file ? 'inline-block' : 'none';
  if (file) {
    uploadFile();
  }
});

function uploadFile() {
  if (!file || !file.name.endsWith('.html')) {
    alert('Please select a valid HTML file.');
    return;
  }

  startTime = new Date();
  startLoadingTimer();

  // Set a timeout to show the loading screen if the process takes more than 2 seconds
  loadingTimeout = setTimeout(showLoadingScreen, 2000);

  const formData = new FormData();
  formData.append('file', file);

  fetch('/astrex_html_logs/upload_log/', {
    method: 'POST',
    body: formData
  }).then(res => res.json())
  .then(data => {
    clearTimeout(loadingTimeout); // Clear the loading timeout if the process completes in time
    hideLoadingScreen();
    clearInterval(loadingTimerInterval);
    if (data.status === 'success') {
      const container = document.getElementById('de032Container');
      container.innerHTML = '';
      const summaryDetails = document.getElementById('summaryDetails');
      const rightItems = document.querySelector('.right-items');
      rightItems.style.display = 'flex';
      de032_counts = data.de032_counts;

      // Update summary information
      summaryDetails.innerHTML = `
        <p>Total DE032 Count: ${data.total_DE032_count}</p>
        <p>Total Transactions: ${data.total_txn}</p>
        <p>Start Log Time: ${data.start_log_time}</p>
        <p>End Log Time: ${data.end_log_time}</p>
        <p>Total Duration: ${calculateDuration(data.start_log_time, data.end_log_time)}</p>
      `;
      document.getElementById('scriptRunDuration').textContent = `Script Run Duration: ${calculateExecutionDuration(Math.floor((new Date() - startTime) / 1000))}`;

      const de032s = data.de032_counts;

      Object.entries(de032s).forEach(([key, count]) => {
        const box = document.createElement('div');
        box.className = 'de032-box';
        box.innerHTML = `
          <div class="de032-header">DE032: ${key}</div>
          <div class="count">Count: ${count}</div>
          <button class="download-btn">Download</button>
          <button class="convert-btn">Convert to EMVCo</button>
        `;
        const btn = box.querySelector('.download-btn');
        const convertBtn = box.querySelector('.convert-btn');
        
        btn.addEventListener('click', () => {
  const dlForm = new FormData();
  dlForm.append('de032', key);
  dlForm.append('filename', file.name);

  showLoadingScreen();

  fetch('/astrex_html_logs/download_filtered/', {
    method: 'POST',
    body: dlForm
  }).then(res => res.json())
  .then(result => {
    if (result.status === 'success') {
      const link = document.createElement('a');
      link.href = `/media/${result.filtered_file}`;
      link.download = result.filtered_file.split('/').pop();
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    } else {
      alert(result.message);
    }
    hideLoadingScreen();
  }).catch(err => {
    hideLoadingScreen();
    console.error(err);
    alert('Download failed.');
  });
});
  
convertBtn.addEventListener('click', () => {
  const convertForm = new FormData();
  convertForm.append('de032', key);
  convertForm.append('filename', file.name);
  fetch('/astrex_html_logs/convert_emvco/', {
    method: 'POST',
    body: convertForm
  }).then(res => res.json())
  .then(result => {
    if (result.status === 'success') {
      const link = document.createElement('a');
      link.href = `/media/${result.emvco_file}`;
      link.download = result.emvco_file.split('/').pop();
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    } else {
      alert(result.message);
    }
  });
});
        container.appendChild(box);
      });

      const downloadAllBtn = document.getElementById('downloadAllBtn');
if (Object.keys(de032_counts).length > 0) {
  downloadAllBtn.style.display = 'inline-block';  // or 'flex' if you prefer
} else {
  downloadAllBtn.style.display = 'none';
}
    } else {
      alert(data.message);
    }
  })
  .catch(err => {
    clearTimeout(loadingTimeout); // Clear the loading timeout if there's an error
    hideLoadingScreen();
    clearInterval(loadingTimerInterval);
    console.error(err);
    alert('Upload failed.');
  });
}

function showLoadingScreen() {
  document.getElementById('loadingScreen').style.display = 'flex';
  cycleMedia();
}

function hideLoadingScreen() {
  const media = document.querySelectorAll('.loading-media');
  media.forEach(item => {
    item.style.display = 'none';
    if (item.tagName === 'VIDEO') {
      item.pause();
      item.currentTime = 0;
    }
  });
  document.getElementById('loadingScreen').style.display = 'none';
  clearInterval(loadingTimerInterval);
}

function cycleMedia() {
  const media = document.querySelectorAll('.loading-media');
  let currentIndex = 0;

  function playNext() {
    // Hide current media
    media[currentIndex].style.opacity = 0;
    setTimeout(() => {
      media[currentIndex].style.display = 'none';

      // Move to the next media
      currentIndex = (currentIndex + 1) % media.length;
      const nextMedia = media[currentIndex];

      // Show the next media
      if (nextMedia.tagName === 'VIDEO') {
        nextMedia.style.display = 'block';
        nextMedia.style.opacity = 1;
        nextMedia.play();
        nextMedia.onended = playNext;
      } else {
        nextMedia.style.display = 'block';
        nextMedia.style.opacity = 1;
        setTimeout(playNext, 2000); // Change this to the duration of the GIF
      }
    }, 1000); // Match the transition duration used in CSS
  }

  // Initially play the first media
  if (media[currentIndex].tagName === 'VIDEO') {
    media[currentIndex].style.display = 'block';
    media[currentIndex].style.opacity = 1;
    media[currentIndex].play();
    media[currentIndex].onended = playNext;
  } else {
    media[currentIndex].style.display = 'block';
    media[currentIndex].style.opacity = 1;
    setTimeout(playNext, 2000); // Change this to the duration of the GIF
  }
}

function startLoadingTimer() {
  const timerElement = document.getElementById('loadingTimer');

  loadingTimerInterval = setInterval(() => {
    const elapsedSeconds = Math.floor((new Date() - startTime) / 1000);
    timerElement.textContent = calculateExecutionDuration(elapsedSeconds);
  }, 1000);
}

function calculateDuration(start, end) {
  const startTime = new Date(start);
  const endTime = new Date(end);
  const duration = endTime - startTime;

  const hours = Math.floor(duration / (1000 * 60 * 60));
  const minutes = Math.floor((duration % (1000 * 60 * 60)) / (1000 * 60));
  const seconds = Math.floor((duration % (1000 * 60)) / 1000);

  return `${hours}h ${minutes}m ${seconds}s`;
}

function calculateExecutionDuration(executionTime) {
  const hours = Math.floor(executionTime / 3600);
  const minutes = Math.floor((executionTime % 3600) / 60);
  const seconds = executionTime % 60;
  return `${hours}h ${minutes}m ${seconds}s`;
}

document.getElementById('downloadAllBtn').addEventListener('click', function(event) {
  event.stopPropagation();
  showLoadingScreen();

  const dlForm = new FormData();
  dlForm.append('filename', file.name);

  fetch('/astrex_html_logs/zip_filtered_files/', {
    method: 'POST',
    body: dlForm
  }).then(res => res.json())
  .then(result => {
    if (result.status === 'success') {
      const link = document.createElement('a');
      link.href = `/media/${result.zip_file}`;
      link.download = result.zip_file.split('/').pop();
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    } else {
      alert(result.message);
    }
    hideLoadingScreen();
  }).catch(err => {
    hideLoadingScreen();
    console.error(err);
    alert('Download failed.');
  });
});
document.getElementById('copyFileNameBtn').addEventListener('click', function () {
  const text = document.getElementById('uploadedFileName').textContent;
  navigator.clipboard.writeText(text)
    .then(() => {
      document.getElementById('copyFileNameBtn').textContent = '✅';
      setTimeout(() => {
        document.getElementById('copyFileNameBtn').textContent = '📋';
      }, 1500);
    })
    .catch(err => {
      alert('Failed to copy filename');
      console.error(err);
    });
});
