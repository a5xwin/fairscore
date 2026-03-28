# Cross-Platform Compatibility Checklist

This document outlines the cross-platform status of the FairScore project and how to fix common issues.

## ✅ Already Cross-Platform Safe

- [x] **Bootstrap script** (`scripts/bootstrap_and_run.py`) - Uses `os.name == "nt"` for OS detection
- [x] **File paths** - Uses `pathlib.Path` and `os.path.join()`, no hardcoded backslashes
- [x] **Python dependencies** - All are cross-platform (FastAPI, Supabase, PyTorch, LightGBM, etc.)
- [x] **Frontend packages** - All npm packages are platform-agnostic
- [x] **Virtual environment** - Script handles both `activate.ps1` (Windows) and `source activate` (Unix)
- [x] **Process management** - Handles Windows process groups and Unix signals correctly

## ⚠️ Potential Issues & Solutions

### Issue 1: Python command availability

**Problem:** `python` might not exist on macOS/Linux
**Status:** Already handled in docs
**User Action:** Use `python3` or ensure Python is in PATH

```bash
# macOS/Linux - use python3
python3 scripts/bootstrap_and_run.py

# Or ensure .venv/bin/python is used
source .venv/bin/activate  # which python will now point to venv
```

### Issue 2: M1/M2 Mac native package compilation

**Problem:** PyTorch, SHAP, LightGBM may fail to install
**Status:** Documented in MAC_SETUP.md
**User Action:** Use architecture-specific flags

```bash
ARCHFLAGS=-Qunused-arguments CPPFLAGS=-QunusedArguments pip install -r requirements.txt
```

### Issue 3: Port conflicts

**Problem:** Ports 8000 or 5173 might already be in use
**Status:** Fully supported via CLI flags
**User Action:** Use custom ports

```bash
python scripts/bootstrap_and_run.py --backend-port 9000 --frontend-port 5174
```

### Issue 4: Environment variable configuration

**Problem:** Users don't know what .env variables are needed
**Status:** ✅ FIXED - Created .env.example
**User Action:** Copy and fill in credentials

```bash
cp .env.example .env
# Edit .env with your Supabase credentials
```

## 📋 Setup Documents Created

1. **[SETUP_GUIDE.md](SETUP_GUIDE.md)** - Complete cross-platform setup guide (Windows, macOS, Linux)
2. **[MAC_SETUP.md](MAC_SETUP.md)** - Detailed macOS-specific guide with troubleshooting
3. **[Dockerfile](Dockerfile)** - Docker image for guaranteed compatibility
4. **[docker-compose.yml](docker-compose.yml)** - Docker Compose for easy containerization

## 🚀 Quick Reference: Running on Different OSes

### Windows
```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python scripts/bootstrap_and_run.py
```

### macOS
```bash
python3 -m venv .venv
source .venv/bin/activate
python scripts/bootstrap_and_run.py
```

### Linux (Ubuntu/Debian)
```bash
python3 -m venv .venv
source .venv/bin/activate
python scripts/bootstrap_and_run.py
```

### Docker (All Platforms)
```bash
docker build -t fairscore .
docker run -p 8000:8000 -p 5173:5173 fairscore
```

## ✅ Testing Checklist for New OS

When testing on a new OS/machine:

- [ ] Python 3.11+ installed
- [ ] Node.js 18+ installed
- [ ] Run: `python -m venv .venv`
- [ ] Activate venv (OS-specific command)
- [ ] Copy `.env.example` to `.env` and fill in credentials
- [ ] Run: `python scripts/bootstrap_and_run.py`
- [ ] Wait for both services to start
- [ ] Open http://localhost:5173 in browser
- [ ] Test backend API at http://localhost:8000/docs
- [ ] Verify prediction endpoints work (requires model artifacts)

## 🐳 Docker Alternative

For guaranteed compatibility without troubleshooting:

```bash
# Prerequisites: Docker Desktop (https://www.docker.com/products/docker-desktop)

# Build once
docker build -t fairscore .

# Run anytime
docker run -it --rm \
  -p 8000:8000 \
  -p 5173:5173 \
  -e SUPABASE_URL=your_url \
  -e SUPABASE_SERVICE_ROLE_KEY=your_key \
  fairscore
```

## 📝 Environment Variables Needed

Create a `.env` file in the project root with:

```env
# Required
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-key-here

# Optional (defaults provided)
DEBUG=false
API_TIMEOUT=30
```

## 🔧 Known Limitations

1. **M1/M2 Macs** - Some packages may compile slowly (first-time setup)
2. **ARM Linux** - PyTorch ARM wheels may not be available, requires compilation
3. **Model training** - Requires significant RAM (6GB+) for ensemble training
4. **GPU support** - PyTorch CUDA disabled by default; install `torch` with GPU support if needed

## 📚 Further Reading

- [SETUP_GUIDE.md](SETUP_GUIDE.md) - Full setup instructions for all OSes
- [MAC_SETUP.md](MAC_SETUP.md) - macOS-specific guidance
- [README.md](README.md) - Project overview

## ✨ Summary

Your project is **production-ready for cross-platform use**! All major compatibility issues are handled by the existing bootstrap script. The new documentation and sample files ensure users on any OS can get started quickly.
