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

def analyze_with_openai_nochunk(installed_apps, events):
    # Obfuscate sensitive information
    obfuscated_apps = {app: {key: obfuscate_sensitive_info(value) if isinstance(value, str) else value
                             for key, value in data.items()}
                       for app, data in installed_apps.items()}

    obfuscated_events = [obfuscate_sensitive_info(str(event)) for event in events]    

    prompt = f"""
    Please analyze the following obfuscated data:

    Installed Applications: {json.dumps(obfuscated_apps, indent=2)}

    Event Logs: {json.dumps(obfuscated_events, indent=2)}    

    For each application, check the following:
    1. The app name and version.
    2. The delivery mechanism.
    3. Whether the app is available in WinGet.

    Merge all the Apps and discovered apps from the Installed Applications Event Logs. Do not miss any app installation.

    Merge all the responses and provide a response in the format:
    AppName, Version, Delivery Mechanism, Is WinGet Compatible
    """

    try:
        response = openai.ChatCompletion.create(
            model=os.getenv("LLM_MODEL", "gpt-3.5-turbo"), 
            messages=[
                {"role": "system", "content": "You are a data scientist that analyzes System Events and applications."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=2000,
            temperature=0.2
        )
        print(f"OpenAI Response: {response}")  

        if 'choices' in response and len(response['choices']) > 0:
            content = response['choices'][0].get('message', {}).get('content', '')
            return content if content else "No content found in response."
        else:
            print(f"Unexpected response format: {response}")
            return "Error: Unexpected response format."
    except Exception as e:
        print(f"Error analyzing with OpenAI: {e}")
        return f"Error analyzing: {e}"

    return response

def analyze_with_openai(installed_apps, events):
    obfuscated_apps = {app: {key: obfuscate_sensitive_info(value) if isinstance(value, str) else value
                             for key, value in data.items()}
                       for app, data in installed_apps.items()}

    obfuscated_events = [obfuscate_sensitive_info(str(event)) for event in events]    
    
    
    def chunk_data(data, chunk_size=10):
        return [data[i:i + chunk_size] for i in range(0, len(data), chunk_size)]
    
    app_items = list(obfuscated_apps.items())
    event_items = list(obfuscated_events)        
    app_chunks = chunk_data(app_items, chunk_size=50)  
    event_chunks = chunk_data(event_items, chunk_size=50)
    

    responses = []
    for app_chunk, event_chunk in zip(app_chunks, event_chunks):        
        prompt = f"""
        Please analyze the following obfuscated data:
        
        Installed Applications: {json.dumps(dict(app_chunk), indent=2)}
        
        Event Logs: {json.dumps(event_chunk, indent=2)}    
        
        
        For each application, check the following:
        1. The app name and version.
        2. The delivery mechanism.
        3. Whether the app is available in WinGet.
        
        Merge all the Apps and discovered apps from the Installed Applications Event Logs. Do not miss any app installation.
        
        Merge all the responses and provide a response in the format:
        AppName, Version, Delivery Mechanism, Is WinGet Compatible
        """

        try:
            response = openai.ChatCompletion.create(
                model=os.getenv("LLM_MODEL", "gpt-3.5-turbo"), 
                messages=[{"role": "system", "content": "You are a data scientist that analyzes System Events and applications."},
                          {"role": "user", "content": prompt}],
                max_tokens=2000,
                temperature=0.2
            )
            print(f"OpenAI Response: {response}")  
            
            if 'choices' in response and len(response['choices']) > 0:
                content = response['choices'][0].get('message', {}).get('content', '')
                if content:
                    responses.append(content)
                else:
                    print("No content found in response.")
                    responses.append("No content found.")
            else:
                print(f"Unexpected response format: {response}")
                responses.append("Error: Unexpected response format.")
        except Exception as e:
            print(f"Error analyzing chunk with OpenAI: {e}")
            responses.append(f"Error analyzing chunk: {e}")

    # Prompt AI to merge all the responses in a format and then return the responses 
    prompt = f"""
    Input: {json.dumps(responses, indent=2)}    
    Please merge all the responses and provide a response in the format:        
    AppName, Version, Delivery Mechanism, Is WinGet Compatible
    """
    
    try:
        responses = openai.ChatCompletion.create(
            model=os.getenv("LLM_MODEL", "gpt-3.5-turbo"), 
            messages=[{"role": "system", "content": "You are a data engineer that produce merged data sets as CSV files."},
                      {"role": "user", "content": prompt}],
            max_tokens=2000,
            temperature=0.2
        )
        print(f"OpenAI Response: {responses}")
    except Exception as e:
        print(f"Error merging responses with OpenAI: {e}")
        
    return responses

def generate_reports(csv_filename, base_directory, computer_name):
    print(f"Starting generate_reports function from {csv_filename}...")

    try:
        df = pd.read_csv(csv_filename, encoding='utf-8')
    except UnicodeDecodeError:
        print("UnicodeDecodeError: Trying with 'latin1' encoding")
        df = pd.read_csv(csv_filename, encoding='latin1')
    
    fig = make_subplots(
        rows=2, cols=2, 
        subplot_titles=[
            "Distribution of Apps by Delivery Mechanism",
            "Number of Apps by Delivery Mechanism",
            "Apps by WinGet Compatibility",
            "App Versions Distribution"
        ],
        specs=[
            [{'type': 'pie'}, {'type': 'bar'}],  
            [{'type': 'bar'}, {'type': 'scatter'}]  
        ]
    )
    
    delivery_counts = df['Delivery Mechanism'].value_counts()
    pie_chart = go.Pie(labels=delivery_counts.index, values=delivery_counts, hole=0.3)
    fig.add_trace(pie_chart, row=1, col=1)
        
    bar_chart = go.Bar(x=delivery_counts.index, y=delivery_counts, name='Delivery Mechanism')
    fig.add_trace(bar_chart, row=1, col=2)
    
    winget_compatible_counts = df['Is WinGet Compatible'].value_counts()
    winget_bar_chart = go.Bar(x=winget_compatible_counts.index, y=winget_compatible_counts, name='WinGet Compatibility')
    fig.add_trace(winget_bar_chart, row=2, col=1)
    
    version_counts = df['Version'].value_counts().head(10)  
    version_scatter_chart = go.Scatter(x=version_counts.index, y=version_counts, mode='markers', name='Version Counts')
    fig.add_trace(version_scatter_chart, row=2, col=2)
        
    fig.update_layout(
        height=800,
        width=1000,
        title_text="App Analysis Reports",
        showlegend=False
    )    
    reporting_path = os.path.join(base_directory, f"ReportingData\\{computer_name}_report.html") 
    fig.write_html(reporting_path)
    print("Interactive HTML report saved to {reporting_path}")

    print("Reports generated successfully.")