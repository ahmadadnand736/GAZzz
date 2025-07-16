import requests
import json
import os
from datetime import datetime

def deploy_cloudflare_worker():
    """Deploy worker to Cloudflare with your credentials"""
    
    # Load configuration
    try:
        with open('config.json', 'r') as f:
            full_config = json.load(f)
            config = full_config['cloudflare']
    except FileNotFoundError:
        config = {
            "api_token": "FdAOb0lSWzYXJV1bw7wu7LzXWALPjSOnbKkT9vKh",
            "account_id": "a418be812e4b0653ca1512804285e4a0",
            "worker_name": "article-generator",
            "selected_domain": "",
            "deployment_type": "subdomain"
        }
    
    # Generate worker code
    worker_code = generate_worker_code()
    
    # Deploy worker
    url = f"https://api.cloudflare.com/client/v4/accounts/{config['account_id']}/workers/scripts/{config['worker_name']}"
    
    headers = {
        "Authorization": f"Bearer {config['api_token']}",
        "Content-Type": "application/javascript"
    }
    
    try:
        response = requests.put(url, headers=headers, data=worker_code)
        
        if response.status_code == 200:
            return {
                "success": True,
                "message": "Worker berhasil dideploy!",
                "url": f"https://{config['worker_name']}.{config['account_id']}.workers.dev",
                "response": response.json()
            }
        else:
            return {
                "success": False,
                "message": f"Deploy gagal: {response.text}",
                "status_code": response.status_code
            }
    except Exception as e:
        return {
            "success": False,
            "message": f"Error: {str(e)}"
        }

def generate_worker_code():
    """Generate complete Cloudflare Worker code"""
    
    # Load articles from _posts folder
    articles_data = []
    if os.path.exists('_posts'):
        for filename in os.listdir('_posts'):
            if filename.endswith('.md'):
                with open(f'_posts/{filename}', 'r', encoding='utf-8') as f:
                    content = f.read()
                    articles_data.append({
                        'filename': filename,
                        'content': content
                    })
    
    # Generate worker code
    worker_code = f'''
// Auto-generated Cloudflare Worker untuk Article Generator
// Generated pada: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

// Website data
const ARTICLES = {json.dumps(articles_data)};

const SITE_CONFIG = {{
    title: "Investment Blog",
    description: "Blog investasi dan keuangan terpercaya",
    domain: "https://article-generator.a418be812e4b0653ca1512804285e4a0.workers.dev"
}};

// Static pages content
const STATIC_PAGES = {{
    'about': `
        <h1>About Us</h1>
        <p>Selamat datang di blog investasi dan keuangan terpercaya. Kami berkomitmen menyediakan informasi terkini tentang investasi, saham, forex, dan cryptocurrency.</p>
        <h2>Misi Kami</h2>
        <p>Membantu Anda mencapai kebebasan finansial melalui pengetahuan investasi yang tepat.</p>
    `,
    'contact': `
        <h1>Contact Us</h1>
        <p>Hubungi kami untuk pertanyaan atau saran:</p>
        <ul>
            <li>Email: info@investmentblog.com</li>
            <li>Telepon: +62 21 1234 5678</li>
        </ul>
    `,
    'privacy-policy': `
        <h1>Privacy Policy</h1>
        <p>Kebijakan privasi kami melindungi data personal Anda...</p>
    `,
    'disclaimer': `
        <h1>Disclaimer</h1>
        <p>Informasi di website ini hanya untuk tujuan edukasi. Konsultasikan dengan ahli keuangan sebelum membuat keputusan investasi.</p>
    `
}};

// CSS Styles
const CSS_STYLES = `
body {{
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    line-height: 1.6;
    color: #333;
    max-width: 800px;
    margin: 0 auto;
    padding: 20px;
    background-color: #f9f9f9;
}}

header {{
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 2rem;
    text-align: center;
    border-radius: 10px;
    margin-bottom: 2rem;
}}

header h1 {{
    margin: 0;
    font-size: 2.5rem;
}}

header p {{
    margin: 0.5rem 0 0 0;
    opacity: 0.9;
}}

.container {{
    background: white;
    padding: 2rem;
    border-radius: 10px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    margin-bottom: 2rem;
}}

.post-meta {{
    color: #666;
    font-size: 0.9rem;
    margin-bottom: 1rem;
}}

.post-content h2 {{
    color: #667eea;
    border-bottom: 2px solid #667eea;
    padding-bottom: 0.5rem;
}}

.post-content h3 {{
    color: #764ba2;
}}

.post-tags {{
    margin-top: 2rem;
    padding-top: 1rem;
    border-top: 1px solid #eee;
}}

.tag {{
    display: inline-block;
    background: #667eea;
    color: white;
    padding: 0.25rem 0.75rem;
    border-radius: 15px;
    font-size: 0.8rem;
    margin-right: 0.5rem;
    margin-bottom: 0.5rem;
    text-decoration: none;
}}

.tag:hover {{
    background: #764ba2;
}}

.articles-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 2rem;
    margin-top: 2rem;
}}

.article-card {{
    background: white;
    border-radius: 10px;
    padding: 1.5rem;
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    transition: transform 0.3s ease;
}}

.article-card:hover {{
    transform: translateY(-5px);
}}

.article-card h3 {{
    margin: 0 0 1rem 0;
    color: #667eea;
}}

.article-card p {{
    color: #666;
    margin-bottom: 1rem;
}}

.article-card a {{
    color: #667eea;
    text-decoration: none;
    font-weight: bold;
}}

.article-card a:hover {{
    text-decoration: underline;
}}

footer {{
    text-align: center;
    margin-top: 3rem;
    padding-top: 2rem;
    border-top: 1px solid #ddd;
    color: #666;
}}

.nav-links {{
    text-align: center;
    margin: 2rem 0;
}}

.nav-links a {{
    display: inline-block;
    margin: 0 1rem;
    padding: 0.5rem 1rem;
    background: #667eea;
    color: white;
    text-decoration: none;
    border-radius: 5px;
    transition: background 0.3s ease;
}}

.nav-links a:hover {{
    background: #764ba2;
}}

@media (max-width: 768px) {{
    body {{
        padding: 10px;
    }}
    
    header h1 {{
        font-size: 2rem;
    }}
    
    .articles-grid {{
        grid-template-columns: 1fr;
    }}
}}
`;

// Helper functions
function parseMarkdown(content) {{
    // Parse frontmatter
    const parts = content.split('---');
    if (parts.length < 3) return null;
    
    const frontmatter = parts[1];
    const body = parts.slice(2).join('---');
    
    // Parse YAML frontmatter (simple parsing)
    const meta = {{}};
    frontmatter.split('\\n').forEach(line => {{
        const [key, ...valueParts] = line.split(':');
        if (key && valueParts.length > 0) {{
            let value = valueParts.join(':').trim();
            value = value.replace(/^["']|["']$/g, ''); // Remove quotes
            meta[key.trim()] = value;
        }}
    }});
    
    // Simple markdown to HTML conversion
    let html = body
        .replace(/^### (.+)$/gm, '<h3>$1</h3>')
        .replace(/^## (.+)$/gm, '<h2>$1</h2>')
        .replace(/^# (.+)$/gm, '<h1>$1</h1>')
        .replace(/\\*\\*(.+?)\\*\\*/g, '<strong>$1</strong>')
        .replace(/\\*(.+?)\\*/g, '<em>$1</em>')
        .replace(/\\n\\n/g, '</p><p>')
        .replace(/^(.+)$/gm, '<p>$1</p>')
        .replace(/<p><h/g, '<h')
        .replace(/<\\/h([1-6])><\\/p>/g, '</h$1>');
    
    return {{ meta, html }};
}}

function generateSitemap() {{
    const baseUrl = SITE_CONFIG.domain;
    const now = new Date().toISOString();
    
    let sitemap = `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
    <url>
        <loc>${{baseUrl}}/</loc>
        <lastmod>${{now}}</lastmod>
        <changefreq>daily</changefreq>
        <priority>1.0</priority>
    </url>`;
    
    // Add static pages
    Object.keys(STATIC_PAGES).forEach(page => {{
        sitemap += `
    <url>
        <loc>${{baseUrl}}/${{page}}/</loc>
        <lastmod>${{now}}</lastmod>
        <changefreq>monthly</changefreq>
        <priority>0.8</priority>
    </url>`;
    }});
    
    // Add articles
    ARTICLES.forEach(article => {{
        const parsed = parseMarkdown(article.content);
        if (parsed && parsed.meta.permalink) {{
            sitemap += `
    <url>
        <loc>${{baseUrl}}${{parsed.meta.permalink}}</loc>
        <lastmod>${{parsed.meta.date || now}}</lastmod>
        <changefreq>monthly</changefreq>
        <priority>0.9</priority>
    </url>`;
        }}
    }});
    
    sitemap += `
</urlset>`;
    
    return sitemap;
}}

function generateRSSFeed() {{
    const baseUrl = SITE_CONFIG.domain;
    const now = new Date().toUTCString();
    
    let rss = `<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
    <channel>
        <title>${{SITE_CONFIG.title}}</title>
        <link>${{baseUrl}}</link>
        <description>${{SITE_CONFIG.description}}</description>
        <language>id</language>
        <pubDate>${{now}}</pubDate>
        <lastBuildDate>${{now}}</lastBuildDate>`;
    
    // Add articles to RSS
    ARTICLES.forEach(article => {{
        const parsed = parseMarkdown(article.content);
        if (parsed && parsed.meta.title) {{
            rss += `
        <item>
            <title>${{parsed.meta.title}}</title>
            <link>${{baseUrl}}${{parsed.meta.permalink || '/'}}</link>
            <description>${{parsed.meta.description || ''}}</description>
            <pubDate>${{new Date(parsed.meta.date || now).toUTCString()}}</pubDate>
            <guid>${{baseUrl}}${{parsed.meta.permalink || '/'}}</guid>
        </item>`;
        }}
    }});
    
    rss += `
    </channel>
</rss>`;
    
    return rss;
}}

function renderPage(title, content) {{
    return `<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>${{title}} - ${{SITE_CONFIG.title}}</title>
    <meta name="description" content="${{SITE_CONFIG.description}}">
    <style>${{CSS_STYLES}}</style>
</head>
<body>
    <header>
        <h1><a href="/" style="color: white; text-decoration: none;">${{SITE_CONFIG.title}}</a></h1>
        <p>${{SITE_CONFIG.description}}</p>
    </header>
    
    <div class="nav-links">
        <a href="/">Home</a>
        <a href="/about">About</a>
        <a href="/contact">Contact</a>
        <a href="/privacy-policy">Privacy</a>
        <a href="/disclaimer">Disclaimer</a>
    </div>
    
    <main class="container">
        ${{content}}
    </main>
    
    <footer>
        <p>&copy; ${{new Date().getFullYear()}} ${{SITE_CONFIG.title}}. All rights reserved.</p>
    </footer>
</body>
</html>`;
}}

function renderHomepage() {{
    let articlesHtml = '';
    
    if (ARTICLES.length > 0) {{
        articlesHtml = '<div class="articles-grid">';
        ARTICLES.forEach(article => {{
            const parsed = parseMarkdown(article.content);
            if (parsed && parsed.meta.title) {{
                articlesHtml += `
                <div class="article-card">
                    <h3><a href="${{parsed.meta.permalink || '/'}}">${{parsed.meta.title}}</a></h3>
                    <p class="post-meta">${{new Date(parsed.meta.date || Date.now()).toLocaleDateString('id-ID')}}</p>
                    <p>${{parsed.meta.description || 'Artikel tentang investasi dan keuangan...'}}</p>
                    <a href="${{parsed.meta.permalink || '/'}}">Baca Selengkapnya →</a>
                </div>`;
            }}
        }});
        articlesHtml += '</div>';
    }} else {{
        articlesHtml = '<p>Belum ada artikel tersedia.</p>';
    }}
    
    const content = `
        <h1>Selamat Datang di ${{SITE_CONFIG.title}}</h1>
        <p>Temukan artikel-artikel terbaru tentang investasi, saham, forex, dan cryptocurrency untuk membantu Anda mencapai kebebasan finansial.</p>
        
        <h2>Artikel Terbaru</h2>
        ${{articlesHtml}}
    `;
    
    return renderPage('Home', content);
}}

// Main handler
export default {{
    async fetch(request, env, ctx) {{
        const url = new URL(request.url);
        const path = url.pathname;
        
        // Handle static pages
        if (STATIC_PAGES[path.substring(1)]) {{
            const pageContent = STATIC_PAGES[path.substring(1)];
            return new Response(
                renderPage(path.substring(1).replace('-', ' ').toUpperCase(), pageContent),
                {{ headers: {{ 'Content-Type': 'text/html' }} }}
            );
        }}
        
        // Handle sitemap
        if (path === '/sitemap.xml') {{
            return new Response(generateSitemap(), {{
                headers: {{ 'Content-Type': 'application/xml' }}
            }});
        }}
        
        // Handle RSS feed
        if (path === '/feed.xml') {{
            return new Response(generateRSSFeed(), {{
                headers: {{ 'Content-Type': 'application/xml' }}
            }});
        }}
        
        // Handle article pages
        if (path.startsWith('/') && path.length > 1) {{
            const article = ARTICLES.find(a => {{
                const parsed = parseMarkdown(a.content);
                return parsed && parsed.meta.permalink === path;
            }});
            
            if (article) {{
                const parsed = parseMarkdown(article.content);
                if (parsed) {{
                    const tagsHtml = parsed.meta.tags ? 
                        `<div class="post-tags">
                            ${{JSON.parse(parsed.meta.tags).map(tag => `<span class="tag">${{tag}}</span>`).join('')}}
                        </div>` : '';
                    
                    const content = `
                        <article>
                            <h1>${{parsed.meta.title}}</h1>
                            <div class="post-meta">
                                Dipublikasikan pada ${{new Date(parsed.meta.date || Date.now()).toLocaleDateString('id-ID')}}
                                ${{parsed.meta.categories ? ' • ' + parsed.meta.categories.replace(/[\\[\\]]/g, '') : ''}}
                            </div>
                            <div class="post-content">
                                ${{parsed.html}}
                            </div>
                            ${{tagsHtml}}
                        </article>
                    `;
                    
                    return new Response(
                        renderPage(parsed.meta.title, content),
                        {{ headers: {{ 'Content-Type': 'text/html' }} }}
                    );
                }}
            }}
        }}
        
        // Handle homepage
        if (path === '/' || path === '/index.html') {{
            return new Response(renderHomepage(), {{
                headers: {{ 'Content-Type': 'text/html' }}
            }});
        }}
        
        // 404 Not Found
        return new Response(
            renderPage('404 - Not Found', '<h1>404 - Halaman Tidak Ditemukan</h1><p>Maaf, halaman yang Anda cari tidak ditemukan.</p>'),
            {{ 
                status: 404,
                headers: {{ 'Content-Type': 'text/html' }}
            }}
        );
    }}
}};
'''
    
    return worker_code

def get_worker_status():
    """Get worker status from Cloudflare"""
    config = {
        "api_token": "FdAOb0lSWzYXJV1bw7wu7LzXWALPjSOnbKkT9vKh",
        "account_id": "a418be812e4b0653ca1512804285e4a0",
        "worker_name": "article-generator"
    }
    
    url = f"https://api.cloudflare.com/client/v4/accounts/{config['account_id']}/workers/scripts/{config['worker_name']}"
    
    headers = {
        "Authorization": f"Bearer {config['api_token']}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(url, headers=headers)
        return response.json()
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    # Test deployment
    result = deploy_cloudflare_worker()
    print(json.dumps(result, indent=2))