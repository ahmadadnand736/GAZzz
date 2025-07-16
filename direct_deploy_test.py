#!/usr/bin/env python3
"""
Direct deployment test for weathered-bonus-2b87 worker
This script tests deployment without full API access
"""

import requests
import json
from cloudflare_deploy import generate_worker_code

def test_direct_deployment():
    """Test direct deployment to the weathered-bonus-2b87 worker"""
    
    # Configuration
    config = {
        "api_token": "FdAOb0lSWzYXJV1bw7wu7LzXWALPjSOnbKkT9vKh",
        "account_id": "a418be812e4b0653ca1512804285e4a0",
        "worker_name": "weathered-bonus-2b87"
    }
    
    # Generate worker code
    worker_code = generate_worker_code()
    
    # API endpoint
    url = f"https://api.cloudflare.com/client/v4/accounts/{config['account_id']}/workers/scripts/{config['worker_name']}"
    
    # Headers
    headers = {
        "Authorization": f"Bearer {config['api_token']}",
        "Content-Type": "application/javascript"
    }
    
    print(f"Attempting to deploy to: {config['worker_name']}")
    print(f"Target URL: https://{config['worker_name']}.{config['account_id']}.workers.dev")
    print(f"API Endpoint: {url}")
    
    try:
        # Deploy worker
        response = requests.put(url, headers=headers, data=worker_code)
        
        print(f"Response Status: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print(f"Response Text: {response.text}")
        
        if response.status_code == 200:
            print("✅ SUCCESS: Worker deployed successfully!")
            return True
        else:
            print(f"❌ FAILED: Status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False

def test_worker_access():
    """Test if we can access the worker URL"""
    worker_url = "https://weathered-bonus-2b87.ahmadadnand736.workers.dev"
    
    try:
        response = requests.get(worker_url, timeout=10)
        print(f"Worker URL: {worker_url}")
        print(f"Status Code: {response.status_code}")
        print(f"Response Length: {len(response.text)}")
        print(f"Response Preview: {response.text[:300]}...")
        
        if response.status_code == 200:
            print("✅ Worker is accessible!")
            return True
        else:
            print(f"⚠️  Worker returned status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Could not access worker: {str(e)}")
        return False

if __name__ == "__main__":
    print("=== Direct Deployment Test ===")
    
    # First test if worker is accessible
    print("\n1. Testing worker accessibility...")
    accessible = test_worker_access()
    
    # Then test deployment
    print("\n2. Testing deployment...")
    deployed = test_direct_deployment()
    
    # Summary
    print("\n=== SUMMARY ===")
    print(f"Worker Accessible: {'✅' if accessible else '❌'}")
    print(f"Deployment Success: {'✅' if deployed else '❌'}")
    
    if not deployed:
        print("\nTroubleshooting:")
        print("1. Check if API token has 'Cloudflare Workers:Edit' permission")
        print("2. Ensure account ID is correct: a418be812e4b0653ca1512804285e4a0")
        print("3. Verify worker name: weathered-bonus-2b87")