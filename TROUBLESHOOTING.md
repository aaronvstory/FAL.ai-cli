# 🔧 Troubleshooting Guide

## Common Issues and Solutions

### ❌ "Can't reach this page" or "Connection refused"

**Problem**: Browser shows "localhost refused to connect" when accessing http://localhost:8000

**Solutions**:

1. **Check if the server is running**:
   ```bash
   # Look for Python processes
   tasklist | findstr python
   
   # Or check if port 8000 is in use
   netstat -an | findstr :8000
   ```

2. **Start the web server properly**:
   ```bash
   # Navigate to project directory
   cd C:\claude\FAL.AI-Maroz
   
   # Start the server
   python web_app.py --host 127.0.0.1 --port 8000
   ```

3. **Use the correct URL**:
   - ✅ Correct: `http://127.0.0.1:8000` or `http://localhost:8000`
   - ❌ Incorrect: `https://localhost:8000` (note the https)

4. **Check firewall settings**:
   - Windows may block the connection
   - Allow Python through Windows Firewall when prompted

### ❌ API Key Issues

**Problem**: Web interface loads but video generation fails

**Solutions**:

1. **Set the FAL API key**:
   ```bash
   # Windows Command Prompt
   set FAL_KEY=your_actual_api_key_here
   
   # Windows PowerShell
   $env:FAL_KEY="your_actual_api_key_here"
   ```

2. **Get a valid API key**:
   - Visit [fal.ai](https://fal.ai/)
   - Sign up and get your API key
   - The key should start with something like "fal_"

3. **Verify the key is set**:
   ```bash
   echo %FAL_KEY%
   ```

### ❌ Missing Dependencies

**Problem**: ImportError or ModuleNotFoundError when starting

**Solutions**:

1. **Install all dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Install specific missing packages**:
   ```bash
   pip install fastapi uvicorn redis aiofiles aiohttp psutil
   ```

3. **Check Python version**:
   ```bash
   python --version
   # Should be Python 3.8 or higher
   ```

### ❌ Port Already in Use

**Problem**: "Address already in use" error on port 8000

**Solutions**:

1. **Use a different port**:
   ```bash
   python web_app.py --host 127.0.0.1 --port 8001
   ```

2. **Kill existing processes on port 8000**:
   ```bash
   # Find process using port 8000
   netstat -ano | findstr :8000
   
   # Kill the process (replace PID with actual process ID)
   taskkill /F /PID <PID>
   ```

### ❌ File Upload Issues

**Problem**: Drag-and-drop or file upload not working

**Solutions**:

1. **Check file types**:
   - Only image files are supported (JPG, PNG, GIF, WebP)
   - Check file extensions and MIME types

2. **Check file permissions**:
   ```bash
   # Create upload directory if missing
   mkdir temp\uploads
   ```

3. **Browser compatibility**:
   - Use a modern browser (Chrome, Firefox, Safari, Edge)
   - Enable JavaScript
   - Clear browser cache

### ❌ WebSocket Connection Issues

**Problem**: Real-time progress updates not working

**Solutions**:

1. **Check browser console**:
   - Press F12 to open developer tools
   - Look for WebSocket connection errors

2. **Firewall/proxy issues**:
   - Corporate firewalls may block WebSocket connections
   - Try disabling antivirus temporarily

3. **Try without WebSocket**:
   - The app will still work, just without real-time updates

## Testing Your Setup

### Quick Test Script

Run this script to verify everything is working:

```bash
python test_web_server.py
```

This will test:
- ✅ All dependencies are installed
- ✅ Web application starts correctly
- ✅ All API endpoints respond
- ✅ Basic functionality works

### Manual Testing Steps

1. **Start the server**:
   ```bash
   python web_app.py --host 127.0.0.1 --port 8000
   ```

2. **Open your browser** and visit: http://localhost:8000

3. **Check the interface**:
   - ✅ Page loads with beautiful gradient interface
   - ✅ Upload area is visible
   - ✅ Model selection cards are displayed
   - ✅ Generation form is present

4. **Test file upload** (optional):
   - Drag an image file to the upload area
   - Should see file preview and upload success message

5. **Check API endpoints**:
   ```bash
   curl http://localhost:8000/api/models
   curl http://localhost:8000/api/performance
   ```

## Still Having Issues?

### Detailed Logging

Enable verbose logging to see what's happening:

```bash
# Start with debug logging
python -c "import logging; logging.basicConfig(level=logging.DEBUG); import web_app; web_app.main()"
```

### System Requirements

Make sure your system meets these requirements:

- **Python**: 3.8 or higher
- **RAM**: At least 4GB available
- **Storage**: 1GB free space for temporary files
- **Network**: Internet connection for FAL.AI API calls
- **Browser**: Modern browser with JavaScript enabled

### Get Help

If you're still having issues:

1. **Check the logs** in the terminal where you started the server
2. **Check browser console** (F12 → Console tab)
3. **Try the test script**: `python test_web_server.py`
4. **Restart everything**: Close browser, stop server, restart both

### Common Error Messages

| Error | Solution |
|-------|----------|
| `ModuleNotFoundError: No module named 'fastapi'` | Run `pip install fastapi uvicorn` |
| `Address already in use` | Use different port or kill existing process |
| `Permission denied` | Run as administrator or check file permissions |
| `Connection refused` | Check if server is running and URL is correct |
| `FAL API key not configured` | Set FAL_KEY environment variable |

---

## Success! 🎉

If you see this in your browser:

- Beautiful gradient interface ✅
- Upload area with drag-and-drop ✅  
- Model selection cards ✅
- Real-time connection indicator ✅

**You're ready to generate videos!** 🎬

Remember to set your FAL API key for actual video generation to work.