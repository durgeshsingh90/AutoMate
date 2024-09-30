import subprocess
import time
import pyautogui


#====Path to Toad executable
#toad_path = r'C:\Program Files\Quest Software\Toad for Oracle 16.3\Toad.exe'
#subprocess.Popen(toad_path)
#print("Started Toad")
#
## Wait for Toad to open (adjust the sleep time as necessary)
#time.sleep(25)  # Adjust based on how long it takes Toad to open
#
## Example: Move the mouse to a specific position and click
## You need to know the exact coordinates where you want to click
## You can use pyautogui.position() to find coordinates
#pyautogui.moveTo(1325, 747)  # Move to coordinates (100, 200)
#pyautogui.click()  # Perform a click
#time.sleep(3)
## Perform more clicks or other actions as needed
#pyautogui.moveTo(453, 182)
#pyautogui.click()
#
## Perform more clicks or other actions as needed
#pyautogui.moveTo(879, 574)
#pyautogui.click()
#print("Performed the required clicks on Toad")

#====== List of app paths
app_paths = [
    # 'explorer',
    r'C:\Program Files\Google\Chrome\Application\chrome.exe',
    r'C:\Program Files\Microsoft Office\root\Office16\OUTLOOK.EXE',
    # #r'C:\Program Files\Microsoft VS Code\Code.exe',
    'mstsc',
    r'C:\Program Files\Notepad++\notepad++.exe',
    r'C:\Program Files\PuTTY\putty.exe',
    r'C:\Softwares\PDFXEdit10_Portable_x64\PDFXEdit.exe',
    r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'
    # r'C:\Program Files (x86)\Zscaler\ZSATray\ZSATray.exe',
    # #r'C:\Users\f94gdos\Pictures\Draw.io\draw.io-24.4.0-windows-no-installer.exe'
    # r'C:\Program Files\Microsoft VS Code\Code.exe'

    # Add more app paths as needed,
]

# Start each app
for app_path in app_paths:
    subprocess.Popen(app_path)
    print(f"{app_path} was successfully started.")

#======Start Raptor_F Django server
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
