# Coding Standards for App Hawk

## 📌 General Guidelines
- Write clean, readable, and maintainable code.
- Follow best practices for each programming language used.
- Ensure code is modular and reusable.
- Document code thoroughly using comments and docstrings.
- Adhere to naming conventions for variables, functions, and files.

---

## 🐍 Python Coding Standards

### 1. Follow PEP 8
- Use spaces instead of tabs (4 spaces per indentation level).
- Limit line length to 79 characters.
- Use meaningful variable and function names.
- Use docstrings for functions and classes.

### 2. Code Structure
- Organize imports:
  ```python
  import os
  import sys
  from datetime import datetime
  ```
- Separate functions and classes with two blank lines.
- Keep function lengths reasonable (max 50 lines if possible).

### 3. Type Hints
Use type hints for function parameters and return values:
```python
 def add_numbers(a: int, b: int) -> int:
     return a + b
```

### 4. Exception Handling
- Use specific exception types instead of generic `except Exception:`
  ```python
  try:
      result = 10 / 0
  except ZeroDivisionError as e:
      print(f"Error: {e}")
  ```

### 5. Logging Instead of Print Statements
Use `logging` for debugging and error tracking:
```python
import logging
logging.basicConfig(level=logging.INFO)
logging.info("This is an informational message")
```

### 6. Testing and Linting
- Use `pytest` for unit tests.
- Run `flake8` or `black` for linting:
  ```bash
  flake8 app.py
  black app.py
  ```

---

## 💻 PowerShell Coding Standards

### 1. General Guidelines
- Use camelCase for variables.
- Use PascalCase for function names.
- Add comments using `#` for clarity.

### 2. Script Structure
- Use consistent indentation (4 spaces per level).
- Begin scripts with `param` block for user inputs.
  ```powershell
  param(
      [string]$FilePath,
      [int]$Count = 10
  )
  ```

### 3. Functions and Modules
- Define functions with proper parameter validation:
  ```powershell
  function Get-UserInfo {
      param (
          [string]$UserName
      )
      Write-Output "Fetching info for $UserName"
  }
  ```

### 4. Error Handling
- Use `Try-Catch` blocks to handle errors:
  ```powershell
  try {
      Get-Item "C:\NonExistentFile.txt"
  } catch {
      Write-Error "File not found!"
  }
  ```

### 5. Formatting and Best Practices
- Use meaningful variable names:
  ```powershell
  $userList = Get-ADUser -Filter *
  ```
- Avoid hardcoded values; use variables and parameters.
- Run `PSScriptAnalyzer` to check for best practices:
  ```powershell
  Invoke-ScriptAnalyzer -Path .\myscript.ps1
  ```

---

## ✅ Code Review Checklist
- [ ] Code follows the respective language’s best practices.
- [ ] No hardcoded values or sensitive information.
- [ ] Includes proper comments and documentation.
- [ ] Handles exceptions properly.
- [ ] Has tests written and passing.

By following these standards, we ensure high-quality, maintainable, and secure code for **App Hawk**! 🚀

