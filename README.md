# Cloudflare Worker Article Generator

Aplikasi Streamlit untuk auto-generate artikel SEO dengan integrasi Cloudflare Worker.

## Fitur

- ✅ Auto-generate artikel dengan AI (Google Gemini)
- ✅ Deploy otomatis ke Cloudflare Worker
- ✅ Scheduler otomatis setiap jam
- ✅ Template website yang SEO-friendly
- ✅ Halaman statis (About, Contact, Privacy Policy, Disclaimer)
- ✅ Sitemap dan RSS feed otomatis
- ✅ Auto-categorization dan tagging
- ✅ Permalink SEO-friendly (domain/permalink)
- ✅ Responsive design dan AdSense ready

## Cara Penggunaan

1. **Jalankan aplikasi Streamlit:**
   ```bash
   streamlit run streamlit_app.py
   ```

2. **Konfigurasi API:**
   - Masukkan Cloudflare API Token dan Account ID
   - Tambahkan Google Gemini API Keys
   - Konfigurasi domain dan worker name

3. **Setup Template:**
   - Customize layout dan styling
   - Edit halaman statis (About, Contact, dll)
   - Sesuaikan CSS untuk branding

4. **Konfigurasi Scheduler:**
   - Set jam otomatis generation (contoh: 8,12,16,20)
   - Tentukan maksimal artikel per run
   - Pilih timezone

5. **Deploy ke Cloudflare Worker:**
   - Generate worker code
   - Deploy ke Cloudflare
   - Worker akan auto-update setiap ada artikel baru

## Struktur Folder

```
├── streamlit_app.py          # Main Streamlit application
├── cloudflare_worker.py      # Cloudflare Worker manager
├── article_generator.py      # Article generation engine
├── template_manager.py       # Template dan static pages
├── cron_scheduler.py         # Scheduler untuk auto-generation
├── config.json              # Konfigurasi API dan settings
├── subjects.txt             # Daftar topik artikel
├── _layouts/                # Template layouts
├── _pages/                  # Static pages
├── _posts/                  # Generated articles
└── assets/                  # CSS dan static files
```

## Konfigurasi

### Cloudflare API
- API Token: Diperlukan untuk deploy worker
- Account ID: ID akun Cloudflare
- Zone ID: ID zona untuk custom domain
- Worker Name: Nama worker (default: article-generator)

### Google Gemini API
- API Keys: Tambahkan multiple keys untuk load balancing
- Model: Menggunakan gemini-1.5-flash untuk kecepatan optimal

### Scheduler
- Schedule Hours: Jam otomatis generation (format: 8,12,16,20)
- Timezone: Timezone untuk scheduling
- Max Articles: Maksimal artikel per run

## Deployment

Aplikasi ini dirancang untuk deployment ke Streamlit Cloud atau platform hosting Streamlit lainnya.

### Untuk Cloudflare Worker:
1. Worker akan auto-deploy dengan konfigurasi yang telah diset
2. Worker akan handle routing, static pages, dan serving artikel
3. Sitemap dan RSS feed akan otomatis ter-generate

## Fitur SEO

- Meta tags yang comprehensive
- Open Graph untuk social sharing
- Schema.org structured data
- Sitemap.xml otomatis
- RSS feed otomatis
- URL structure yang SEO-friendly
- Internal linking otomatis

## Troubleshooting

1. **API Key Error:** Pastikan API keys valid dan memiliki quota
2. **Deployment Error:** Periksa Cloudflare credentials dan permissions
3. **Scheduler Issue:** Pastikan timezone dan format jam sudah benar
4. **Template Error:** Periksa syntax HTML dan CSS

## Support

Untuk bantuan dan support, silakan hubungi melalui interface Streamlit atau check logs di dashboard aplikasi.