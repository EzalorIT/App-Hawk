# Contributing to App Hawk

Thank you for considering contributing to **App Hawk**! We welcome contributions from the community to help improve and expand the project. Please read this guide to understand how to contribute.

## 📌 Getting Started

1. **Fork the Repository**: Click the "Fork" button on GitHub to create your own copy of the repository.
2. **Clone the Repository**: Clone the forked repository to your local machine using:
   ```bash
   git clone https://github.com/your-username/app-hawk.git
   cd app-hawk
   ```
3. **Set Up the Environment**:
   - Install dependencies:
     ```bash
     pip install -r requirements.txt
     ```
   - Set up environment variables (see `README.md`).

## 🛠 Contributing Guidelines

### 1. Reporting Issues
If you find a bug, security vulnerability, or have a feature request:
- Check if it has already been reported in the [Issues](https://github.com/EzalorIT/app-hawk/issues) section.
- If not, create a **detailed issue report**, including:
  - A clear and descriptive title.
  - Steps to reproduce the issue.
  - Expected vs. actual behavior.
  - Logs or screenshots if applicable.

### 2. Submitting Code Changes
#### 📌 Before You Start
- Ensure your changes align with the project's scope and goals.
- Create a **feature branch** before making changes:
  ```bash
  git checkout -b feature-branch-name
  ```
- Make sure your code follows the best practices outlined in the [Coding Standards](https://github.com/EzalorIT/App-Hawk/blob/main/CODINGSTANDARDS.md).

#### ✨ Making a Pull Request (PR)
1. **Commit your changes**:
   ```bash
   git add .
   git commit -m "Brief description of changes"
   git push origin feature-branch-name
   ```
2. Open a **Pull Request (PR)** to the `main` branch.
3. Provide a clear **title and description** of your changes.
4. Reference any related issues (e.g., `Closes #123`).
5. Wait for a maintainer to review and provide feedback.

### 3. Coding Standards
- Follow **PEP 8** style guide for Python.
- Keep code modular and well-documented.
- Use meaningful variable and function names.
- Add comments where necessary for clarity.
- Run tests before submitting PRs.
- Refer to detailed coding standards https://github.com/EzalorIT/App-Hawk/blob/main/CODINGSTANDARDS.md

### 4. Writing Tests
- We use `pytest` for testing.
- Run existing tests before submitting PRs:
  ```bash
  pytest
  ```
- If you add new functionality, add corresponding test cases.

## 📜 Licensing
By contributing to **App Hawk**, you agree that your contributions will be licensed under the [GYL License](https://github.com/EzalorIT/App-Hawk/blob/main/LICENSE.txt).

## 📧 Need Help?
For questions, feel free to open a [Discussion](https://github.com/EzalorIT/app-hawk/discussions) or contact the maintainers via GitHub Issues.

Happy Coding! 🚀

