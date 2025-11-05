#!/usr/bin/env python3
"""
Quick test script to verify Simultaneous SDK installation and basic functionality.
"""

import sys
import os

def test_imports():
    """Test that all imports work."""
    print("Testing imports...")
    try:
        from simultaneous import SimClient, Browser, BrowserClient
        print("✅ Imports successful")
        return True
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        print("\n💡 Tip: Install dependencies with: pip install -e '.[dev]'")
        return False

def test_client_init():
    """Test client initialization."""
    print("\nTesting client initialization...")
    try:
        from simultaneous import SimClient, Browser
        
        # Test with no API key (should work)
        client = SimClient()
        print("✅ SimClient initialized (no API key)")
        
        # Test with API key
        client = SimClient(api_key="test-key")
        print("✅ SimClient initialized (with API key)")
        
        # Test with custom API URL
        client = SimClient(api_key="test-key", api_url="https://api.simultaneous.live")
        print("✅ SimClient initialized (with custom API URL)")
        
        return True
    except Exception as e:
        print(f"❌ Client initialization failed: {e}")
        return False

def test_runtime_init():
    """Test runtime initialization."""
    print("\nTesting runtime initialization...")
    try:
        from simultaneous import Browser
        
        # Test with defaults
        runtime = Browser()
        print("✅ Browser runtime initialized (defaults)")
        
        # Test with explicit provider
        runtime = Browser(provider="browserbase")
        print("✅ Browser runtime initialized (browserbase provider)")
        
        # Test with project ID
        runtime = Browser(provider="browserbase", project="test-project-id")
        print("✅ Browser runtime initialized (with project ID)")
        
        return True
    except Exception as e:
        print(f"❌ Runtime initialization failed: {e}")
        return False

def test_browser_client():
    """Test BrowserClient initialization."""
    print("\nTesting BrowserClient initialization...")
    try:
        from simultaneous import BrowserClient
        
        # Test basic initialization
        browser = BrowserClient()
        print("✅ BrowserClient initialized (basic)")
        
        # Test with session URL
        browser = BrowserClient(session_url="wss://test.example.com/session")
        print("✅ BrowserClient initialized (with session URL)")
        
        # Test availability check
        available = browser.is_available()
        if available:
            print("✅ Browser automation SDK is installed")
        else:
            print("⚠️  Browser automation SDK is not installed (optional)")
        
        return True
    except Exception as e:
        print(f"❌ BrowserClient initialization failed: {e}")
        return False

def test_provider_router():
    """Test provider router."""
    print("\nTesting provider router...")
    try:
        from simultaneous.providers.router import get_adapter
        from simultaneous.runtime.base import RuntimeKind
        
        # Test getting browserbase adapter
        adapter = get_adapter(
            runtime_kind=RuntimeKind.BROWSER,
            provider="browserbase",
            config={"project_id": "test-project-id"},
        )
        print("✅ Provider router works (browserbase)")
        
        # Test auto provider
        adapter = get_adapter(
            runtime_kind=RuntimeKind.BROWSER,
            provider="auto",
            config={"project_id": "test-project-id"},
        )
        print("✅ Provider router works (auto provider)")
        
        return True
    except Exception as e:
        print(f"❌ Provider router test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("=" * 60)
    print("Simultaneous SDK - Quick Test")
    print("=" * 60)
    
    results = []
    results.append(("Imports", test_imports()))
    results.append(("Client Init", test_client_init()))
    results.append(("Runtime Init", test_runtime_init()))
    results.append(("BrowserClient", test_browser_client()))
    results.append(("Provider Router", test_provider_router()))
    
    print("\n" + "=" * 60)
    print("Test Results Summary")
    print("=" * 60)
    
    all_passed = True
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{name:20} {status}")
        if not passed:
            all_passed = False
    
    print("=" * 60)
    
    if all_passed:
        print("\n🎉 All tests passed! SDK is ready to use.")
        print("\nNext steps:")
        print("1. Set up environment variables (see INSTALL.md)")
        print("2. Create a project via Simultaneous API")
        print("3. Start building agents!")
        return 0
    else:
        print("\n⚠️  Some tests failed. Please check the errors above.")
        print("\n💡 Common fixes:")
        print("   - Install dependencies: pip install -e '.[dev]'")
        print("   - Check Python version (requires 3.11+): python --version")
        return 1

if __name__ == "__main__":
    sys.exit(main())

