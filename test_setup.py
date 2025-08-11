#!/usr/bin/env python3
"""
Test script to verify the QuickBooks expense extractor setup
"""

def test_imports():
    """Test that all required modules can be imported"""
    try:
        import config
        print("✓ config.py imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import config.py: {e}")
        return False
    
    try:
        import quickbooks_client
        print("✓ quickbooks_client.py imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import quickbooks_client.py: {e}")
        return False
    
    try:
        import data_exporter
        print("✓ data_exporter.py imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import data_exporter.py: {e}")
        return False
    
    try:
        import auth_helper
        print("✓ auth_helper.py imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import auth_helper.py: {e}")
        return False
    
    return True

def test_dependencies():
    """Test that required Python packages are available"""
    try:
        import pandas as pd
        print(f"✓ pandas {pd.__version__} available")
    except ImportError:
        print("✗ pandas not available - install with: pip install pandas")
        return False
    
    try:
        import requests
        print(f"✓ requests {requests.__version__} available")
    except ImportError:
        print("✗ requests not available - install with: pip install requests")
        return False
    
    try:
        import openpyxl
        print(f"✓ openpyxl {openpyxl.__version__} available")
    except ImportError:
        print("✗ openpyxl not available - install with: pip install openpyxl")
        return False
    
    try:
        from dotenv import load_dotenv
        print("✓ python-dotenv available")
    except ImportError:
        print("✗ python-dotenv not available - install with: pip install python-dotenv")
        return False
    
    return True

def test_config():
    """Test configuration loading"""
    try:
        from config import QuickBooksConfig
        config = QuickBooksConfig()
        print("✓ Configuration loaded successfully")
        print(f"  - Output directory: {config.OUTPUT_DIR}")
        print(f"  - Default export format: {config.DEFAULT_EXPORT_FORMAT}")
        print(f"  - Supported formats: {', '.join(config.EXPORT_FORMATS)}")
        return True
    except Exception as e:
        print(f"✗ Configuration test failed: {e}")
        return False

def test_file_structure():
    """Test that all required files exist"""
    import os
    
    required_files = [
        'main.py',
        'config.py',
        'quickbooks_client.py',
        'data_exporter.py',
        'auth_helper.py',
        'requirements.txt',
        'env_example.txt',
        'README.md'
    ]
    
    missing_files = []
    for file in required_files:
        if os.path.exists(file):
            print(f"✓ {file} exists")
        else:
            print(f"✗ {file} missing")
            missing_files.append(file)
    
    if missing_files:
        print(f"\nMissing files: {', '.join(missing_files)}")
        return False
    
    return True

def main():
    """Run all tests"""
    print("QuickBooks Expense Extractor - Setup Test")
    print("=" * 50)
    
    tests = [
        ("File Structure", test_file_structure),
        ("Dependencies", test_dependencies),
        ("Configuration", test_config),
        ("Module Imports", test_imports),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        print("-" * 30)
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"✗ Test failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("Test Summary:")
    print("-" * 30)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{test_name}: {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Your setup is ready.")
        print("\nNext steps:")
        print("1. Copy env_example.txt to .env")
        print("2. Add your QuickBooks API credentials")
        print("3. Run: python auth_helper.py --authenticate")
        print("4. Run: python main.py --help")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please fix the issues above.")
        print("\nCommon solutions:")
        print("- Install missing dependencies: pip install -r requirements.txt")
        print("- Check file permissions and paths")
        print("- Verify Python version (3.7+)")

if __name__ == "__main__":
    main() 