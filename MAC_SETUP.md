# macOS-Specific Setup Guide

This guide covers everything you need to run FairScore on Mac (Intel & M1/M2/M3).

## Prerequisites Check

```bash
# Check Python version
python3 --version

# Check Node version  
node --version
npm --version
```

If any are missing, see "Installation" section below.

---

## Quick Start (5 minutes)

### Step 1: Clone the Project
```bash
git clone <repository-url> fairscore
cd fairscore
```

### Step 2: Create Virtual Environment
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Step 3: Configure Supabase Credentials
```bash
cp .env.example .env
# Edit .env and add your Supabase URL and key
nano .env  # or use VS Code
```

### Step 4: Run Everything
```bash
python scripts/bootstrap_and_run.py
```

That's it! Open http://localhost:5173 in your browser.

---

## Installation (If Needed)

### Install Python 3.11+

**Using Homebrew (Recommended):**
```bash
brew install python@3.11
```

**Using Python.org (Alternative):**
1. Download from https://www.python.org/downloads/macos/
2. Run the installer
3. Verify: `python3 --version`

### Install Node.js 18+

**Using Homebrew:**
```bash
brew install node
```

**Using NodeSource (Alternative):**
```bash
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs
```

### Install Xcode Command Line Tools (Required for compilation)

```bash
xcode-select --install
```

This is needed for packages like SHAP, LightGBM that compile native code.

---

## Troubleshooting macOS Issues

### Issue: "python3: command not found"

**Solution 1:** Use Homebrew's Python
```bash
brew install python@3.11
# Then add to ~/.zshrc or ~/.bash_profile:
alias python3=/usr/local/bin/python3
```

**Solution 2:** Use the full path
```bash
/usr/local/bin/python3 scripts/bootstrap_and_run.py
```

### Issue: "pip: command not found" after creating venv

**Solution:**
```bash
# Make sure venv is activated
source .venv/bin/activate

# Verify python points to venv
which python

# Upgrade pip
python -m pip install --upgrade pip
```

### Issue: M1/M2 Mac - PyTorch/SHAP installation fails

**Solution:** Use architecture-specific flags

```bash
source .venv/bin/activate
ARCHFLAGS=-Qunused-arguments CPPFLAGS=-QunusedArguments pip install -r requirements.txt
ARCHFLAGS=-Qunused-arguments CPPFLAGS=-QunusedArguments pip install -r backend/requirements.txt
```

Or add to your shell profile permanently:
```bash
# Add to ~/.zshrc (default on macOS)
export ARCHFLAGS=-Qunused-arguments
export CPPFLAGS=-QunusedArguments
```

### Issue: Port 8000 or 5173 already in use

**Solution 1:** Stop the process using the port
```bash
# Find what's using port 8000
lsof -i :8000
# Kill it by PID
kill -9 <PID>
```

**Solution 2:** Use different ports
```bash
python scripts/bootstrap_and_run.py --backend-port 9000 --frontend-port 5174
```

### Issue: "Permission denied" errors

**Solution:**
```bash
# Grant execute permissions
chmod -R +x .venv/bin
chmod +x scripts/bootstrap_and_run.py
```

### Issue: Dependency installation hangs

**Solution:** Check your network and try:
```bash
pip install --default-timeout=100 -r requirements.txt
```

---

## Optional: Using Docker (Guaranteed Compatibility)

If you encounter persistent issues, Docker provides a guaranteed working environment:

```bash
# Build the image (one-time)
docker build -t fairscore .

# Run the container
docker run -p 8000:8000 -p 5173:5173 fairscore
```

**Note:** Docker is optional and mainly useful if you hit compilation issues.

---

## Development Workflow

### Start Development
```bash
# Make sure you're in the project root
source .venv/bin/activate
python scripts/bootstrap_and_run.py
```

### Deactivate Virtual Environment
```bash
deactivate
```

### Update Dependencies
```bash
source .venv/bin/activate
pip install --upgrade -r requirements.txt
pip install --upgrade -r backend/requirements.txt
cd frontend && npm install
```

### Check for Issues
```bash
# Backend logs
# (visible in the terminal where bootstrap runs)

# Frontend issues  
# (visible in VS Code's Problems panel or browser console)
```

---

## FAQ

**Q: Should I commit the `.venv` folder?**
A: No. Add to `.gitignore` (usually already done). Users will create their own venv.

**Q: How do I use VS Code with this project?**
A: 
1. Open the project folder in VS Code
2. Select Python interpreter: `View > Command Palette > Python: Select Interpreter`
3. Choose `./.venv/bin/python`
4. The terminal will auto-activate the venv

**Q: Can I run this on older macOS versions?**
A: Make sure you have Python 3.11+. If your macOS is very old (pre-2017), you may hit compatibility issues with some ML libraries.

**Q: How do I reset the project to a clean state?**
A:
```bash
# Remove virtual environment
rm -rf .venv

# Remove frontend node_modules
rm -rf frontend/node_modules

# Remove Python cache
find . -type d -name __pycache__ -exec rm -rf {} +

# Start fresh
python3 -m venv .venv
source .venv/bin/activate
python scripts/bootstrap_and_run.py
```

---

## Getting Help

- **For setup issues:** Check [SETUP_GUIDE.md](../SETUP_GUIDE.md)
- **For API issues:** Visit http://localhost:8000/docs
- **For frontend issues:** Check browser console (Cmd+Option+I)
- **For backend logs:** Check the terminal output
