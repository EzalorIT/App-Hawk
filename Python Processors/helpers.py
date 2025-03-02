def extract_application_events(log_type='Application'):
    print(f"Starting extract_application_events function to extract logs from {log_type} log...")
    log_handle = win32evtlog.OpenEventLog(None, log_type)
    events = []
    total_events = win32evtlog.GetNumberOfEventLogRecords(log_handle)    
    time_threshold = datetime.now() - timedelta(days=1)

    progress = 0
    while True:
        events_batch = win32evtlog.ReadEventLog(log_handle, win32evtlog.EVENTLOG_SEQUENTIAL_READ | win32evtlog.EVENTLOG_FORWARDS_READ, 0)

        if not events_batch:
            break

        for event in events_batch:            
            event_time = event.TimeGenerated            
            if event_time >= time_threshold:
                events.append(event)

            progress += 1
            update_progress(progress, total_events)

    print(f"\nCompleted extract_application_events function with {len(events)} events retrieved.")
    return events

def get_installed_apps_registry():
    print("Starting get_installed_apps_registry function to retrieve installed applications from the Windows registry...")
    registry_apps = {}
    registry_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"
    progress = 0
    for hive in [winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER]:
        try:
            reg_key = winreg.OpenKey(hive, registry_path)
            total = winreg.QueryInfoKey(reg_key)[0]
            for i in range(0, total):
                sub_key = winreg.EnumKey(reg_key, i)
                try:
                    app_key = winreg.OpenKey(reg_key, sub_key)
                    app_name = winreg.QueryValueEx(app_key, "DisplayName")[0]
                    app_version = winreg.QueryValueEx(app_key, "DisplayVersion")[0] if "DisplayVersion" in dict(winreg.QueryInfoKey(app_key))[1] else "N/A"
                    registry_apps[app_name] = {'Version': app_version, 'Delivery Mechanism': 'App Provider'}
                    progress += 1
                    update_progress(progress, total)
                except:
                    continue
        except:
            continue

    print(f"\nCompleted get_installed_apps_registry function with {len(registry_apps)} applications retrieved.")
    return registry_apps

def get_installed_apps_wmi():
    print("Starting get_installed_apps_wmi function to retrieve installed applications using WMI...")
    pythoncom.CoInitialize()  
    c = wmi.WMI()
    apps = {}
    progress = 0
    total = len(list(c.Win32_Product()))  
    for product in c.Win32_Product():
        try:
            manufacturer = product.Manufacturer if hasattr(product, 'Manufacturer') else 'Unknown'
            apps[product.Name] = {
                'Version': product.Version,
                'Manufacturer': manufacturer,
                'Delivery Mechanism': 'App Provider'
            }
            progress += 1
            update_progress(progress, total)
        except AttributeError:
            continue

    print(f"\nCompleted get_installed_apps_wmi function with {len(apps)} applications retrieved.")
    return apps

def get_installed_apps_winget():
    print("Starting get_installed_apps_winget function to retrieve installed applications via WinGet...")
    installed_apps = {}
    try:
        
        result = subprocess.run(['winget', 'list'], capture_output=True, text=True)
        if result.returncode == 0:            
            lines = result.stdout.splitlines()
            for line in lines[3:]:  
                app_info = line.split()
                if len(app_info) >= 2:
                    app_name = app_info[0]
                    app_version = app_info[1]
                    installed_apps[app_name] = {'Version': app_version, 'Delivery Mechanism': 'WinGet'}
        else:
            print("Error fetching WinGet list.")
    except Exception as e:
        print(f"Error running WinGet: {e}")

    print(f"\nCompleted get_installed_apps_winget function with {len(installed_apps)} applications retrieved.")
    return installed_apps