#!/usr/bin/env python3
"""
Script to get Yandex.Disk OAuth token

This script helps you obtain an OAuth token for Yandex.Disk API.
You need to register an application first at https://oauth.yandex.ru/
"""

import sys

try:
    import yadisk
except ImportError:
    print("Error: yadisk library not installed")
    print("Run: pip install yadisk")
    sys.exit(1)


def get_token_interactive():
    """Get OAuth token interactively"""
    print("=" * 60)
    print("Yandex.Disk OAuth Token Generator")
    print("=" * 60)
    print()
    print("First, you need to register an application:")
    print("1. Go to https://oauth.yandex.ru/")
    print("2. Click 'Register new client'")
    print("3. Fill in the form:")
    print("   - Name: CloudTube Bot (or any name)")
    print("   - Platforms: Check 'Web services'")
    print("   - Redirect URI: https://oauth.yandex.ru/verification_code")
    print("   - Permissions: Check 'Yandex.Disk REST API'")
    print("4. Click 'Create'")
    print("5. Copy the Client ID and Client Secret")
    print()
    
    client_id = input("Enter Client ID: ").strip()
    client_secret = input("Enter Client Secret: ").strip()
    
    if not client_id or not client_secret:
        print("Error: Client ID and Secret are required")
        sys.exit(1)
    
    # Create client
    client = yadisk.Client(id=client_id, secret=client_secret)
    
    # Get authorization URL
    url = client.get_code_url()
    
    print()
    print("=" * 60)
    print("Step 2: Get Authorization Code")
    print("=" * 60)
    print()
    print("1. Open this URL in your browser:")
    print(f"   {url}")
    print()
    print("2. Log in to your Yandex account")
    print("3. Allow access to Yandex.Disk")
    print("4. Copy the verification code")
    print()
    
    code = input("Enter verification code: ").strip()
    
    if not code:
        print("Error: Verification code is required")
        sys.exit(1)
    
    try:
        # Exchange code for token
        response = client.get_token(code)
        
        print()
        print("=" * 60)
        print("Success! Your OAuth Token:")
        print("=" * 60)
        print()
        print(response.access_token)
        print()
        print("=" * 60)
        print()
        print("Save this token securely!")
        print("Use it as WEBDAV_PASSWORD in your .env file")
        print()
        
        return response.access_token
        
    except Exception as e:
        print(f"Error getting token: {e}")
        sys.exit(1)


def main():
    """Main function"""
    try:
        token = get_token_interactive()
        
        # Test the token
        print("Testing token...")
        client = yadisk.Client(token=token)
        
        if client.check_token():
            print("✅ Token is valid!")
            
            # Get disk info
            disk_info = client.get_disk_info()
            total_gb = disk_info.total_space / (1024**3)
            used_gb = disk_info.used_space / (1024**3)
            free_gb = (disk_info.total_space - disk_info.used_space) / (1024**3)
            
            print()
            print("Yandex.Disk Info:")
            print(f"  Total: {total_gb:.2f} GB")
            print(f"  Used: {used_gb:.2f} GB")
            print(f"  Free: {free_gb:.2f} GB")
        else:
            print("❌ Token is invalid!")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\nCancelled by user")
        sys.exit(0)
    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
