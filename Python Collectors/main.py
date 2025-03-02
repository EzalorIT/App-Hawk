import os
import subprocess
import csv
from datetime import datetime
import psutil
import winreg

output_path = r"D:\output"

def ensure_output_path_exists(output_path):
    if not os.path.exists(output_path):
        print(f"Output path does not exist. Creating directory at {output_path}")
        os.makedirs(output_path)

def get_current_date():
    return datetime.now().strftime('%d%m%Y')

def get_hostname():
    return psutil.Process().name()

def extract_application_events():
    print("Starting Extract-ApplicationEvents function to extract logs from Application log...")
    events = []
    try:
        command = 'wevtutil qe Application /f:text /c:100'
        result = subprocess.check_output(command, shell=True, encoding='utf-8')
        event_lines = result.splitlines()
                
        for line in event_lines:
            events.append({"Message": line})
    except subprocess.CalledProcessError as e:
        print(f"Error extracting events: {e}")
    
    print(f"Completed Extract-ApplicationEvents function with {len(events)} events retrieved.")
    return events


def get_installed_apps_registry():
    print("Starting Get-InstalledAppsRegistry function to retrieve installed applications from the Windows registry...")
    installed_apps = []
    hives = [winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER]
    registry_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"
    
    for hive in hives:
        try:
            with winreg.ConnectRegistry(None, hive) as hkey:
                registry_key = winreg.OpenKey(hkey, registry_path)
                for i in range(0, winreg.QueryInfoKey(registry_key)[0]):
                    try:
                        subkey_name = winreg.EnumKey(registry_key, i)
                        subkey = winreg.OpenKey(registry_key, subkey_name)
                        app_name, _ = winreg.QueryValueEx(subkey, "DisplayName")
                        app_version, _ = winreg.QueryValueEx(subkey, "DisplayVersion")
                        installed_apps.append({"Name": app_name, "Version": app_version, "DeliveryMechanism": "App Provider"})
                    except WindowsError:
                        continue
        except WindowsError:
            continue
    print(f"Completed Get-InstalledAppsRegistry function with {len(installed_apps)} applications retrieved.")
    return installed_apps

def get_installed_apps_wmi():
    print("Starting Get-InstalledAppsWMI function to retrieve installed applications using WMI...")
    installed_apps = []
    try:
        command = 'wmic product get name, version, vendor'
        result = subprocess.check_output(command, shell=True, encoding='utf-8')
        for line in result.splitlines()[1:]:
            app_info = line.split()
            if len(app_info) >= 2:
                installed_apps.append({
                    "Name": app_info[0],
                    "Version": app_info[1],
                    "Manufacturer": app_info[2] if len(app_info) > 2 else "Unknown",
                    "DeliveryMechanism": "App Provider"
                })
    except subprocess.CalledProcessError as e:
        print(f"Error retrieving WMI data: {e}")
    print(f"Completed Get-InstalledAppsWMI function with {len(installed_apps)} applications retrieved.")
    return installed_apps


def get_installed_apps_winget():
    print("Starting Get-InstalledAppsWinget function to retrieve installed applications via WinGet...")
    installed_apps = []
    try:
        command = 'winget list'
        result = subprocess.check_output(command, shell=True, encoding='utf-8')
        lines = result.splitlines()
        for line in lines[3:]:
            app_info = line.split()
            if len(app_info) >= 2:
                installed_apps.append({
                    "Name": app_info[0],
                    "Version": app_info[1],
                    "DeliveryMechanism": "WinGet"
                })
    except subprocess.CalledProcessError as e:
        print(f"Error running WinGet: {e}")
    print(f"Completed Get-InstalledAppsWinget function with {len(installed_apps)} applications retrieved.")
    return installed_apps


def append_changed_data(file_path, new_data, unique_fields):
    existing_data_set = {}

    if os.path.exists(file_path):
        with open(file_path, mode='r', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                key = "_".join([row[field] for field in unique_fields if field in row])
                existing_data_set[key] = True
        print(f"Loaded existing data. Found {len(existing_data_set)} unique entries in {file_path}.")
    else:
        print(f"File {file_path} does not exist, creating new file.")

    new_rows = []
    for row in new_data:
        key = "_".join([row[field] for field in unique_fields if field in row])
        if key not in existing_data_set:
            new_rows.append(row)

    if new_rows:
        with open(file_path, mode='a', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=new_rows[0].keys())
            if file.tell() == 0:  
                writer.writeheader()
            writer.writerows(new_rows)
        print(f"{len(new_rows)} new rows appended to {file_path}")
    else:
        print(f"No new data to append to {file_path}")

def invoke_sequential_execution(output_path):
    ensure_output_path_exists(output_path)

    date_string = get_current_date()
    hostname = get_hostname()
    
    print("Starting sequential execution...")
    events = extract_application_events()
    installed_apps_registry = get_installed_apps_registry()
    installed_apps_wmi = get_installed_apps_wmi()
    installed_apps_winget = get_installed_apps_winget()
    
    events_file_path = os.path.join(output_path, f"{hostname}_ApplicationEvents_{date_string}.csv")
    installed_apps_registry_file_path = os.path.join(output_path, f"{hostname}_InstalledAppsRegistry_{date_string}.csv")
    installed_apps_wmi_file_path = os.path.join(output_path, f"{hostname}_InstalledAppsWMI_{date_string}.csv")
    installed_apps_winget_file_path = os.path.join(output_path, f"{hostname}_InstalledAppsWinget_{date_string}.csv")

   
    append_changed_data(events_file_path, events, unique_fields=['Message'])
    append_changed_data(installed_apps_registry_file_path, installed_apps_registry, unique_fields=['Name', 'Version'])
    append_changed_data(installed_apps_wmi_file_path, installed_apps_wmi, unique_fields=['Name', 'Version'])
    append_changed_data(installed_apps_winget_file_path, installed_apps_winget, unique_fields=['Name', 'Version'])

invoke_sequential_execution(output_path)
