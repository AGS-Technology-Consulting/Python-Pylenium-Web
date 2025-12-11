# Pylenium UI Automation Framework

A scalable, modular, and maintainable UI automation framework built using **Python**, **Pylenium**, **Pytest**, and the Page Object Model (POM).  
This framework supports:

- Multi-environment execution  
- Centralized configuration  
- Screenshot capture on failure  
- Reusable Page Objects  
- Logging utilities  
- Test categorization (pass, fail, skip)  
- Reporting (pytest-html / Allure optional)  

---

## 1. Create & Activate Virtual Environment

### Windows
```bash
python -m venv venv
venv\Scripts\activate 
```

### Mac/Linux
```bash
python -m venv venv
source venv/bin/activate
```

## 2. Install Dependencies

After activating the virtual environment:

```bash
pip install -r requirements.txt
```

## 3. Running Tests

Default:
```bash
pytest
```
Run for specific environment:
```bash
pytest --env=qa
```
Run a specific test file:
```bash
pytest tests/e2e/test_login.py
```

Headless Execution:
```bash
pytest --options="headless"
```

# Running Tests with Allure
```bash
1. pytest --alluredir=reports/allure-results
2. allure serve reports/allure-results
```