import re
import json
import urllib.parse
import pythoncom
import wmi
import win32evtlog
import subprocess
import os
import winreg
import psutil
import winrm
import csv
import concurrent.futures
import requests
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from collections import defaultdict
import threading
import sys
import time
import yaml
import openai
import matplotlib.pyplot as plt
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.graph_objects as go
from cryptography.fernet import Fernet

base_directory = os.getenv("BASE_DIRECTORY", "D:\\Work\\AppHawk\\Test\\")

if not os.path.exists(base_directory):
    print(f"Base directory {base_directory} does not exist.")
    exit(1)

script_directory = os.path.dirname(os.path.realpath(__file__))
encryption_script_path = os.path.join(script_directory, "encrypt.py")

if not os.path.exists(encryption_script_path):
    print(f"Encryption script not found at {encryption_script_path}.")
    exit(1)
else:
    print(f"Executing encryption script at {encryption_script_path}...")
    os.system(f"python \"{encryption_script_path}\"")

key_path = os.path.join(base_directory, "Vault\\secret.key")
encrypted_key_path = os.path.join(base_directory, "Vault\\encrypted_openai_key.txt")

try:
    with open(key_path, "rb") as key_file:
        key = key_file.read()

    cipher_suite = Fernet(key)
    with open(encrypted_key_path, "rb") as enc_file:
        encrypted_api_key = enc_file.read()

    openai_api_key = cipher_suite.decrypt(encrypted_api_key).decode()
    print("API key successfully decrypted.")
except Exception as e:
    print(f"Error retrieving or decrypting API key: {e}")
    exit(1)

openai.api_key = openai_api_key

def update_progress(progress, total):
    percent_complete = (progress / total) * 100
    sys.stdout.write(f"\rProcessing... {progress}/{total} ({percent_complete:.2f}%)")
    sys.stdout.flush()

def obfuscate_sensitive_info(data):
    obfuscated_data = re.sub(r'(HostName|IP|UserName|Password|Email)\S*', '***', data)
    return obfuscated_data

def analyze_with_openai(installed_apps, events):
    obfuscated_apps = {app: {key: obfuscate_sensitive_info(value) if isinstance(value, str) else value
                             for key, value in data.items()}
                       for app, data in installed_apps.items()}

    obfuscated_events = [obfuscate_sensitive_info(str(event)) for event in events]
    
    def chunk_data(data, chunk_size=10):
        return [data[i:i + chunk_size] for i in range(0, len(data), chunk_size)]
    
    app_items = list(obfuscated_apps.items())
    event_items = list(obfuscated_events)    
    app_chunks = chunk_data(app_items, chunk_size=5)  
    event_chunks = chunk_data(event_items, chunk_size=5)

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
        
        Provide a response in the format:
        AppName, Version, Delivery Mechanism, Is WinGet Compatible
        """

        try:
            response = openai.ChatCompletion.create(
                model=os.getenv("LLM_MODEL", "gpt-3.5-turbo"), 
                messages=[{"role": "system", "content": "You are a systems engineer that analyzes System Events and applications."},
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

    return responses

def output_to_csv_from_analysis(openai_responses, filename, base_directory, computer_name):

    print(f"Starting output_to_csv_from_analysis function to write data to {filename}...")       
    header = ['AppName', 'Version', 'Delivery Mechanism', 'Is WinGet Compatible']
    rows = set()  
    
    for response in openai_responses:        
        lines = response.splitlines()
        for line in lines:
            if line.strip():
                app_data = line.split(',')
                if len(app_data) == 4:
                    app_name = app_data[0].strip()
                    version = app_data[1].strip()
                    delivery_mechanism = app_data[2].strip()
                    winget_compatible = app_data[3].strip()
                    rows.add((app_name, version, delivery_mechanism, winget_compatible))
   
    with open(filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(header) 
        writer.writerows(rows)   

    print(f"Data has been written to {filename}")
    generate_reports(filename, base_directory, computer_name)

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

def get_computer_name():    
    computer_name = os.environ.get('COMPUTERNAME') or os.environ.get('HOSTNAME')
    return computer_name

def get_csv_data(file_path):
    data = {}

    try:
        # Attempt to open the file
        with open(file_path, mode='r') as file:
            csv_reader = csv.DictReader(file)
            
            for index, row in enumerate(csv_reader):
                print(f"Row from CSV: {row}")
                
                if 'id' in row:
                    key = row['id']
                else:
                    key = str(index)
                
                data[key] = row

    except FileNotFoundError:
        print(f"Error: The file '{file_path}' was not found.")
    except PermissionError:
        print(f"Error: Permission denied when trying to read '{file_path}'.")
    except csv.Error as e:
        print(f"Error: CSV reading error occurred: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

    return data

# Main function
def main():
    print("Starting main function...")
        
    with concurrent.futures.ThreadPoolExecutor() as executor:
        print("Submitting tasks to the executor...")
        
        base_directory = os.getenv("BASE_DIRECTORY", "D:\\Work\\AppHawk\\Test\\")
        current_date = datetime.now().strftime("%d%m%Y")
        computer_name = get_computer_name()        
        
        installed_apps_events_filename = f"{computer_name}_ApplicationEvents_{current_date}.csv"
        installed_apps_registry_filename = f"{computer_name}_InstalledAppsRegistry_{current_date}.csv"
        installed_apps_wmi_filename = f"{computer_name}_InstalledAppsWMI_{current_date}.csv"
        installed_apps_winget_filename = f"{computer_name}_InstalledAppsWinget_{current_date}.csv"
        
        installed_apps_events_path = os.path.join(base_directory, installed_apps_events_filename)
        installed_apps_registry_path = os.path.join(base_directory, installed_apps_registry_filename)
        installed_apps_wmi_path = os.path.join(base_directory, installed_apps_wmi_filename)
        installed_apps_winget_path = os.path.join(base_directory, installed_apps_winget_filename)
        
        installed_apps_events = get_csv_data(installed_apps_events_path)
        installed_apps_registry = get_csv_data(installed_apps_registry_path)
        installed_apps_wmi = get_csv_data(installed_apps_wmi_path)
        installed_apps_winget = get_csv_data(installed_apps_winget_path)
                
        installed_apps = {**installed_apps_registry, **installed_apps_wmi, **installed_apps_winget}
        print(f"Total Installed Apps: {len(installed_apps)}")
        print(f"Total App Events: {len(installed_apps_events)}") 
               
        openai_responses = analyze_with_openai(installed_apps, installed_apps_events)
        print(f"OpenAI Analysis Responses: {openai_responses}")
                
        output_path = os.path.join(base_directory, f"AnalysersData\\{computer_name}_output_{current_date}.csv") 
        output_to_csv_from_analysis(openai_responses, filename=output_path, base_directory=base_directory, computer_name=computer_name)

    print("Completed main function.")


if __name__ == "__main__":
    main()