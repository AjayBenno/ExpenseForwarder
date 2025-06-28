"""Setup script for expense forwarder."""

import os
import sys
import subprocess
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible."""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        print(f"Current version: {sys.version}")
        return False
    print(f"✅ Python version: {sys.version.split()[0]}")
    return True

def install_dependencies():
    """Install required dependencies."""
    print("\n📦 Installing dependencies...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], 
                      check=True, capture_output=True, text=True)
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        print(f"Error output: {e.stderr}")
        return False

def create_env_file():
    """Create .env file from template if it doesn't exist."""
    env_file = Path(".env")
    example_file = Path("config.example.env")
    
    if env_file.exists():
        print("\n📝 .env file already exists")
        return True
    
    if not example_file.exists():
        print("\n❌ config.example.env not found")
        return False
    
    try:
        # Copy example to .env
        with open(example_file, 'r') as src, open(env_file, 'w') as dst:
            dst.write(src.read())
        
        print("\n📝 Created .env file from template")
        print("⚠️  Please edit .env file with your API keys:")
        print("   - OpenAI API Key")
        print("   - Splitwise Client ID and Secret")
        return True
        
    except Exception as e:
        print(f"\n❌ Failed to create .env file: {e}")
        return False

def run_basic_test():
    """Run basic tests to verify setup."""
    print("\n🧪 Running basic tests...")
    try:
        result = subprocess.run([sys.executable, "test_example.py"], 
                               capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print("✅ Basic tests passed")
            return True
        else:
            print(f"❌ Tests failed: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ Tests timed out")
        return False
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return False

def print_next_steps():
    """Print next steps for the user."""
    print("\n" + "="*50)
    print("🎉 Setup completed!")
    print("="*50)
    print("\n📋 Next steps:")
    print("1. Edit .env file with your API keys:")
    print("   - Get OpenAI API key from: https://platform.openai.com/")
    print("   - Get Splitwise credentials from: https://secure.splitwise.com/apps")
    print()
    print("2. Test authentication:")
    print("   python main.py --auth-only --subject '' --body ''")
    print()
    print("3. Try a sample expense:")
    print("   python main.py --subject 'Dinner' --body 'Pizza $30 with John'")
    print()
    print("4. See more examples:")
    print("   python example_usage.py")
    print()
    print("📖 Read README.md for detailed documentation")

def main():
    """Main setup function."""
    print("Expense Forwarder Setup")
    print("="*50)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Install dependencies
    if not install_dependencies():
        print("\n❌ Setup failed during dependency installation")
        sys.exit(1)
    
    # Create .env file
    if not create_env_file():
        print("\n❌ Setup failed during .env creation")
        sys.exit(1)
    
    # Run basic tests
    if not run_basic_test():
        print("\n⚠️  Basic tests failed, but setup may still work")
        print("   This is likely due to missing API keys")
    
    # Print next steps
    print_next_steps()

if __name__ == "__main__":
    main() 