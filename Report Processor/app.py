from flask import Flask, render_template, request, send_from_directory, jsonify
import os
import pandas as pd
from io import StringIO

app = Flask(__name__)

base_directory = os.getenv("BASE_DIRECTORY", "D:\\Work\\AppHawk\\Test\\")
REPORTS_DIR = os.path.join(base_directory, 'ReportingData')
CSV_DIR = os.path.join(base_directory, 'AnalysersData')  # Assuming the CSV files are stored in a directory called 'CSVData'

# Function to get all report filenames
def get_reports():
    return [f for f in os.listdir(REPORTS_DIR) if f.endswith('.html')]

# Function to get all CSV filenames
def get_csv_files():
    return [f for f in os.listdir(CSV_DIR) if f.endswith('.csv')]

# Function to consolidate CSV files into a single DataFrame and return it as JSON
def consolidate_csv():
    csv_files = get_csv_files()
    all_data = []

    for csv_file in csv_files:
        file_path = os.path.join(CSV_DIR, csv_file)
        data = pd.read_csv(file_path)
        all_data.append(data)

    # Concatenate all dataframes into one
    consolidated_data = pd.concat(all_data, ignore_index=True)

    # Return the consolidated data as JSON
    return consolidated_data.to_dict(orient='records')

# Route to serve the reports
@app.route('/reports/<filename>')
def serve_report(filename):
    # Ensure the filename is secure to prevent path traversal attacks
    safe_filename = os.path.basename(filename)
    return send_from_directory(REPORTS_DIR, safe_filename)

@app.route('/api', methods=['GET'])
def get_consolidated_csv():
    # Generate the consolidated data in JSON format
    consolidated_data = consolidate_csv()

    # Return the consolidated data as JSON
    return jsonify(consolidated_data)

@app.route('/')
def index():
    # Get all reports
    reports = get_reports()
    
    # Get filter parameters from query string (hostname filter)
    filter_hostname = request.args.get('hostname')
    
    # Apply hostname filter (if any)
    if filter_hostname:
        reports = [report for report in reports if filter_hostname in report]
    
    return render_template('index.html', reports=reports)

if __name__ == "__main__":
    app.run(debug=True)
