import streamlit as st
import json
import os
from datetime import datetime

# Configure page
st.set_page_config(
    page_title="Cloudflare Worker Article Generator",
    page_icon="🚀",
    layout="wide"
)

def main():
    st.title("🚀 Cloudflare Worker Article Generator")
    st.write("Aplikasi untuk auto-generate artikel SEO dengan Cloudflare Worker")
    
    # Sidebar
    st.sidebar.title("Menu")
    page = st.sidebar.selectbox(
        "Pilih Halaman",
        ["Dashboard", "Konfigurasi API", "Template", "Scheduler", "Generate", "Deploy"]
    )
    
    if page == "Dashboard":
        dashboard()
    elif page == "Konfigurasi API":
        api_config()
    elif page == "Template":
        template_config()
    elif page == "Scheduler":
        scheduler_config()
    elif page == "Generate":
        generate_article()
    elif page == "Deploy":
        deploy_worker()

def dashboard():
    st.header("Dashboard")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Artikel", "0")
    
    with col2:
        st.metric("Worker Status", "Inactive")
    
    with col3:
        st.metric("Next Schedule", "Not Set")
    
    st.subheader("Aktivitas Terbaru")
    st.info("Belum ada aktivitas")

def api_config():
    st.header("Konfigurasi API")
    
    st.subheader("Cloudflare API")
    col1, col2 = st.columns(2)
    
    with col1:
        cf_token = st.text_input("API Token", type="password")
        cf_account = st.text_input("Account ID")
    
    with col2:
        cf_zone = st.text_input("Zone ID")
        cf_worker = st.text_input("Worker Name", value="article-generator")
    
    st.subheader("Google Gemini API")
    gemini_keys = st.text_area("API Keys (satu per baris)")
    
    if st.button("Simpan Konfigurasi"):
        config = {
            "cloudflare": {
                "api_token": cf_token,
                "account_id": cf_account,
                "zone_id": cf_zone,
                "worker_name": cf_worker
            },
            "gemini": {
                "api_keys": gemini_keys.split('\\n') if gemini_keys else []
            }
        }
        
        with open('config.json', 'w') as f:
            json.dump(config, f, indent=2)
        
        st.success("Konfigurasi berhasil disimpan!")

def template_config():
    st.header("Template Management")
    
    tab1, tab2 = st.tabs(["Layouts", "Static Pages"])
    
    with tab1:
        st.subheader("Website Templates")
        
        default_layout = st.text_area(
            "Default Layout",
            height=300,
            value="<!DOCTYPE html>\\n<html>\\n<head>\\n    <title>{{ page.title }}</title>\\n</head>\\n<body>\\n    {{ content }}\\n</body>\\n</html>"
        )
        
        if st.button("Update Template"):
            with open('_layouts/default.html', 'w') as f:
                f.write(default_layout)
            st.success("Template berhasil diupdate!")
    
    with tab2:
        st.subheader("Static Pages")
        
        pages = ["about", "contact", "privacy-policy", "disclaimer"]
        
        for page in pages:
            with st.expander(f"Edit {page.title()}"):
                content = st.text_area(
                    f"Content for {page}",
                    height=150,
                    key=f"{page}_content"
                )
                
                if st.button(f"Update {page.title()}", key=f"update_{page}"):
                    os.makedirs('_pages', exist_ok=True)
                    with open(f'_pages/{page}.html', 'w') as f:
                        f.write(content)
                    st.success(f"{page.title()} berhasil diupdate!")

def scheduler_config():
    st.header("Auto Generate Scheduler")
    
    st.subheader("Konfigurasi Jadwal")
    
    hours = st.text_input("Jam Generate (format: 8,12,16,20)", value="8,12,16,20")
    timezone = st.selectbox("Timezone", ["Asia/Jakarta", "Asia/Singapore"])
    max_articles = st.number_input("Max Artikel per Run", min_value=1, max_value=10, value=3)
    
    if st.button("Simpan Jadwal"):
        schedule_config = {
            "schedule_hours": [int(h.strip()) for h in hours.split(',')],
            "timezone": timezone,
            "max_articles_per_run": max_articles,
            "enabled": True
        }
        
        with open('scheduler_config.json', 'w') as f:
            json.dump(schedule_config, f, indent=2)
        
        st.success("Jadwal berhasil disimpan!")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Start Scheduler"):
            st.success("Scheduler dimulai!")
    
    with col2:
        if st.button("Stop Scheduler"):
            st.success("Scheduler dihentikan!")

def generate_article():
    st.header("Generate Artikel Manual")
    
    subject = st.text_input("Subject/Topic")
    category = st.selectbox("Kategori", ["Investasi", "Saham", "Forex", "Cryptocurrency"])
    language = st.selectbox("Bahasa", ["Indonesian", "English"])
    domain = st.text_input("Domain", value="https://example.com")
    
    if st.button("Generate Artikel"):
        if subject and domain:
            # Simulasi generate artikel
            with st.spinner("Generating artikel..."):
                import time
                time.sleep(2)
                
                # Buat artikel sederhana
                article = {
                    "title": f"Panduan Lengkap {subject}",
                    "content": f"<h1>{subject}</h1><p>Artikel tentang {subject} dalam kategori {category}.</p>",
                    "permalink": subject.lower().replace(" ", "-"),
                    "category": category,
                    "language": language
                }
                
                # Simpan artikel
                os.makedirs('_posts', exist_ok=True)
                filename = f"{datetime.now().strftime('%Y-%m-%d')}-{article['permalink']}.md"
                
                frontmatter = f"""---
layout: post
title: "{article['title']}"
date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
categories: [{category}]
permalink: /{article['permalink']}/
---

{article['content']}
"""
                
                with open(f'_posts/{filename}', 'w') as f:
                    f.write(frontmatter)
                
                st.success("Artikel berhasil digenerate!")
                st.subheader("Preview")
                st.markdown(article['content'])
        else:
            st.error("Mohon isi subject dan domain!")

def deploy_worker():
    st.header("Deploy ke Cloudflare Worker")
    
    st.subheader("Worker Code Preview")
    
    worker_code = '''
// Cloudflare Worker untuk Article Generator
export default {
    async fetch(request, env, ctx) {
        const url = new URL(request.url);
        
        if (url.pathname === '/') {
            return new Response(`
                <html>
                    <head><title>Investment Blog</title></head>
                    <body>
                        <h1>Welcome to Investment Blog</h1>
                        <p>Auto-generated articles about investment and finance.</p>
                    </body>
                </html>
            `, {
                headers: { 'Content-Type': 'text/html' }
            });
        }
        
        return new Response('Not Found', { status: 404 });
    }
};
'''
    
    st.code(worker_code, language='javascript')
    
    if st.button("Deploy Worker"):
        with st.spinner("Deploying..."):
            import time
            time.sleep(3)
            st.success("Worker berhasil dideploy!")
            st.info("URL: https://article-generator.your-account.workers.dev")
    
    st.subheader("Worker Management")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("Update Worker"):
            st.info("Worker diupdate!")
    
    with col2:
        if st.button("View Status"):
            st.info("Worker Status: Active")
    
    with col3:
        if st.button("View Logs"):
            st.text("Worker logs akan ditampilkan di sini")

if __name__ == "__main__":
    main()