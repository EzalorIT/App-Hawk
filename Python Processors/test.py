import re
import json
import os
import csv
import concurrent.futures
import pandas as pd
import sys
import time
import openai
import tiktoken
from datetime import datetime
from cryptography.fernet import Fernet

# Set Base Directory
base_directory = os.getenv("BASE_DIRECTORY", "D:\\Work\\AppHawk\\Test\\")
ENABLE_AI_ANALYSIS = os.getenv("ENABLE_AI_ANALYSIS", "False").lower() == "true"

if not os.path.exists(base_directory):
    print(f"❌ Base directory {base_directory} does not exist.")
    exit(1)

# Load Encryption Key
key_path = os.path.join(base_directory, "Vault\\secret.key")
encrypted_key_path = os.path.join(base_directory, "Vault\\encrypted_openai_key.txt")

try:
    with open(key_path, "rb") as key_file:
        key = key_file.read()

    cipher_suite = Fernet(key)
    with open(encrypted_key_path, "rb") as enc_file:
        encrypted_api_key = enc_file.read()

    openai_api_key = cipher_suite.decrypt(encrypted_api_key).decode()
    openai.api_key = openai_api_key
    print("✅ API key successfully decrypted.")
except Exception as e:
    print(f"❌ Error retrieving or decrypting API key: {e}")
    exit(1)

# Function to Read CSV Data
def get_csv_data(file_path):
    data = {}

    try:
        with open(file_path, mode='r', encoding='utf-8') as file:
            csv_reader = csv.DictReader(file)
            for index, row in enumerate(csv_reader):
                key = row.get('id', str(index))
                data[key] = row
    except FileNotFoundError:
        print(f"❌ Error: The file '{file_path}' was not found.")
    except PermissionError:
        print(f"❌ Error: Permission denied when reading '{file_path}'.")
    except csv.Error as e:
        print(f"❌ CSV reading error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

    return data

# Function to Obfuscate Sensitive Info
def obfuscate_sensitive_info(data):
    product_pattern = re.compile(r"Product Name:\s*(?P<product>.+?)\.\s*Product Version:\s*(?P<version>[\d.]+)", re.IGNORECASE)
    extracted_data = []

    if isinstance(data, dict):
        message = data.pop("Message", None)
        if message:
            matches = product_pattern.findall(message)
            extracted_data = [{"product": match[0], "version": match[1]} for match in matches]

    elif isinstance(data, list):
        for item in data:
            result = obfuscate_sensitive_info(item)
            if result:
                extracted_data.extend(result if isinstance(result, list) else [result])

    return extracted_data if extracted_data else []  # Ensure it always returns a list

# Token Counting
def count_tokens(text):
    encoding = tiktoken.encoding_for_model(os.getenv("LLM_MODEL", "gpt-3.5-turbo"))
    return len(encoding.encode(text))

# Chunk Data
def chunk_data_dynamic(data, max_tokens=4096):
    chunks = []
    current_chunk = []
    current_token_count = 0
    
    for item in data:
        item_text = json.dumps(item, indent=2)
        item_tokens = count_tokens(item_text)

        if current_token_count + item_tokens > max_tokens:
            chunks.append(current_chunk)
            current_chunk = []
            current_token_count = 0

        current_chunk.append(item)
        current_token_count += item_tokens

    if current_chunk:
        chunks.append(current_chunk)

    return chunks

# AI Analysis
def analyze_with_openai_chunked(installed_apps, events):
    raw_events_path = os.path.join(base_directory, "AnalysersData", "events_raw.csv")
    pd.DataFrame(list(events.values())).to_csv(raw_events_path, index=False)
    print(f"✅ Raw events saved at {raw_events_path}")

    obfuscated_events = obfuscate_sensitive_info(events)

    event_items = []
    for sublist in obfuscated_events:
        if isinstance(sublist, list):
            event_items.extend(sublist)
        elif isinstance(sublist, dict):
            event_items.append(sublist)

    event_items_path = os.path.join(base_directory, "AnalysersData", "event_items_obfuscated.csv")
    if event_items:
        pd.DataFrame(event_items).to_csv(event_items_path, index=False)
        print(f"✅ Obfuscated events saved at {event_items_path}")
    else:
        print("⚠ Warning: No valid event data found!")

    app_chunks = chunk_data_dynamic(list(installed_apps.values()), max_tokens=4096)
    event_chunks = chunk_data_dynamic(event_items, max_tokens=4096)

    responses = []
    for app_chunk, event_chunk in zip(app_chunks, event_chunks):
        prompt = f"""
        You are an AI that analyzes system event logs and installed applications.
        **Installed Applications:** {json.dumps(app_chunk, indent=2)}
        **Event Logs:** {json.dumps(event_chunk, indent=2)}
        """
        try:
            if ENABLE_AI_ANALYSIS:
                response = openai.ChatCompletion.create(
                    model=os.getenv("LLM_MODEL", "gpt-3.5-turbo"), 
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=4000,
                    temperature=0.2
                )
                responses.append(response['choices'][0]['message']['content'])
        except Exception as e:
            print(f"❌ Error analyzing chunk with OpenAI: {e}")

    return "\n".join(responses)

# Write Output CSV
def output_to_csv(ai_generated_csv, filename):
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    if ai_generated_csv.strip():
        with open(filename, mode='w', encoding='utf-8') as file:
            file.write(ai_generated_csv.strip())
        print(f"✅ Output saved: {filename}")

# Get Computer Name
def get_computer_name():
    return os.environ.get('COMPUTERNAME') or os.environ.get('HOSTNAME')

# Merge CSV Files
def merge_csv_files(base_directory, computer_name):
    files = ["ApplicationEvents", "InstalledAppsRegistry", "InstalledAppsWMI", "InstalledAppsWinget", "RunningProcesses"]
    dataframes = []

    for file in files:
        path = os.path.join(base_directory, "CollectorsData", f"{computer_name}_{file}.csv")
        if os.path.exists(path):
            df = pd.read_csv(path, encoding='utf-8', on_bad_lines='skip')
            df.columns = df.columns.str.lower().str.strip()
            df.rename(columns={"appname": "name", "applicationname": "name", "appversion": "version", "applicationversion": "version"}, inplace=True)
            dataframes.append(df)

    merged_data = pd.concat(dataframes, ignore_index=True)
    return merged_data.drop_duplicates(subset=['name', 'version'], keep='first')

# Main Function
def main():
    print("🚀 Starting analysis...")

    computer_name = get_computer_name()
    merged_data = merge_csv_files(base_directory, computer_name)

    if merged_data.empty:
        print("❌ Error: No application data found.")
        return

    installed_apps = merged_data.to_dict(orient='index')
    installed_apps_events = get_csv_data(os.path.join(base_directory, "CollectorsData", f"{computer_name}_ApplicationEvents.csv"))

    output_csv_path = os.path.join(base_directory, "AnalysersData", f"{computer_name}_output.csv")
    
    if ENABLE_AI_ANALYSIS:
        responses = analyze_with_openai_chunked(installed_apps, installed_apps_events)
    else:
        responses = "AI analysis disabled."

    output_to_csv(responses, output_csv_path)
    print("✅ Analysis complete.")

if __name__ == "__main__":
    main()
