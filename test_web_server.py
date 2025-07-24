#!/usr/bin/env python3
"""
Quick test script to verify the web application is working
"""

import os
import sys
import time
import requests
import subprocess
from pathlib import Path

def test_web_application():
    """Test that the web application starts and responds correctly"""
    
    print("🧪 Testing FAL.AI Video Generator Web Application")
    print("=" * 60)
    
    # Set a test API key
    os.environ["FAL_KEY"] = "test_key_for_ui_testing"
    
    # Start the server in background
    print("🚀 Starting web server...")
    
    try:
        # Import and start the web app
        from web_app import app
        import uvicorn
        
        # Test the endpoints directly
        print("✅ Successfully imported web application")
        
        # Test if we can create the app
        from fastapi.testclient import TestClient
        client = TestClient(app)
        
        print("🧪 Testing API endpoints...")
        
        # Test main page
        response = client.get("/")
        print(f"📄 Main page: {response.status_code}")
        assert response.status_code == 200
        
        # Test models endpoint
        response = client.get("/api/models")
        print(f"🤖 Models API: {response.status_code}")
        assert response.status_code == 200
        
        # Test performance endpoint
        response = client.get("/api/performance")
        print(f"📊 Performance API: {response.status_code}")
        assert response.status_code == 200
        
        print("✅ All API endpoints working correctly!")
        
        print("\n🎉 SUCCESS: Web application is fully functional!")
        print("\n📡 To start the server manually:")
        print("   python web_app.py --host 127.0.0.1 --port 8000")
        print("   Then visit: http://localhost:8000")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Install missing dependencies: pip install fastapi uvicorn")
        return False
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_web_application()
    sys.exit(0 if success else 1)