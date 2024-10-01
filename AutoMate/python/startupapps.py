import subprocess
import time
import pyautogui

#====== List of app paths
app_paths = [
    r'C:\Program Files\Google\Chrome\Application\chrome.exe',
    r'C:\Program Files\Microsoft Office\root\Office16\OUTLOOK.EXE',
    'mstsc',
    r'C:\Program Files\Notepad++\notepad++.exe',
    r'C:\Program Files\PuTTY\putty.exe',
    r'C:\Softwares\PDFXEdit10_Portable_x64\PDFXEdit.exe',
    r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'
]

# Open Chrome with multiple URLs
chrome_path = r'C:\Program Files\Google\Chrome\Application\chrome.exe'
urls = [
    "https://www.portal1.com",  # Replace with the actual URLs you want to open
    "https://www.portal2.com",
    "https://www.portal3.com"
]

try:
    # Pass all URLs as arguments to Chrome
    subprocess.Popen([chrome_path] + urls)
    print(f"Google Chrome started with URLs: {', '.join(urls)}")
except Exception as e:
    print(f"Failed to open Google Chrome with the links. Error: {e}")

# Start other apps
for app_path in app_paths:
    subprocess.Popen(app_path)
    print(f"{app_path} was successfully started.")

#====== Start Raptor_F Django server
django_project_path = r'C:\Durgesh\Office\Automation\Raptor_Fiserv\Raptor_F'

try:
    subprocess.Popen(['python','manage.py','runserver'], cwd=django_project_path)
    print("Raptor_F started")

except Exception as e:
    print (f"Failed to start Raptor_F django server. Error: {e}")

#======== Start AutoMate Django server on port 8001
django_project_path_automate = r'C:\Durgesh\Office\Automation\AutoMate\Automate'

try:
    subprocess.Popen(['python', 'manage.py', 'runserver', '8001'], cwd=django_project_path_automate)
    print("AutoMate started on port 8001")
except Exception as e:
    print(f"Failed to start AutoMate django server. Error: {e}")