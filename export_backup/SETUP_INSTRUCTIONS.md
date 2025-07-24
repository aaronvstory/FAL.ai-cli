# 🚀 FAL.AI Video Generator - External Setup Instructions

> **Step-by-step guide for external development setup**

## 📋 **Prerequisites**

### **System Requirements**
- **Python**: 3.8+ (3.9+ recommended)
- **Operating System**: Windows, macOS, or Linux
- **Memory**: 4GB RAM minimum, 8GB recommended
- **Storage**: 2GB free space
- **Internet**: Required for API calls and dependencies

### **Required Accounts & Keys**
- **FAL.AI Account**: Get your API key from [fal.ai/dashboard](https://fal.ai/dashboard)
- **Optional**: GitHub account for version control

---

## 🏗️ **Step 1: Environment Setup**

### **Create Project Directory**
```bash
# Create and enter project directory
mkdir fal-ai-video-generator
cd fal-ai-video-generator
```

### **Extract Export Files**
1. Copy all files from the export package to your project directory
2. Ensure the directory structure matches the layout in README_EXPORT.md

### **Verify File Structure**
```bash
# Check main files are present
ls -la

# Should see:
# FAL_LAUNCHER.py (main entry point)
# main.py, web_app.py, security.py, performance.py
# requirements.txt
# config/, web/, core/, tests/ directories
```

---

## 🐍 **Step 2: Python Environment**

### **Option A: Virtual Environment (Recommended)**
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### **Option B: Conda Environment**
```bash
# Create conda environment
conda create -n fal-ai python=3.9
conda activate fal-ai

# Install dependencies
pip install -r requirements.txt
```

### **Option C: System Python (Not recommended)**
```bash
# Install directly to system Python
pip install -r requirements.txt
```

---

## 🔑 **Step 3: API Key Configuration**

### **Get Your FAL API Key**
1. Visit [fal.ai/dashboard](https://fal.ai/dashboard)
2. Sign up or log in to your account
3. Navigate to API Keys section
4. Create a new API key
5. Copy the key (it starts with `key_...`)

### **Set Environment Variable**

**Windows (Command Prompt):**
```cmd
set FAL_KEY=your_fal_api_key_here
```

**Windows (PowerShell):**
```powershell
$env:FAL_KEY="your_fal_api_key_here"
```

**Windows (Permanent):**
```cmd
setx FAL_KEY "your_fal_api_key_here"
```

**macOS/Linux:**
```bash
export FAL_KEY=your_fal_api_key_here

# Add to ~/.bashrc or ~/.zshrc for persistence
echo 'export FAL_KEY=your_fal_api_key_here' >> ~/.bashrc
```

### **Alternative: .env File**
```bash
# Create .env file in project root
echo "FAL_KEY=your_fal_api_key_here" > .env
```

---

## ✅ **Step 4: Verification & Testing**

### **Test Installation**
```bash
# Test Python and dependencies
python -c "import fal_client, fastapi, uvicorn; print('✅ All dependencies installed')"

# Test API key
python -c "import os; print('✅ API key set' if os.getenv('FAL_KEY') else '❌ API key missing')"
```

### **Launch Application**
```bash
# Start the unified launcher
python FAL_LAUNCHER.py

# Should show:
# - Colorful ASCII banner
# - Environment status check
# - Interactive menu with 6 options
```

### **Test Web Interface**
```bash
# Launch web mode directly
python FAL_LAUNCHER.py --mode web

# Should:
# - Start server on http://127.0.0.1:8000
# - Open browser automatically
# - Show modern drag-and-drop interface
```

### **Run Tests**
```bash
# Run basic functionality tests
python -m pytest tests/test_launcher_core.py -v

# Should show mostly passing tests
```

---

## 🔧 **Step 5: Configuration & Customization**

### **Adjust Settings**
```bash
# Launch interactive settings
python FAL_LAUNCHER.py
# Select option 4 (Settings)
```

**Available Settings:**
- Default model selection
- Default duration (1-10 seconds)
- Default aspect ratio
- Auto-open web browser
- Cost warnings

### **Directory Setup**
The application will auto-create these directories:
- `data/` - User preferences and history
- `temp/uploads/` - Temporary file storage
- `logs/` - Application logs

### **Optional: Redis Cache**
For better performance, install Redis:

**Windows:**
- Download Redis from [releases page](https://github.com/microsoftarchive/redis/releases)
- Or use Docker: `docker run -d -p 6379:6379 redis:alpine`

**macOS:**
```bash
brew install redis
redis-server
```

**Linux:**
```bash
sudo apt-get install redis-server
sudo systemctl start redis-server
```

---

## 🐳 **Step 6: Docker Setup (Optional)**

### **Development with Docker**
```bash
# Start development environment
docker-compose up -d

# Access services:
# App: http://localhost:8000
# Redis: localhost:6379
```

### **Production with Docker**
```bash
# Start production environment
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Additional services:
# Grafana: http://localhost:3000 (admin/admin123)
# Prometheus: http://localhost:9090
```

---

## 🚨 **Common Issues & Solutions**

### **Issue: "Import Error: No module named 'fal_client'"**
**Solution:**
```bash
pip install fal-client
# or
pip install -r requirements.txt
```

### **Issue: "tkinter not found" (Linux)**  
**Solution:**
```bash
# Ubuntu/Debian
sudo apt-get install python3-tk

# CentOS/RHEL
sudo yum install tkinter
```

### **Issue: "Port 8000 already in use"**
**Solution:**
```bash
# The launcher automatically finds free ports
# Or kill existing process:
# Windows: netstat -ano | findstr :8000
# Linux/Mac: lsof -ti:8000 | xargs kill
```

### **Issue: "FAL API key not working"**
**Solution:**
1. Verify key format (starts with `key_`)
2. Check [fal.ai/dashboard](https://fal.ai/dashboard) for key status
3. Ensure no extra spaces or quotes
4. Try regenerating the key

### **Issue: "Web interface blank page"**
**Solution:**
```bash
# Check browser console for errors
# Verify static files are present:
ls web/static/

# Clear browser cache
# Try different browser
```

---

## 🎯 **Next Steps**

### **Basic Usage**
1. **Start the launcher**: `python FAL_LAUNCHER.py`
2. **Choose Web Interface** (option 1) for first-time use
3. **Upload an image** and enter a creative prompt
4. **Select Kling 2.1 Pro** for best quality/cost balance
5. **Generate your first video!**

### **Advanced Usage**
- Explore CLI mode for power-user features
- Try Quick Generate for rapid iterations
- Customize settings for your workflow
- Set up batch processing for multiple videos

### **Development Setup**
- Set up IDE/editor with Python support
- Configure linting (flake8, black)
- Set up debugging with breakpoints
- Explore the codebase structure

---

## 📚 **Additional Resources**

### **Documentation**
- `README_EXPORT.md` - Complete feature overview
- `CLAUDE.md` - Development guidelines (if included)
- `web/templates/` - Web interface customization
- `tests/` - Example usage patterns

### **API Documentation**
- [FAL.AI API Docs](https://fal.ai/docs)
- [FAL.AI Model Gallery](https://fal.ai/models)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)

### **Community & Support**
- FAL.AI Discord community
- GitHub issues in original repository
- Stack Overflow for technical questions

---

## ✅ **Verification Checklist**

- [ ] Python 3.8+ installed and working
- [ ] Virtual environment created and activated
- [ ] All dependencies installed (`pip install -r requirements.txt`)
- [ ] FAL API key obtained and configured
- [ ] Environment variable `FAL_KEY` set correctly
- [ ] Launcher starts without errors (`python FAL_LAUNCHER.py`)
- [ ] Web interface accessible (option 1 in launcher)
- [ ] Basic tests pass (`pytest tests/test_launcher_core.py`)
- [ ] Sample video generation works

---

<div align="center">

**🎉 You're all set up and ready to generate amazing AI videos! 🚀**

*Need help? Check the troubleshooting section or refer to the original repository.*

</div>