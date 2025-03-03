# App Hawk

**App Hawk** is an AI-based auditing and reporting tool designed for auditing applications across Windows devices. It uses a modular architecture to collect, obfuscate, analyze, and report on various system details such as installed applications, their versions, installation methods, and compatibility with `winget`. The tool is designed for efficiency, privacy, and scalability.

![image](https://github.com/EzalorIT/App-Hawk/blob/main/Design/ComponentDesign.png)

![image](https://github.com/user-attachments/assets/cfd43110-514b-4d38-978a-75642e6e1e8c)


## Overview

App Hawk is composed of several key components:

1. **Collectors**: PowerShell agents running on client devices to collect data such as:
   - Process logs
   - Application installations
   - WMI queries
   - Registry data
   - `winget` data
   
2. **Processor**: This component obfuscates sensitive data like usernames, passwords, IPs, hostnames, and emails before sending it to the AI model for analysis.

3. **OpenAI LLM Model**: This AI model analyzes the obfuscated data and discovers details about the installed applications, their versions, installation methods, and `winget` compatibility.

4. **Reporting Module**: A Flask-based web application that presents the collected analysis data in HTML reports, indexed by device hostname, with filtering functionality. It also exposes an API to provide consolidated analysis data in JSON format.

## Features

- **AI-Powered App Analysis**: Utilizes OpenAI's LLM for analyzing application data, including detection of installed apps, versions, and installation sources.
- **Data Obfuscation**: Ensures privacy and security by obfuscating sensitive information before processing.
- **HTML and CSV Reports**: Generates per-device reports in HTML format and consolidated analysis in CSV files.
- **Flask Reporting App**: Provides a user-friendly interface to view and filter reports by device hostname.
- **API Access**: Exposes an API endpoint to retrieve analysis data in JSON format.
- **Environment Variables**: Uses environment variables for configuring the base directory, LLM model name, and OpenAI API key.

## Components

### Collectors
PowerShell agents that collect data from client devices across the following sources:
- Process logs
- Application installations
- WMI queries
- Windows Registry
- `winget` data

### Processor
The processor obfuscates sensitive data such as:
- Usernames
- IP addresses
- Hostnames
- Passwords
- Emails

Once obfuscated, the data is sent to the **OpenAI LLM Model** for analysis.

### OpenAI LLM Model
- Analyzes the collected data to identify:
  - Installed apps
  - App versions
  - Installation methods (e.g., winget, manual installation)
  - `winget` compatibility
- Sends the processed data back to the processor over HTTP.

### Reporting Module
- **Web Interface**: A Flask application for viewing indexed and filtered reports in HTML format.
- **API Endpoint**: Provides consolidated output data as JSON for integration with other systems.

## Installation

### Prerequisites

- Python 3.x
- PowerShell (for running collectors on Windows devices)
- OpenAI API key
- Required environment variables set for:
  - Base directory
  - LLM model name
  - OpenAI API key

### Environment Variables
Make sure to set the following environment variables before running the tool:

- `BASE_DIRECTORY`: The base directory for all components.
- `LLM_MODEL_NAME`: The name of the OpenAI model to be used for analysis.
- `OPENAI_API_KEY`: Your OpenAI API key for accessing the LLM model.

### Installation Steps

1. Clone the repository:

   ```bash
   git clone https://github.com/your-username/app-hawk.git
   cd app-hawk
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Set the necessary environment variables:

   ```bash
   export BASE_DIRECTORY=/path/to/base/directory
   export LLM_MODEL_NAME="gpt-3.5-turbo"  # Example model name
   export OPENAI_API_KEY="your-openai-api-key"
   ```

4. Start the reporting server:

   ```bash
   python app_hawk_reporting.py
   ```

5. Run the **Collectors** on your client devices to start collecting data.

6. Once data is collected, the Processor component will obfuscate and send the data for analysis by the OpenAI LLM model.

7. After processing, access the reports through the Flask-based web interface or via the API endpoint.

## Usage

1. **Web Interface**: Access the reports via the Flask app, which will display indexed reports. You can filter by hostname to view device-specific data.

2. **API Access**: Retrieve consolidated analysis data in JSON format by querying the API endpoint:

   ```bash
   GET http://localhost:5000/api/analysis
   ```

## Reporting

- **CSV Output**: The Processor generates a CSV file containing a summary of the analysis, including installed apps, versions, installation sources, and compatibility with `winget`.
- **HTML Output**: For each device, an HTML file is generated with a detailed summary of the analysis, including a table of installed applications, their versions, and installation methods.

## License

App Hawk is licensed under the **GYL Open Source License**. See the [LICENSE](https://github.com/EzalorIT/App-Hawk/blob/main/LICENSE.txt) file for more information.

## Contributing

We welcome contributions to improve App Hawk! If you would like to contribute, please fork the repository, create a branch, and submit a pull request. Make sure to follow our [contribution guidelines](CONTRIBUTING.md).

## Contact

For any inquiries or support, feel free to open an issue in the GitHub repository or contact us at ezalorit@gmail.com

---

We hope App Hawk helps you streamline your Windows device auditing and reporting process, all while maintaining the privacy and security of your sensitive data.
```

This `README.md` file covers installation, usage, components, and features, with a professional and clear structure. It also includes licensing information, contact details, and contribution guidelines, making it suitable for public GitHub repositories.
