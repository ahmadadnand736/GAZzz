import streamlit as st
import json
import os
import requests
from datetime import datetime

# Configure Streamlit page
st.set_page_config(
    page_title="Cloudflare Worker Article Generator",
    page_icon="🚀",
    layout="wide"
)

# Load configuration
@st.cache_data
def load_config():
    try:
        with open('config.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {
            "cloudflare": {
                "api_token": "FdAOb0lSWzYXJV1bw7wu7LzXWALPjSOnbKkT9vKh",
                "account_id": "a418be812e4b0653ca1512804285e4a0",
                "zone_id": "",
                "worker_name": "article-generator"
            },
            "gemini": {"api_keys": []}
        }

# Test Cloudflare connection
def test_cloudflare_connection():
    config = load_config()
    headers = {
        "Authorization": f"Bearer {config['cloudflare']['api_token']}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get("https://api.cloudflare.com/client/v4/user/tokens/verify", headers=headers)
        return response.json()
    except Exception as e:
        return {"error": str(e)}

def main():
    st.title("🚀 Cloudflare Worker Article Generator")
    st.write("Aplikasi untuk auto-generate artikel SEO dengan Cloudflare Worker")
    
    # Sidebar navigation
    st.sidebar.title("Navigasi")
    page = st.sidebar.selectbox(
        "Pilih Halaman",
        ["Dashboard", "Konfigurasi API", "Template Management", "Scheduler", "Generate Manual", "Deploy Worker"]
    )
    
    if page == "Dashboard":
        show_dashboard()
    elif page == "Konfigurasi API":
        show_api_config()
    elif page == "Template Management":
        show_template_management()
    elif page == "Scheduler":
        show_scheduler()
    elif page == "Generate Manual":
        show_manual_generation()
    elif page == "Deploy Worker":
        show_deploy_worker()

def show_dashboard():
    st.header("Dashboard")
    
    # Test Cloudflare connection
    cf_status = test_cloudflare_connection()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Count articles in _posts folder
        article_count = 0
        if os.path.exists('_posts'):
            article_count = len([f for f in os.listdir('_posts') if f.endswith('.md')])
        st.metric("Total Artikel", str(article_count))
    
    with col2:
        if "success" in cf_status and cf_status["success"]:
            st.metric("Cloudflare Status", "✅ Connected")
        else:
            st.metric("Cloudflare Status", "❌ Error")
    
    with col3:
        st.metric("Worker Status", "Ready to Deploy")
    
    st.subheader("Cloudflare Connection Test")
    
    if st.button("Test Connection"):
        with st.spinner("Testing Cloudflare connection..."):
            result = test_cloudflare_connection()
            st.json(result)
    
    st.subheader("Aktivitas Terbaru")
    
    # Show recent files
    if os.path.exists('_posts'):
        posts = os.listdir('_posts')
        if posts:
            st.write("Generated Articles:")
            for post in sorted(posts)[-5:]:  # Show last 5 posts
                st.text(f"📄 {post}")
        else:
            st.info("Belum ada artikel yang di-generate")
    else:
        st.info("Belum ada aktivitas")

def show_api_config():
    st.header("Konfigurasi API")
    
    # Load current config
    config = load_config()
    
    # Worker Target Configuration
    st.subheader("Worker Target Configuration")
    
    # Current worker info
    current_worker = config['cloudflare'].get('worker_name', 'weathered-bonus-2b87')
    current_url = config['cloudflare'].get('target_url', 'https://weathered-bonus-2b87.ahmadadnand736.workers.dev')
    
    st.info(f"Current Target: {current_worker}")
    st.info(f"Current URL: {current_url}")
    
    # Manual worker configuration
    st.subheader("Manual Worker Configuration")
    
    col1, col2 = st.columns(2)
    
    with col1:
        new_worker_name = st.text_input("Worker Name", value=current_worker)
    
    with col2:
        new_worker_url = st.text_input("Worker URL", value=current_url)
    
    if st.button("Update Worker Configuration"):
        # Update config with new worker info
        config['cloudflare']['worker_name'] = new_worker_name
        config['cloudflare']['target_url'] = new_worker_url
        
        with open('config.json', 'w') as f:
            json.dump(config, f, indent=2)
        
        st.success("Worker configuration updated!")
        st.rerun()
    
    # Test current worker
    if st.button("Test Current Worker URL"):
        try:
            response = requests.get(current_url, timeout=10)
            if response.status_code == 200:
                st.success(f"Worker accessible at {current_url}")
                st.text(f"Response: {response.text[:200]}...")
            else:
                st.warning(f"Worker returned status {response.status_code}")
        except Exception as e:
            st.error(f"Could not reach worker: {str(e)}")
    
    # API Token Instructions
    st.subheader("API Token Setup")
    
    # Check current API status
    if st.button("Test API Connection"):
        try:
            headers = {
                "Authorization": f"Bearer {config['cloudflare']['api_token']}",
                "Content-Type": "application/json"
            }
            response = requests.get("https://api.cloudflare.com/client/v4/user/tokens/verify", headers=headers)
            result = response.json()
            
            if result.get('success'):
                st.success("✅ API Token is valid!")
                st.json(result.get('result', {}))
            else:
                st.error("❌ API Token is invalid or has insufficient permissions")
                st.json(result.get('errors', []))
        except Exception as e:
            st.error(f"Connection error: {str(e)}")
    
    with st.expander("📋 API Token Setup Instructions"):
        st.markdown("""
        **Your current API token needs proper permissions. Follow these steps:**
        
        1. **Go to Cloudflare Dashboard**
           - Visit: https://dash.cloudflare.com/profile/api-tokens
           - Click "Create Token"
        
        2. **Choose Custom Token**
           - Click "Custom token" → "Get started"
        
        3. **Configure Permissions**
           - **Zone permissions:**
             - Zone:Zone:Read
             - Zone:Zone Settings:Read
           - **Account permissions:**
             - Account:Cloudflare Workers:Edit
             - Account:Account Settings:Read
        
        4. **Set Resources**
           - **Account Resources:** Include all accounts
           - **Zone Resources:** Include all zones
        
        5. **Generate Token**
           - Click "Continue to summary"
           - Click "Create Token"
           - **Copy the token immediately**
        
        6. **Update Configuration**
           - Paste the new token in the field below
           - Click "Simpan Konfigurasi"
        
        **Target Worker:** weathered-bonus-2b87
        **Target URL:** https://weathered-bonus-2b87.ahmadadnand736.workers.dev
        """)
    
    # Deployment status
    st.subheader("Current Deployment Status")
    
    if st.button("Check Worker Status"):
        try:
            worker_url = "https://weathered-bonus-2b87.ahmadadnand736.workers.dev"
            response = requests.get(worker_url, timeout=10)
            
            if response.status_code == 200:
                st.success("✅ Worker is active and responding")
                st.text("Response preview:")
                st.code(response.text[:500] + "..." if len(response.text) > 500 else response.text)
            elif response.status_code == 404:
                st.warning("⚠️ Worker exists but no content deployed")
                st.info("You can deploy your article generator to this worker")
            else:
                st.error(f"❌ Worker returned status {response.status_code}")
        except Exception as e:
            st.error(f"Could not reach worker: {str(e)}")
    
    # Cloudflare API Configuration
    st.subheader("Cloudflare API")
    
    col1, col2 = st.columns(2)
    
    with col1:
        cf_api_token = st.text_input("Cloudflare API Token", 
                                   value=config['cloudflare']['api_token'], 
                                   type="password")
        cf_account_id = st.text_input("Account ID", 
                                    value=config['cloudflare']['account_id'])
    
    with col2:
        cf_zone_id = st.text_input("Zone ID", 
                                 value=config['cloudflare'].get('zone_id', '')) 
        cf_worker_name = st.text_input("Worker Name", 
                                     value=config['cloudflare'].get('worker_name', 'article-generator'))
    
    # Domain Selection
    st.subheader("Domain Configuration")
    
    # Get available domains
    from cloudflare_domains import CloudflareDomainManager
    domain_manager = CloudflareDomainManager()
    
    if st.button("Load Domains from Cloudflare"):
        with st.spinner("Loading domains..."):
            zones_result = domain_manager.get_zones()
            
            if zones_result['success']:
                st.session_state.available_domains = zones_result['zones']
                st.success(f"Loaded {len(zones_result['zones'])} domains")
            else:
                st.error(f"Failed to load domains: {zones_result['error']}")
    
    # Domain selection
    if 'available_domains' in st.session_state:
        st.subheader("Select Domain for Deployment")
        
        deployment_type = st.radio(
            "Deployment Type",
            ["subdomain", "custom_domain"],
            index=0 if config['cloudflare'].get('deployment_type') == 'subdomain' else 1,
            format_func=lambda x: "Workers.dev Subdomain" if x == "subdomain" else "Custom Domain"
        )
        
        if deployment_type == "subdomain":
            st.info(f"Worker akan di-deploy ke: https://{cf_worker_name}.{cf_account_id}.workers.dev")
            selected_domain = ""
            selected_zone_id = ""
        else:
            # Show available domains
            domain_options = [""] + [f"{domain['name']} ({domain['status']})" for domain in st.session_state.available_domains]
            selected_domain_display = st.selectbox("Select Domain", domain_options)
            
            if selected_domain_display:
                # Find selected domain info
                domain_name = selected_domain_display.split(' (')[0]
                selected_domain_info = next((d for d in st.session_state.available_domains if d['name'] == domain_name), None)
                
                if selected_domain_info:
                    selected_domain = selected_domain_info['name']
                    selected_zone_id = selected_domain_info['id']
                    st.info(f"Worker akan di-deploy ke: https://{selected_domain}")
                    st.json({
                        "Domain": selected_domain_info['name'],
                        "Status": selected_domain_info['status'],
                        "Plan": selected_domain_info['plan']
                    })
                else:
                    selected_domain = ""
                    selected_zone_id = ""
            else:
                selected_domain = ""
                selected_zone_id = ""
        
        # Save domain config
        if st.button("Save Domain Configuration"):
            domain_manager.save_domain_config(selected_domain, deployment_type, selected_zone_id)
            st.success("Domain configuration saved!")
    
    # Google Gemini API Configuration
    st.subheader("Google Gemini API")
    gemini_api_keys = st.text_area("API Keys (satu per baris)", 
                                  value='\n'.join(config['gemini']['api_keys']))
    
    if st.button("Simpan Konfigurasi"):
        new_config = {
            "cloudflare": {
                "api_token": cf_api_token,
                "account_id": cf_account_id,
                "zone_id": cf_zone_id,
                "worker_name": cf_worker_name,
                "selected_domain": config['cloudflare'].get('selected_domain', ''),
                "deployment_type": config['cloudflare'].get('deployment_type', 'subdomain')
            },
            "gemini": {
                "api_keys": gemini_api_keys.split('\n') if gemini_api_keys else []
            },
            "domain": config.get('domain', 'https://example.com'),
            "site_title": config.get('site_title', 'Investment Blog'),
            "site_description": config.get('site_description', 'Blog investasi dan keuangan terpercaya')
        }
        
        with open('config.json', 'w') as f:
            json.dump(new_config, f, indent=2)
        
        st.success("Konfigurasi berhasil disimpan!")
        st.rerun()

def show_template_management():
    st.header("Template Management")
    
    # Template tabs
    tab1, tab2, tab3 = st.tabs(["Layouts", "Pages", "Static Assets"])
    
    with tab1:
        st.subheader("Website Templates")
        
        # Default layout editor
        default_layout = st.text_area(
            "Default Layout (HTML)",
            height=300,
            value=st.session_state.template_manager.get_default_layout()
        )
        
        # Post layout editor
        post_layout = st.text_area(
            "Post Layout (HTML)",
            height=300,
            value=st.session_state.template_manager.get_post_layout()
        )
        
        if st.button("Update Templates"):
            st.session_state.template_manager.update_layouts(default_layout, post_layout)
            st.success("Templates berhasil diupdate!")
    
    with tab2:
        st.subheader("Static Pages")
        
        pages = ["about", "contact", "privacy-policy", "disclaimer"]
        
        for page in pages:
            with st.expander(f"Edit {page.title()} Page"):
                content = st.text_area(
                    f"{page.title()} Content",
                    height=200,
                    key=f"{page}_content"
                )
                
                if st.button(f"Update {page.title()}", key=f"update_{page}"):
                    st.session_state.template_manager.update_page(page, content)
                    st.success(f"{page.title()} page berhasil diupdate!")
    
    with tab3:
        st.subheader("CSS & Static Files")
        
        css_content = st.text_area(
            "Custom CSS",
            height=200,
            value=st.session_state.template_manager.get_css()
        )
        
        if st.button("Update CSS"):
            st.session_state.template_manager.update_css(css_content)
            st.success("CSS berhasil diupdate!")

def show_scheduler():
    st.header("Auto Generate Scheduler")
    
    # Schedule configuration
    st.subheader("Konfigurasi Jadwal")
    
    schedule_hours = st.text_input(
        "Jam Generate (format: 8,12,16,20)",
        placeholder="8,12,16,20"
    )
    
    timezone = st.selectbox(
        "Timezone",
        ["Asia/Jakarta", "Asia/Kuala_Lumpur", "Asia/Singapore"]
    )
    
    max_articles_per_run = st.number_input(
        "Maksimal Artikel per Run",
        min_value=1,
        max_value=10,
        value=3
    )
    
    if st.button("Simpan Jadwal"):
        if schedule_hours:
            hours = [int(h.strip()) for h in schedule_hours.split(',')]
            st.session_state.cron_scheduler.set_schedule(hours, timezone, max_articles_per_run)
            st.success("Jadwal berhasil disimpan!")
        else:
            st.error("Masukkan jam yang valid!")
    
    # Scheduler status
    st.subheader("Status Scheduler")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Start Scheduler"):
            st.session_state.cron_scheduler.start()
            st.success("Scheduler dimulai!")
    
    with col2:
        if st.button("Stop Scheduler"):
            st.session_state.cron_scheduler.stop()
            st.success("Scheduler dihentikan!")
    
    # Next run info
    next_run = st.session_state.cron_scheduler.get_next_run()
    if next_run:
        st.info(f"Next run: {next_run}")

def show_manual_generation():
    st.header("Generate Artikel Manual")
    
    # Subject input
    subject = st.text_input("Subject/Topic")
    
    # Category selection
    categories = ["Investasi", "Saham", "Forex", "Cryptocurrency", "Finansial", "Ekonomi"]
    category = st.selectbox("Kategori", categories)
    
    # Language selection
    language = st.selectbox("Bahasa", ["Indonesian", "English"])
    
    # Domain configuration
    domain = st.text_input("Domain", placeholder="https://example.com")
    
    if st.button("Generate Artikel"):
        if subject and domain:
            with st.spinner("Generating artikel..."):
                try:
                    article = st.session_state.article_generator.generate_article(
                        subject=subject,
                        category=category,
                        language=language,
                        domain=domain
                    )
                    
                    st.success("Artikel berhasil digenerate!")
                    
                    # Preview article
                    st.subheader("Preview Artikel")
                    st.markdown(article['content'])
                    
                    # Show metadata
                    st.subheader("Metadata")
                    st.json(article['metadata'])
                    
                except Exception as e:
                    st.error(f"Error generating artikel: {str(e)}")
        else:
            st.error("Mohon isi subject dan domain!")

def show_deploy_worker():
    st.header("Deploy ke Cloudflare Worker")
    
    # Import the deployment functions
    from cloudflare_deploy import deploy_cloudflare_worker, get_worker_status
    from cloudflare_domains import CloudflareDomainManager
    
    # Load current config
    config = load_config()
    domain_manager = CloudflareDomainManager()
    deployment_info = domain_manager.get_current_deployment_info()
    
    # Show current deployment configuration
    st.subheader("Current Deployment Configuration")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.info(f"**Deployment Type:** {deployment_info['deployment_type'].title()}")
        st.info(f"**Worker Name:** {deployment_info['worker_name']}")
    
    with col2:
        if deployment_info['deployment_type'] == 'custom_domain':
            st.info(f"**Domain:** {deployment_info['selected_domain']}")
        st.info(f"**Target URL:** {deployment_info['url']}")
    
    # Check current worker status
    st.subheader("Worker Status")
    
    if st.button("Check Status"):
        with st.spinner("Checking worker status..."):
            status = get_worker_status()
            st.json(status)
    
    # Deploy button
    st.subheader("Deploy Worker")
    
    if st.button("Deploy Worker", type="primary"):
        try:
            with st.spinner("Deploying worker..."):
                # First deploy the worker script
                result = deploy_cloudflare_worker()
                
                if result['success']:
                    st.success(f"✅ Worker script deployed successfully!")
                    
                    # If custom domain is selected, create route
                    if deployment_info['deployment_type'] == 'custom_domain' and deployment_info['selected_domain']:
                        with st.spinner("Setting up custom domain route..."):
                            zone_id = config['cloudflare']['zone_id']
                            domain_info = {
                                'id': zone_id,
                                'name': deployment_info['selected_domain']
                            }
                            
                            domain_result = domain_manager.deploy_to_domain(domain_info, 'custom_domain')
                            
                            if domain_result['success']:
                                st.success(f"✅ Custom domain route created!")
                                st.info(f"🌐 Worker available at: {domain_result['url']}")
                                st.json(domain_result.get('route', {}))
                            else:
                                st.error(f"❌ Custom domain setup failed: {domain_result['error']}")
                                st.info(f"Worker still available at subdomain: {result['url']}")
                    else:
                        st.info(f"🌐 Worker available at: {result['url']}")
                    
                    st.json(result.get('response', {}))
                else:
                    st.error(f"❌ {result['message']}")
                    if 'status_code' in result:
                        st.error(f"Status Code: {result['status_code']}")
        except Exception as e:
            st.error(f"Error deploying worker: {str(e)}")
    
    # Worker management
    st.subheader("Worker Management")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("Update Worker"):
            with st.spinner("Updating worker..."):
                result = deploy_cloudflare_worker()
                if result['success']:
                    st.success("Worker berhasil diupdate!")
                else:
                    st.error("Update gagal!")
    
    with col2:
        if st.button("Test Worker"):
            st.info("Testing worker...")
            try:
                import requests
                test_url = deployment_info['url']
                response = requests.get(test_url, timeout=10)
                if response.status_code == 200:
                    st.success("✅ Worker berjalan dengan baik!")
                    st.text(f"Response length: {len(response.text)} characters")
                else:
                    st.error(f"❌ Worker error: {response.status_code}")
            except Exception as e:
                st.error(f"Test error: {str(e)}")
    
    with col3:
        if st.button("View Worker"):
            st.info("Opening worker URL...")
            st.markdown(f"[Open Worker]({deployment_info['url']})")
    
    # Domain Routes Management (for custom domains)
    if deployment_info['deployment_type'] == 'custom_domain' and deployment_info['selected_domain']:
        st.subheader("Domain Routes Management")
        
        zone_id = config['cloudflare']['zone_id']
        
        if st.button("View Current Routes"):
            with st.spinner("Loading routes..."):
                routes_result = domain_manager.get_worker_routes(zone_id)
                
                if routes_result['success']:
                    st.json(routes_result['routes'])
                else:
                    st.error(f"Failed to load routes: {routes_result['error']}")
    
    # Worker code preview
    st.subheader("Worker Code Preview")
    
    with st.expander("View Generated Worker Code"):
        from cloudflare_deploy import generate_worker_code
        worker_code = generate_worker_code()
        st.code(worker_code[:2000] + "..." if len(worker_code) > 2000 else worker_code, language='javascript')

if __name__ == "__main__":
    main()