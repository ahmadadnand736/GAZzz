import requests
import json
import re

class CloudflareWorkerDetector:
    def __init__(self):
        self.config = self.load_config()
        self.base_url = "https://api.cloudflare.com/client/v4"
        
    def load_config(self):
        """Load configuration from config.json"""
        try:
            with open('config.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {
                "cloudflare": {
                    "api_token": "FdAOb0lSWzYXJV1bw7wu7LzXWALPjSOnbKkT9vKh",
                    "account_id": "a418be812e4b0653ca1512804285e4a0",
                    "worker_name": "article-generator"
                }
            }
    
    def get_headers(self):
        """Get headers for Cloudflare API requests"""
        return {
            "Authorization": f"Bearer {self.config['cloudflare']['api_token']}",
            "Content-Type": "application/json"
        }
    
    def get_all_workers(self):
        """Get all workers from Cloudflare account"""
        account_id = self.config['cloudflare']['account_id']
        url = f"{self.base_url}/accounts/{account_id}/workers/scripts"
        
        try:
            response = requests.get(url, headers=self.get_headers())
            
            if response.status_code == 200:
                data = response.json()
                if data['success']:
                    workers = []
                    for worker in data['result']:
                        # Get worker details
                        worker_info = {
                            'id': worker['id'],
                            'created_on': worker.get('created_on', ''),
                            'modified_on': worker.get('modified_on', ''),
                            'subdomain_url': f"https://{worker['id']}.{account_id}.workers.dev"
                        }
                        
                        # Check if worker responds
                        try:
                            test_response = requests.get(worker_info['subdomain_url'], timeout=5)
                            worker_info['status'] = 'active' if test_response.status_code == 200 else 'inactive'
                            worker_info['response_code'] = test_response.status_code
                        except:
                            worker_info['status'] = 'inactive'
                            worker_info['response_code'] = 0
                        
                        workers.append(worker_info)
                    
                    return {
                        "success": True,
                        "workers": workers
                    }
                else:
                    return {
                        "success": False,
                        "error": data.get('errors', ['Unknown error'])
                    }
            else:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}: {response.text}"
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_worker_subdomains(self):
        """Get all worker subdomains for the account"""
        account_id = self.config['cloudflare']['account_id']
        url = f"{self.base_url}/accounts/{account_id}/workers/subdomain"
        
        try:
            response = requests.get(url, headers=self.get_headers())
            
            if response.status_code == 200:
                data = response.json()
                if data['success']:
                    subdomain_info = data['result']
                    return {
                        "success": True,
                        "subdomain": subdomain_info.get('subdomain', ''),
                        "full_subdomain": f"{subdomain_info.get('subdomain', '')}.workers.dev"
                    }
                else:
                    return {
                        "success": False,
                        "error": data.get('errors', ['Unknown error'])
                    }
            else:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}: {response.text}"
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def detect_existing_worker(self, target_url="https://weathered-bonus-2b87.ahmadadnand736.workers.dev"):
        """Detect if the target URL is an existing worker"""
        try:
            # Extract worker name from URL
            url_pattern = r'https://([^.]+)\.([^.]+)\.workers\.dev'
            match = re.match(url_pattern, target_url)
            
            if match:
                worker_name = match.group(1)
                account_subdomain = match.group(2)
                
                # Check if this worker exists
                all_workers = self.get_all_workers()
                
                if all_workers['success']:
                    # Look for worker with matching name
                    for worker in all_workers['workers']:
                        if worker['id'] == worker_name:
                            return {
                                "success": True,
                                "exists": True,
                                "worker_name": worker_name,
                                "subdomain": account_subdomain,
                                "full_url": target_url,
                                "status": worker['status'],
                                "worker_info": worker
                            }
                    
                    # Worker not found, but we can create it
                    return {
                        "success": True,
                        "exists": False,
                        "worker_name": worker_name,
                        "subdomain": account_subdomain,
                        "full_url": target_url,
                        "can_create": True
                    }
                else:
                    return {
                        "success": False,
                        "error": all_workers['error']
                    }
            else:
                return {
                    "success": False,
                    "error": "Invalid worker URL format"
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def update_worker_config(self, worker_name, target_url):
        """Update configuration with detected worker"""
        self.config['cloudflare']['worker_name'] = worker_name
        self.config['cloudflare']['target_url'] = target_url
        
        # Save updated config
        with open('config.json', 'w') as f:
            json.dump(self.config, f, indent=2)
        
        return True
    
    def create_or_update_worker(self, worker_name, worker_code):
        """Create or update a specific worker"""
        account_id = self.config['cloudflare']['account_id']
        url = f"{self.base_url}/accounts/{account_id}/workers/scripts/{worker_name}"
        
        headers = {
            "Authorization": f"Bearer {self.config['cloudflare']['api_token']}",
            "Content-Type": "application/javascript"
        }
        
        try:
            response = requests.put(url, headers=headers, data=worker_code)
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "success": True,
                    "message": f"Worker '{worker_name}' deployed successfully",
                    "url": f"https://{worker_name}.{account_id}.workers.dev",
                    "response": result
                }
            else:
                return {
                    "success": False,
                    "message": f"Deploy failed: {response.text}",
                    "status_code": response.status_code
                }
        except Exception as e:
            return {
                "success": False,
                "message": f"Error: {str(e)}"
            }

if __name__ == "__main__":
    # Test the detector
    detector = CloudflareWorkerDetector()
    
    print("Testing worker detection...")
    result = detector.detect_existing_worker("https://weathered-bonus-2b87.ahmadadnand736.workers.dev")
    print(json.dumps(result, indent=2))
    
    print("\nGetting all workers...")
    workers = detector.get_all_workers()
    print(json.dumps(workers, indent=2))
    
    print("\nGetting subdomain info...")
    subdomain = detector.get_worker_subdomains()
    print(json.dumps(subdomain, indent=2))