# FairScore Setup Guide - Cross-Platform (Windows, Mac, Linux)

This guide covers first-time setup for all operating systems.

## Prerequisites

- **Python 3.11+** (download from [python.org](https://www.python.org/downloads/))
- **Node.js 18+** (download from [nodejs.org](https://nodejs.org/))
- **Git** (optional, for cloning the repo)

## Quick Start (All Platforms)

### 1. Clone/Extract Project
```bash
cd Desktop
git clone <repository-url> project
cd project
```

### 2. Create Python Virtual Environment

**Windows (PowerShell or Command Prompt):**
```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**macOS/Linux (Bash/Zsh):**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Configure Environment Variables
```bash
# Copy the example .env file
cp .env.example .env
# OR just copy in your file explorer

# Edit .env and add your Supabase credentials
# Open .env in your editor and fill in:
# SUPABASE_URL=...
# SUPABASE_SERVICE_ROLE_KEY=...
```

### 4. Start Everything
```bash
python scripts/bootstrap_and_run.py
```

This will:
- Install all Python dependencies (FastAPI, Supabase, ML libraries, etc.)
- Install all Node dependencies
- Check for model artifacts
- Start both backend and frontend

**Output:**
```
Backend:  http://0.0.0.0:8000
Frontend: http://0.0.0.0:5173
```

Press **Ctrl+C** once to stop both services.

---

## Detailed Setup by OS

### macOS Setup

1. **Install Python 3.11+ (if not already installed):**
   ```bash
   # Using Homebrew (recommended)
   brew install python@3.11
   
   # Verify installation
   python3 --version
   ```

2. **Install Node.js:**
   ```bash
   brew install node
   node --version
   ```

3. **Create virtual environment:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

4. **For M1/M2 Macs:** Some packages may require special handling:
   ```bash
   # If you encounter issues with PyTorch/SHAP, use:
   ARCHFLAGS=-Qunused-arguments CPPFLAGS=-QunusedArguments python scripts/bootstrap_and_run.py
   ```

### Windows Setup

1. **Open PowerShell as Administrator** and run:
   ```powershell
   py -3.11 -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

   *If you get an execution policy error:*
   ```powershell
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
   ```

2. **Run bootstrap:**
   ```powershell
   python scripts/bootstrap_and_run.py
   ```

### Linux Setup

1. **Install Python and Node:**
   ```bash
   sudo apt-get update
   sudo apt-get install python3.11 python3.11-venv nodejs npm
   ```

2. **Create virtual environment:**
   ```bash
   python3.11 -m venv .venv
   source .venv/bin/activate
   ```

3. **Run bootstrap:**
   ```bash
   python scripts/bootstrap_and_run.py
   ```

---

## Handling Missing Model Artifacts

If prediction endpoints fail, you need to train the models:

```bash
# With the venv activated:
python backend/models/preprocessing.py
python backend/models/random_forest.py
python backend/models/lightgbm_model.py
python backend/models/tab_transformer.py
python backend/models/stacked_ensemble.py
```

Or use the flag on startup:
```bash
python scripts/bootstrap_and_run.py --train-missing-models
```

**Note:** Training may take 5-10 minutes. For M1/M2 Macs and Linux ARM devices, read "Special Considerations" below.

---

## Common Issues & Troubleshooting

### Issue: `python` command not found

**Solution:** Use `python3` instead (common on macOS/Linux):
```bash
python3 scripts/bootstrap_and_run.py
```

Or use the explicit venv path:
```bash
.venv/bin/python scripts/bootstrap_and_run.py
```

### Issue: Virtual environment not activating

**Windows (PowerShell):**
```powershell
# Make sure you're in the project root first
cd c:\path\to\project
.\.venv\Scripts\Activate.ps1
```

**macOS/Linux:**
```bash
source .venv/bin/activate
# Verify with: which python
```

### Issue: `Permission denied` on macOS/Linux

**Solution:** Grant execute permission:
```bash
chmod +x .venv/bin/activate
```

### Issue: Port 8000 or 5173 already in use

**Solution:** Use custom ports:
```bash
python scripts/bootstrap_and_run.py --backend-port 9000 --frontend-port 5174
```

### Issue: `pip install` fails with compilation errors

**macOS:**
```bash
# Install build tools first
xcode-select --install
brew install libffi openssl
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get install build-essential python3-dev libffi-dev libssl-dev
```

**Windows:**
- Download and install Visual Studio C++ Build Tools

---

## Special Considerations

### M1/M2 Mac Users

Some ML libraries may need special installation. If you encounter errors:

```bash
# Activate venv first
source .venv/bin/activate

# Install with architecture-specific flags
ARCHFLAGS=-Qunused-arguments CPPFLAGS=-QunusedArguments pip install -r requirements.txt
ARCHFLAGS=-Qunused-arguments CPPFLAGS=-QunusedArguments pip install -r backend/requirements.txt
```

### ARM Linux (Raspberry Pi, etc.)

Some packages like PyTorch may not be available pre-compiled. You may need:
```bash
# Use pre-built wheels or compile from source
pip install --upgrade pip setuptools wheel
```

### Docker (Cross-platform solution)

If you want guaranteed compatibility, use Docker:

```bash
# Create a Dockerfile in the project root
docker build -t fairscore .
docker run -p 8000:8000 -p 5173:5173 fairscore
```

---

## Deactivating Virtual Environment

When done developing:

**Windows:**
```powershell
deactivate
```

**macOS/Linux:**
```bash
deactivate
```

---

## Next Steps

1. Add your Supabase credentials to `.env`
2. Run `python scripts/bootstrap_and_run.py`
3. Open http://localhost:5173 in your browser
4. Start developing!

For API documentation, visit http://localhost:8000/docs after startup.

---

## Getting Help

- **Backend API**: http://localhost:8000/docs (FastAPI Swagger)
- **Backend Logs**: Check the terminal output
- **Frontend Logs**: Check the browser console (F12)
