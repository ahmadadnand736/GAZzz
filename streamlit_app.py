import streamlit as st
import json
import os
import requests
import schedule
import time
import threading
from datetime import datetime
from cloudflare_worker import CloudflareWorkerManager
from article_generator import ArticleGenerator
from template_manager import TemplateManager
from cron_scheduler import CronScheduler

# Configure Streamlit page
st.set_page_config(
    page_title="Cloudflare Worker Article Generator",
    page_icon="🚀",
    layout="wide"
)

# Initialize session state
if 'worker_manager' not in st.session_state:
    st.session_state.worker_manager = CloudflareWorkerManager()
if 'article_generator' not in st.session_state:
    st.session_state.article_generator = ArticleGenerator()
if 'template_manager' not in st.session_state:
    st.session_state.template_manager = TemplateManager()
if 'cron_scheduler' not in st.session_state:
    st.session_state.cron_scheduler = CronScheduler()

def main():
    st.title("🚀 Cloudflare Worker Article Generator")
    st.sidebar.title("Navigasi")
    
    # Sidebar navigation
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
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Artikel", "0", "0")
    
    with col2:
        st.metric("Worker Status", "Inactive", "")
    
    with col3:
        st.metric("Scheduler Status", "Stopped", "")
    
    st.subheader("Aktivitas Terbaru")
    
    # Log aktivitas
    if 'activity_log' not in st.session_state:
        st.session_state.activity_log = []
    
    if st.session_state.activity_log:
        for log in st.session_state.activity_log[-10:]:  # Show last 10 activities
            st.text(f"{log['timestamp']}: {log['message']}")
    else:
        st.info("Belum ada aktivitas")

def show_api_config():
    st.header("Konfigurasi API")
    
    # Cloudflare API Configuration
    st.subheader("Cloudflare API")
    
    col1, col2 = st.columns(2)
    
    with col1:
        cf_api_token = st.text_input("Cloudflare API Token", type="password")
        cf_account_id = st.text_input("Account ID")
    
    with col2:
        cf_zone_id = st.text_input("Zone ID") 
        cf_worker_name = st.text_input("Worker Name", value="article-generator")
    
    # Google Gemini API Configuration
    st.subheader("Google Gemini API")
    gemini_api_keys = st.text_area("API Keys (satu per baris)")
    
    if st.button("Simpan Konfigurasi"):
        config = {
            "cloudflare": {
                "api_token": cf_api_token,
                "account_id": cf_account_id,
                "zone_id": cf_zone_id,
                "worker_name": cf_worker_name
            },
            "gemini": {
                "api_keys": gemini_api_keys.split('\n') if gemini_api_keys else []
            }
        }
        
        with open('config.json', 'w') as f:
            json.dump(config, f, indent=2)
        
        st.success("Konfigurasi berhasil disimpan!")

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
    
    # Worker code preview
    st.subheader("Worker Code Preview")
    
    worker_code = st.session_state.worker_manager.generate_worker_code()
    st.code(worker_code, language='javascript')
    
    # Deploy button
    if st.button("Deploy Worker"):
        try:
            with st.spinner("Deploying worker..."):
                result = st.session_state.worker_manager.deploy_worker()
                if result['success']:
                    st.success(f"Worker berhasil dideploy! URL: {result['url']}")
                else:
                    st.error(f"Deployment gagal: {result['error']}")
        except Exception as e:
            st.error(f"Error deploying worker: {str(e)}")
    
    # Worker management
    st.subheader("Worker Management")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("Update Worker"):
            st.info("Updating worker...")
    
    with col2:
        if st.button("Delete Worker"):
            st.warning("Worker akan dihapus!")
    
    with col3:
        if st.button("View Logs"):
            st.info("Menampilkan logs...")

if __name__ == "__main__":
    main()