#!/usr/bin/env python3
"""
Test and validate NOAA CDO API token
"""

import requests
import os
from dotenv import load_dotenv

def test_noaa_token():
    """Test NOAA token validation"""
    load_dotenv()
    token = os.getenv('NOAA_CDO_TOKEN')
    
    if not token:
        print("❌ No NOAA_CDO_TOKEN found in .env file")
        return False
    
    print(f"🔍 Testing NOAA token: {token[:10]}...{token[-5:]}")
    print(f"Token length: {len(token)}")
    
    # Test the token with a simple API call
    headers = {'token': token}
    url = 'https://www.ncei.noaa.gov/cdo-web/api/v2/datasets'
    
    try:
        response = requests.get(url, headers=headers, params={'limit': 1})
        print(f"API Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Token is VALID!")
            print(f"   Found {len(data.get('results', []))} datasets")
            return True
        elif response.status_code == 400:
            error_data = response.json()
            print(f"❌ Token is INVALID: {error_data.get('message', 'Unknown error')}")
            print("\nPossible issues:")
            print("1. Token is not activated yet")
            print("2. Token was copied incorrectly")
            print("3. Token has expired")
            print("4. Token needs to be activated on NOAA website")
            return False
        else:
            print(f"❌ Unexpected response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Network error: {e}")
        return False

def main():
    """Main function"""
    print("🧪 NOAA Token Validation Test")
    print("=" * 40)
    
    is_valid = test_noaa_token()
    
    if not is_valid:
        print("\n🔧 Troubleshooting Steps:")
        print("1. Go to: https://www.ncdc.noaa.gov/cdo-web/token")
        print("2. Check if your token is activated")
        print("3. Try generating a new token")
        print("4. Make sure the token is copied correctly to .env")
        print("\n💡 Alternative: We can use direct APIs without the token")
        print("   The direct APIs (US Weather Service, Environment Canada) work without tokens")
    else:
        print("\n🎉 Token is working! We can now use the NOAA CDO API library")

if __name__ == "__main__":
    main()

