import requests
import json

class CloudflareDomainManager:
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
                    "zone_id": "",
                    "worker_name": "article-generator",
                    "selected_domain": "",
                    "deployment_type": "subdomain"
                }
            }
    
    def get_headers(self):
        """Get headers for Cloudflare API requests"""
        return {
            "Authorization": f"Bearer {self.config['cloudflare']['api_token']}",
            "Content-Type": "application/json"
        }
    
    def get_zones(self):
        """Get all zones (domains) from Cloudflare account"""
        url = f"{self.base_url}/zones"
        
        try:
            response = requests.get(url, headers=self.get_headers())
            
            if response.status_code == 200:
                data = response.json()
                if data['success']:
                    zones = []
                    for zone in data['result']:
                        zones.append({
                            'id': zone['id'],
                            'name': zone['name'],
                            'status': zone['status'],
                            'plan': zone['plan']['name'] if zone['plan'] else 'Free'
                        })
                    return {
                        "success": True,
                        "zones": zones
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
    
    def get_worker_routes(self, zone_id):
        """Get existing worker routes for a zone"""
        url = f"{self.base_url}/zones/{zone_id}/workers/routes"
        
        try:
            response = requests.get(url, headers=self.get_headers())
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "success": True,
                    "routes": data.get('result', [])
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
    
    def create_worker_route(self, zone_id, pattern, worker_name):
        """Create a worker route for custom domain"""
        url = f"{self.base_url}/zones/{zone_id}/workers/routes"
        
        data = {
            "pattern": pattern,
            "script": worker_name
        }
        
        try:
            response = requests.post(url, headers=self.get_headers(), json=data)
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "success": True,
                    "route": result.get('result', {})
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
    
    def delete_worker_route(self, zone_id, route_id):
        """Delete a worker route"""
        url = f"{self.base_url}/zones/{zone_id}/workers/routes/{route_id}"
        
        try:
            response = requests.delete(url, headers=self.get_headers())
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "message": "Route deleted successfully"
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
    
    def get_worker_subdomain_url(self, account_id, worker_name):
        """Get worker subdomain URL"""
        return f"https://{worker_name}.{account_id}.workers.dev"
    
    def get_custom_domain_url(self, domain_name):
        """Get custom domain URL"""
        return f"https://{domain_name}"
    
    def deploy_to_domain(self, domain_info, deployment_type="subdomain"):
        """Deploy worker to selected domain"""
        account_id = self.config['cloudflare']['account_id']
        worker_name = self.config['cloudflare']['worker_name']
        
        if deployment_type == "subdomain":
            # Deploy to workers.dev subdomain
            return {
                "success": True,
                "url": self.get_worker_subdomain_url(account_id, worker_name),
                "type": "subdomain",
                "message": "Worker deployed to subdomain"
            }
        
        elif deployment_type == "custom_domain":
            # Deploy to custom domain
            zone_id = domain_info['id']
            domain_name = domain_info['name']
            
            # Create route pattern (all traffic)
            pattern = f"{domain_name}/*"
            
            # Create worker route
            route_result = self.create_worker_route(zone_id, pattern, worker_name)
            
            if route_result['success']:
                return {
                    "success": True,
                    "url": self.get_custom_domain_url(domain_name),
                    "type": "custom_domain",
                    "message": f"Worker deployed to {domain_name}",
                    "route": route_result['route']
                }
            else:
                return {
                    "success": False,
                    "error": route_result['error']
                }
        
        else:
            return {
                "success": False,
                "error": "Invalid deployment type"
            }
    
    def save_domain_config(self, selected_domain, deployment_type, zone_id=""):
        """Save domain configuration to config.json"""
        self.config['cloudflare']['selected_domain'] = selected_domain
        self.config['cloudflare']['deployment_type'] = deployment_type
        self.config['cloudflare']['zone_id'] = zone_id
        
        with open('config.json', 'w') as f:
            json.dump(self.config, f, indent=2)
        
        return True
    
    def get_current_deployment_info(self):
        """Get current deployment information"""
        deployment_type = self.config['cloudflare'].get('deployment_type', 'subdomain')
        selected_domain = self.config['cloudflare'].get('selected_domain', '')
        account_id = self.config['cloudflare']['account_id']
        worker_name = self.config['cloudflare']['worker_name']
        
        if deployment_type == "subdomain":
            url = self.get_worker_subdomain_url(account_id, worker_name)
        else:
            url = self.get_custom_domain_url(selected_domain) if selected_domain else ""
        
        return {
            "deployment_type": deployment_type,
            "selected_domain": selected_domain,
            "url": url,
            "worker_name": worker_name
        }

if __name__ == "__main__":
    # Test the domain manager
    manager = CloudflareDomainManager()
    
    # Test getting zones
    print("Testing zones...")
    zones = manager.get_zones()
    print(json.dumps(zones, indent=2))
    
    # Test current deployment info
    print("\nCurrent deployment info:")
    info = manager.get_current_deployment_info()
    print(json.dumps(info, indent=2))