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
import tiktoken

base_directory = os.getenv("BASE_DIRECTORY", "D:\\Work\\AppHawk\\Test\\")
ENABLE_AI_ANALYSIS = os.getenv("ENABLE_AI_ANALYSIS", "False").lower() == "true"

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

import re

def obfuscate_sensitive_info(data):
    """Extracts Product Name and Version, removes unnecessary fields, and ensures structured output."""
    product_pattern = re.compile(
        r"Product Name:\s*(?P<product>.+?)\.\s*Product Version:\s*(?P<version>[\d.]+)", re.IGNORECASE
    )

    if isinstance(data, dict):
        message = data.pop("Message", None)  # Remove the Message key

        if message:
            # Debug: Print extracted message before processing
            print("🔍 Processing Message:", message)

            # Extract Product Name and Version
            matches = product_pattern.findall(message)
            extracted_data = [{"product": match[0], "version": match[1]} for match in matches]

            # Debug: Print extracted data
            print("✅ Extracted Data:", extracted_data)

            return extracted_data if extracted_data else None  # Return structured data only

        return None  # Ignore logs without product details

    elif isinstance(data, list):
        # Debug: Print before processing
        print("🔍 Processing List of Events:", data[:3])

        clean_data = []
        for item in data:
            result = obfuscate_sensitive_info(item)
            if result:
                if isinstance(result, list):
                    clean_data.extend(result)
                else:
                    clean_data.append(result)

        # Debug: Print extracted events
        print("✅ Cleaned Event Data:", clean_data[:3])

        return clean_data

    return None  # Ignore non-relevant data




def count_tokens(text):
    encoding = tiktoken.encoding_for_model(os.getenv("LLM_MODEL", "gpt-3.5-turbo"))
    return len(encoding.encode(text))

def chunk_data_dynamic(data, max_tokens=4096):  
    chunks = []
    current_chunk = []
    current_token_count = 0
    
    for item in data:
        item_text = json.dumps(item, indent=2) 
        item_tokens = count_tokens(item_text) 
        
        if item_tokens > max_tokens:
            print(f"Warning: Single item too large ({item_tokens} tokens). Truncating data.")
            item_text = item_text[:max_tokens]
            item_tokens = count_tokens(item_text)
                
        if current_token_count + item_tokens > max_tokens:
            chunks.append(current_chunk)
            current_chunk = []
            current_token_count = 0

        current_chunk.append(item)
        current_token_count += item_tokens
    
    if current_chunk:
        chunks.append(current_chunk)

    print(f"Total Chunks Created: {len(chunks)}")
    return chunks

def analyze_with_openai_chunked(installed_apps, events):   
    # Debug: Export raw events before obfuscation
    raw_events_path = os.path.join(base_directory, "AnalysersData", "events_raw.csv")
    pd.DataFrame(list(events.values())).to_csv(raw_events_path, index=False)
    print(f"✅ Raw events saved at {raw_events_path}")

    # Ensure obfuscated_events is always a list
    obfuscated_events = obfuscate_sensitive_info(events) or []

    # Debug: Print sample obfuscated events before processing
    print("🔍 Sample Obfuscated Events:", obfuscated_events[:5])

    # Ensure valid structured list
    event_items = []
    for sublist in (obfuscated_events if isinstance(obfuscated_events, list) else [obfuscated_events]):
        if isinstance(sublist, list):
            event_items.extend(sublist)
        elif isinstance(sublist, dict):
            event_items.append(sublist)

    # Debug: Ensure valid event items exist
    if not event_items:
        print("⚠ Warning: No valid event items found after obfuscation!")

    # Export structured event items
    event_items_path = os.path.join(base_directory, "AnalysersData", "event_items_obfuscated.csv")
    if event_items:
        pd.DataFrame(event_items).to_csv(event_items_path, index=False)
        print(f"✅ Obfuscated events saved at {event_items_path}")
    else:
        print(f"⚠ No obfuscated event data found, empty file at {event_items_path}")

    # Process installed apps
    app_items = list(installed_apps.values())
    app_items_df = pd.DataFrame(app_items)
    app_items_df.to_csv(os.path.join(base_directory, "AnalysersData", "app_items_obfuscated.csv"), index=False)

    # Debug: Print sample structured event items before chunking
    print("🔍 Sample Structured Event Items:", event_items[:5])

    # Chunk data
    app_chunks = chunk_data_dynamic(app_items, max_tokens=4096)
    event_chunks = chunk_data_dynamic(event_items, max_tokens=4096)

    responses = []

    for app_chunk, event_chunk in zip(app_chunks, event_chunks):        
        prompt = f"""
        You are an AI that analyzes system event logs and installed applications.
        
        Please analyze the following input csv and figure out if each application is winget compatible by checking winget catalog and return the results **strictly in CSV format**.
        Retain app names from original data and merge discovered apps from event logs. Do not skip any MSIX or MSI installations. The count of apps in output should be > the input count.    
        In the events logs use intelligence to discover any new application not in the input and merge it with the final response in the same format and analysis for winget. 
        Do not skip any app from original input csv
        
        **Installed Applications:**
        {json.dumps(app_chunk, indent=2)}

        **Event Logs:**
        {json.dumps(event_chunk, indent=2)}

        ---
        **Output Format (CSV only, no explanation, no extra text):**
        
        ```
        "AppName","Version","Delivery Mechanism","Is WinGet Compatible"
        "Google Chrome","114.0.5735.110","Installer","Yes"
        "Visual Studio Code","1.75.1","Winget","Yes"
        ```

        - **Every value must be enclosed in double quotes (`"`)** to handle commas properly.
        - **Do not include extra text** before or after the CSV output.
        - **Strictly follow the format without errors.**
        """

        try:
            if ENABLE_AI_ANALYSIS:
                response = openai.ChatCompletion.create(
                    model=os.getenv("LLM_MODEL", "gpt-3.5-turbo"), 
                    messages=[{"role": "system", "content": "You are an AI that processes and returns structured CSV data."},
                            {"role": "user", "content": prompt}],
                    max_tokens=4000,  
                    temperature=0.2
                )
                
                if 'choices' in response and len(response['choices']) > 0:
                    csv_content = response['choices'][0]['message']['content']
                    responses.append(csv_content)
                else:
                    print("⚠ Error: AI did not return structured CSV data.")
                    responses.append("Error: No content found.")
        except Exception as e:
            print(f"❌ Error analyzing chunk with OpenAI: {e}")
            responses.append(f"Error analyzing chunk: {e}")

    return "\n".join(responses)





def output_to_csv_from_analysis(ai_generated_csv, filename, base_directory, computer_name):
    """
    Writes AI-generated CSV data to a file, ensuring proper structure.
    """
    print(f"Writing AI-generated CSV data to {filename}...")  

    if not ai_generated_csv.strip():
        print("Warning: AI-generated CSV is empty.")
        return

    # Ensure output directory exists
    os.makedirs(os.path.dirname(filename), exist_ok=True)

    # Save AI-generated CSV ensuring UTF-8 encoding
    with open(filename, mode='w', newline='', encoding='utf-8') as file:
        file.write(ai_generated_csv.strip())

    print(f"✅ AI-generated data successfully saved to {filename}.")


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

def merge_csv_files(base_directory, computer_name):
    """Reads and merges all CSV data before processing."""
    installed_apps_events_path = os.path.join(base_directory, "CollectorsData", f"{computer_name}_ApplicationEvents.csv")
    installed_apps_registry_path = os.path.join(base_directory, "CollectorsData", f"{computer_name}_InstalledAppsRegistry.csv")
    installed_apps_wmi_path = os.path.join(base_directory, "CollectorsData", f"{computer_name}_InstalledAppsWMI.csv")
    installed_apps_winget_path = os.path.join(base_directory, "CollectorsData", f"{computer_name}_InstalledAppsWinget.csv")
    running_processes_path = os.path.join(base_directory, "CollectorsData", f"{computer_name}_RunningProcesses.csv")

    # Define a helper function to load CSV safely
    def load_csv(file_path):
        if os.path.exists(file_path):
            try:
                return pd.read_csv(file_path, encoding='utf-8')
            except UnicodeDecodeError:
                return pd.read_csv(file_path, encoding='latin1')
        else:
            print(f"Warning: {file_path} not found.")
            return pd.DataFrame()  


    df_installed_apps_events = load_csv(installed_apps_events_path)
    df_installed_apps_registry = load_csv(installed_apps_registry_path)
    df_installed_apps_wmi = load_csv(installed_apps_wmi_path)
    df_installed_apps_winget = load_csv(installed_apps_winget_path)
    df_running_processes = load_csv(running_processes_path)

    for df in [df_installed_apps_events, df_installed_apps_registry, df_installed_apps_wmi, df_installed_apps_winget, df_running_processes]:
        df.columns = df.columns.str.strip().str.lower()  # Normalize column names

        # Rename important columns
        column_mappings = {
            "appname": "name",
            "applicationname": "name",
            "appversion": "version",
            "applicationversion": "version"
        }
        df.rename(columns=column_mappings, inplace=True)
        
        if 'name' not in df.columns:
            df['name'] = None
        if 'version' not in df.columns:
            df['version'] = None

    # Merge all data
    merged_data = pd.concat([df_installed_apps_registry, df_installed_apps_wmi, df_installed_apps_winget, df_running_processes], ignore_index=True)

    if merged_data.empty:
        raise ValueError("Merged data is empty. Ensure CSV files contain valid data.")

    print(f"Merged data columns: {merged_data.columns}")

    return merged_data

def get_csv_data(file_path):
    data = {}

    try:
        with open(file_path, mode='r', encoding='utf-8') as file:
            csv_reader = csv.DictReader(file)
            for index, row in enumerate(csv_reader):
                data[str(index)] = row  # Using row index as the key
    except FileNotFoundError:
        print(f"❌ Error: The file '{file_path}' was not found.")
    except PermissionError:
        print(f"❌ Error: Permission denied when reading '{file_path}'.")
    except csv.Error as e:
        print(f"❌ CSV reading error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

    return data

# Main function
def main():
    print("Starting main function...")
        
    with concurrent.futures.ThreadPoolExecutor() as executor:
        print("Submitting tasks to the executor...")
        
        base_directory = os.getenv("BASE_DIRECTORY", "D:\\Work\\AppHawk\\Test\\")
        current_date = datetime.now().strftime("%d%m%Y")
        computer_name = get_computer_name()        
        
        installed_apps_events_filename = f"{computer_name}_ApplicationEvents.csv"
        #installed_apps_registry_filename = f"{computer_name}_InstalledAppsRegistry.csv"
        #installed_apps_wmi_filename = f"{computer_name}_InstalledAppsWMI.csv"
        #installed_apps_winget_filename = f"{computer_name}_InstalledAppsWinget.csv"
        #running_processes_filename = f"{computer_name}_RunningProcesses.csv"
        
        installed_apps_events_path = os.path.join(base_directory,"CollectorsData",installed_apps_events_filename)
        #installed_apps_registry_path = os.path.join(base_directory,"CollectorsData", installed_apps_registry_filename)
        #installed_apps_wmi_path = os.path.join(base_directory, "CollectorsData",  installed_apps_wmi_filename)
        #installed_apps_winget_path = os.path.join(base_directory, "CollectorsData",  installed_apps_winget_filename)
        #running_processes_path = os.path.join(base_directory, "CollectorsData", running_processes_filename)
        
        installed_apps_events = get_csv_data(installed_apps_events_path)
        #installed_apps_registry = get_csv_data(installed_apps_registry_path)
        #installed_apps_wmi = get_csv_data(installed_apps_wmi_path)
        #installed_apps_winget = get_csv_data(installed_apps_winget_path)
        #running_processes = get_csv_data(running_processes_path)      
        
        # Merge CSV data before processing
        merged_data = merge_csv_files(base_directory, computer_name)

        # Drop duplicates based on Name and Version
        if 'name' in merged_data.columns and 'version' in merged_data.columns:
            deduplicated_data = merged_data.drop_duplicates(subset=['name', 'version'], keep='first')
        else:
            raise KeyError("Columns 'Name' and 'Version' not found in the merged data.")

        print(f"Total unique applications: {len(deduplicated_data)}")

        # Convert to dictionary for further analysis
        installed_apps = deduplicated_data.to_dict(orient='index')      

        print(f"Total Installed Apps: {len(installed_apps)}")
        print(f"Total App Events: {len(installed_apps_events)}")         
        
        # Output installed apps as csv 
        deduplicated_data.to_csv(os.path.join(base_directory, f"AnalysersData\\{computer_name}_all_installed_apps_{current_date}.csv"), index=False)
        
        # IF USE AI                 
        if True:
            #responses = analyze_with_openai(installed_apps, installed_apps_events)
            responses = analyze_with_openai_chunked(installed_apps, installed_apps_events)
            print(f"OpenAI Analysis Responses: {responses}")
        # ELSE USE PYTHON ANALYSIS
        else:
            print("Skipping OpenAI analysis. Starting Pandas-based analysis...")
            responses = []         
            
        output_path = os.path.join(base_directory, f"AnalysersData\\{computer_name}_output_{current_date}.csv") 
        output_to_csv_from_analysis(responses, filename=output_path, base_directory=base_directory, computer_name=computer_name)

    print("Completed main function.")


if __name__ == "__main__":
    main()