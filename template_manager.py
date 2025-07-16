import os
import json
from datetime import datetime

class TemplateManager:
    def __init__(self):
        self.layouts_dir = "_layouts"
        self.pages_dir = "_pages"
        self.assets_dir = "assets"
        self.css_file = "assets/style.css"
        self.ensure_directories()
    
    def ensure_directories(self):
        """Create necessary directories if they don't exist"""
        for directory in [self.layouts_dir, self.pages_dir, self.assets_dir]:
            os.makedirs(directory, exist_ok=True)
    
    def get_default_layout(self):
        """Get default layout template"""
        default_layout = """<!DOCTYPE html>
<html lang="{{ page.lang | default: 'id' }}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% if page.title %}{{ page.title }} | {% endif %}{{ site.title | default: "Investment Blog" }}</title>
    
    <!-- SEO Meta Tags -->
    <meta name="description" content="{{ page.description | default: site.description | default: 'Blog investasi dan keuangan terpercaya' }}">
    <meta name="keywords" content="investasi, saham, forex, cryptocurrency, finansial, trading">
    <meta name="author" content="{{ page.author | default: site.author | default: 'Investment Expert' }}">
    
    <!-- Open Graph Meta Tags -->
    <meta property="og:title" content="{% if page.title %}{{ page.title }}{% else %}{{ site.title }}{% endif %}">
    <meta property="og:description" content="{{ page.description | default: site.description }}">
    <meta property="og:type" content="{% if page.layout == 'post' %}article{% else %}website{% endif %}">
    <meta property="og:url" content="{{ site.url }}{{ page.url }}">
    <meta property="og:site_name" content="{{ site.title }}">
    
    {% if page.image %}
    <meta property="og:image" content="{{ site.url }}{{ page.image }}">
    {% endif %}
    
    <!-- Twitter Card Meta Tags -->
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="{% if page.title %}{{ page.title }}{% else %}{{ site.title }}{% endif %}">
    <meta name="twitter:description" content="{{ page.description | default: site.description }}">
    {% if page.image %}
    <meta name="twitter:image" content="{{ site.url }}{{ page.image }}">
    {% endif %}
    
    <!-- Schema.org structured data -->
    <script type="application/ld+json">
    {
        "@context": "https://schema.org",
        "@type": "{% if page.layout == 'post' %}Article{% else %}WebSite{% endif %}",
        "name": "{% if page.title %}{{ page.title }}{% else %}{{ site.title }}{% endif %}",
        "description": "{{ page.description | default: site.description }}",
        "url": "{{ site.url }}{{ page.url }}",
        {% if page.layout == 'post' %}
        "author": {
            "@type": "Person",
            "name": "{{ page.author | default: 'Investment Expert' }}"
        },
        "datePublished": "{{ page.date | date_to_xmlschema }}",
        "dateModified": "{{ page.date | date_to_xmlschema }}",
        {% endif %}
        "publisher": {
            "@type": "Organization",
            "name": "{{ site.title }}",
            "url": "{{ site.url }}"
        }
    }
    </script>
    
    <!-- CSS Styles -->
    <link rel="stylesheet" href="/assets/style.css">
    
    <!-- Favicon -->
    <link rel="icon" type="image/x-icon" href="/favicon.ico">
    
    <!-- RSS Feed -->
    <link rel="alternate" type="application/rss+xml" title="{{ site.title }}" href="/feed.xml">
    
    <!-- Sitemap -->
    <link rel="sitemap" type="application/xml" title="Sitemap" href="/sitemap.xml">
</head>
<body>
    <!-- Header -->
    <header class="site-header">
        <nav class="navbar">
            <div class="container">
                <div class="navbar-brand">
                    <a href="/" class="logo">{{ site.title | default: "Investment Blog" }}</a>
                </div>
                <ul class="navbar-nav">
                    <li><a href="/">Home</a></li>
                    <li><a href="/about">About</a></li>
                    <li><a href="/contact">Contact</a></li>
                </ul>
            </div>
        </nav>
    </header>
    
    <!-- Main Content -->
    <main class="main-content">
        <div class="container">
            {{ content }}
        </div>
    </main>
    
    <!-- Footer -->
    <footer class="site-footer">
        <div class="container">
            <div class="footer-content">
                <div class="footer-section">
                    <h4>{{ site.title | default: "Investment Blog" }}</h4>
                    <p>{{ site.description | default: "Blog investasi dan keuangan terpercaya untuk membantu Anda meraih kebebasan finansial." }}</p>
                </div>
                <div class="footer-section">
                    <h4>Quick Links</h4>
                    <ul>
                        <li><a href="/about">About</a></li>
                        <li><a href="/contact">Contact</a></li>
                        <li><a href="/privacy-policy">Privacy Policy</a></li>
                        <li><a href="/disclaimer">Disclaimer</a></li>
                    </ul>
                </div>
                <div class="footer-section">
                    <h4>Categories</h4>
                    <ul>
                        <li><a href="/category/investasi">Investasi</a></li>
                        <li><a href="/category/saham">Saham</a></li>
                        <li><a href="/category/forex">Forex</a></li>
                        <li><a href="/category/cryptocurrency">Cryptocurrency</a></li>
                    </ul>
                </div>
            </div>
            <div class="footer-bottom">
                <p>&copy; {{ site.time | date: '%Y' }} {{ site.title | default: "Investment Blog" }}. All rights reserved.</p>
            </div>
        </div>
    </footer>
    
    <!-- Analytics (placeholder) -->
    <!-- Google Analytics or other tracking codes can be added here -->
</body>
</html>"""
        
        # Save to file
        with open(f"{self.layouts_dir}/default.html", "w", encoding="utf-8") as f:
            f.write(default_layout)
        
        return default_layout
    
    def get_post_layout(self):
        """Get post layout template"""
        post_layout = """---
layout: default
---

<article class="post" itemscope itemtype="http://schema.org/BlogPosting">
    <header class="post-header">
        <h1 class="post-title" itemprop="name headline">{{ page.title }}</h1>
        <div class="post-meta">
            <time class="post-date" datetime="{{ page.date | date_to_xmlschema }}" itemprop="datePublished">
                {{ page.date | date: "%B %d, %Y" }}
            </time>
            {% if page.author %}
            <span class="post-author" itemprop="author">by {{ page.author }}</span>
            {% endif %}
        </div>
        
        {% if page.image %}
        <div class="post-featured-image">
            <img src="{{ page.image }}" alt="{{ page.title }}" itemprop="image">
        </div>
        {% endif %}
    </header>
    
    <div class="post-content" itemprop="articleBody">
        {{ content }}
    </div>
    
    <footer class="post-footer">
        {% if page.categories %}
        <div class="post-categories">
            <span class="label">Categories:</span>
            {% for category in page.categories %}
            <a href="/category/{{ category | slugify }}" class="category-tag">{{ category }}</a>
            {% endfor %}
        </div>
        {% endif %}
        
        {% if page.tags %}
        <div class="post-tags">
            <span class="label">Tags:</span>
            {% for tag in page.tags %}
            <a href="/tag/{{ tag | slugify }}" class="tag">#{{ tag }}</a>
            {% endfor %}
        </div>
        {% endif %}
        
        <div class="post-share">
            <span class="label">Share:</span>
            <a href="https://twitter.com/intent/tweet?url={{ site.url }}{{ page.url }}&text={{ page.title }}" target="_blank" class="share-twitter">Twitter</a>
            <a href="https://www.facebook.com/sharer/sharer.php?u={{ site.url }}{{ page.url }}" target="_blank" class="share-facebook">Facebook</a>
            <a href="https://www.linkedin.com/sharing/share-offsite/?url={{ site.url }}{{ page.url }}" target="_blank" class="share-linkedin">LinkedIn</a>
        </div>
    </footer>
</article>

<!-- Related Posts -->
<section class="related-posts">
    <h3>Related Articles</h3>
    <div class="related-grid">
        {% for post in site.related_posts limit:3 %}
        <article class="related-post">
            <h4><a href="{{ post.url }}">{{ post.title }}</a></h4>
            <time>{{ post.date | date: "%B %d, %Y" }}</time>
        </article>
        {% endfor %}
    </div>
</section>"""
        
        # Save to file
        with open(f"{self.layouts_dir}/post.html", "w", encoding="utf-8") as f:
            f.write(post_layout)
        
        return post_layout
    
    def get_css(self):
        """Get CSS styles"""
        css_content = """/* Reset and base styles */
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    line-height: 1.6;
    color: #333;
    background-color: #fff;
}

.container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 0 20px;
}

/* Header */
.site-header {
    background-color: #2c3e50;
    color: white;
    padding: 1rem 0;
}

.navbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.navbar-brand .logo {
    font-size: 1.5rem;
    font-weight: bold;
    color: white;
    text-decoration: none;
}

.navbar-nav {
    display: flex;
    list-style: none;
    gap: 2rem;
}

.navbar-nav a {
    color: white;
    text-decoration: none;
    transition: color 0.3s;
}

.navbar-nav a:hover {
    color: #3498db;
}

/* Main Content */
.main-content {
    min-height: 70vh;
    padding: 2rem 0;
}

/* Post Styles */
.post {
    max-width: 800px;
    margin: 0 auto;
}

.post-header {
    text-align: center;
    margin-bottom: 2rem;
}

.post-title {
    font-size: 2.5rem;
    color: #2c3e50;
    margin-bottom: 1rem;
}

.post-meta {
    color: #7f8c8d;
    font-size: 0.9rem;
    margin-bottom: 1rem;
}

.post-featured-image {
    margin: 2rem 0;
    text-align: center;
}

.post-featured-image img {
    max-width: 100%;
    height: auto;
    border-radius: 8px;
    box-shadow: 0 4px 8px rgba(0,0,0,0.1);
}

.post-content {
    font-size: 1.1rem;
    line-height: 1.8;
    margin-bottom: 2rem;
}

.post-content h1,
.post-content h2,
.post-content h3,
.post-content h4 {
    color: #2c3e50;
    margin: 2rem 0 1rem 0;
}

.post-content h2 {
    font-size: 1.8rem;
    border-bottom: 2px solid #3498db;
    padding-bottom: 0.5rem;
}

.post-content h3 {
    font-size: 1.4rem;
}

.post-content p {
    margin-bottom: 1rem;
}

.post-content ul,
.post-content ol {
    margin: 1rem 0;
    padding-left: 2rem;
}

.post-content li {
    margin-bottom: 0.5rem;
}

.post-content blockquote {
    border-left: 4px solid #3498db;
    padding-left: 1rem;
    margin: 1rem 0;
    font-style: italic;
    color: #7f8c8d;
}

.post-content a {
    color: #3498db;
    text-decoration: none;
}

.post-content a:hover {
    text-decoration: underline;
}

/* Post Footer */
.post-footer {
    border-top: 1px solid #ecf0f1;
    padding-top: 2rem;
    margin-top: 2rem;
}

.post-categories,
.post-tags,
.post-share {
    margin-bottom: 1rem;
}

.label {
    font-weight: bold;
    margin-right: 0.5rem;
}

.category-tag,
.tag {
    display: inline-block;
    background-color: #ecf0f1;
    color: #2c3e50;
    padding: 0.25rem 0.5rem;
    border-radius: 4px;
    text-decoration: none;
    margin-right: 0.5rem;
    margin-bottom: 0.5rem;
    font-size: 0.9rem;
}

.category-tag:hover,
.tag:hover {
    background-color: #3498db;
    color: white;
}

.post-share a {
    display: inline-block;
    margin-right: 1rem;
    color: #3498db;
    text-decoration: none;
}

.post-share a:hover {
    text-decoration: underline;
}

/* Related Posts */
.related-posts {
    margin-top: 3rem;
    padding-top: 2rem;
    border-top: 1px solid #ecf0f1;
}

.related-posts h3 {
    color: #2c3e50;
    margin-bottom: 1rem;
}

.related-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 1rem;
}

.related-post {
    background-color: #f8f9fa;
    padding: 1rem;
    border-radius: 8px;
}

.related-post h4 {
    margin-bottom: 0.5rem;
}

.related-post a {
    color: #2c3e50;
    text-decoration: none;
}

.related-post a:hover {
    color: #3498db;
}

.related-post time {
    color: #7f8c8d;
    font-size: 0.9rem;
}

/* Footer */
.site-footer {
    background-color: #34495e;
    color: white;
    padding: 2rem 0 1rem 0;
    margin-top: 3rem;
}

.footer-content {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 2rem;
    margin-bottom: 2rem;
}

.footer-section h4 {
    margin-bottom: 1rem;
    color: #3498db;
}

.footer-section ul {
    list-style: none;
}

.footer-section li {
    margin-bottom: 0.5rem;
}

.footer-section a {
    color: #bdc3c7;
    text-decoration: none;
}

.footer-section a:hover {
    color: white;
}

.footer-bottom {
    text-align: center;
    padding-top: 1rem;
    border-top: 1px solid #7f8c8d;
    color: #bdc3c7;
}

/* Responsive Design */
@media (max-width: 768px) {
    .navbar {
        flex-direction: column;
        gap: 1rem;
    }
    
    .navbar-nav {
        gap: 1rem;
    }
    
    .post-title {
        font-size: 2rem;
    }
    
    .post-content {
        font-size: 1rem;
    }
    
    .related-grid {
        grid-template-columns: 1fr;
    }
}

/* AdSense Optimization */
.adsense-container {
    text-align: center;
    margin: 2rem 0;
    padding: 1rem;
    background-color: #f8f9fa;
    border-radius: 8px;
}

.adsense-label {
    font-size: 0.8rem;
    color: #7f8c8d;
    margin-bottom: 0.5rem;
}

/* SEO Enhancements */
.breadcrumb {
    margin-bottom: 1rem;
    font-size: 0.9rem;
}

.breadcrumb a {
    color: #3498db;
    text-decoration: none;
}

.breadcrumb a:hover {
    text-decoration: underline;
}

/* Loading Animation */
.loading {
    display: flex;
    justify-content: center;
    align-items: center;
    height: 200px;
}

.spinner {
    border: 4px solid #f3f3f3;
    border-top: 4px solid #3498db;
    border-radius: 50%;
    width: 40px;
    height: 40px;
    animation: spin 1s linear infinite;
}

@keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}"""
        
        # Save to file
        with open(self.css_file, "w", encoding="utf-8") as f:
            f.write(css_content)
        
        return css_content
    
    def update_layouts(self, default_layout, post_layout):
        """Update layout templates"""
        with open(f"{self.layouts_dir}/default.html", "w", encoding="utf-8") as f:
            f.write(default_layout)
        
        with open(f"{self.layouts_dir}/post.html", "w", encoding="utf-8") as f:
            f.write(post_layout)
    
    def update_css(self, css_content):
        """Update CSS styles"""
        with open(self.css_file, "w", encoding="utf-8") as f:
            f.write(css_content)
    
    def create_static_pages(self):
        """Create essential static pages"""
        pages = {
            "about": {
                "title": "About Us",
                "content": """
<h1>About Us</h1>
<p>Welcome to our investment and finance blog. We are dedicated to providing you with the latest insights, tips, and strategies to help you achieve financial success.</p>

<h2>Our Mission</h2>
<p>Our mission is to democratize financial knowledge and make investing accessible to everyone. We believe that with the right information and guidance, anyone can build wealth and achieve financial freedom.</p>

<h2>What We Cover</h2>
<ul>
    <li>Stock market analysis and investment strategies</li>
    <li>Forex trading tips and techniques</li>
    <li>Cryptocurrency insights and trends</li>
    <li>Personal finance and budgeting advice</li>
    <li>Retirement planning and wealth building</li>
</ul>

<h2>Our Team</h2>
<p>Our team consists of experienced financial professionals, certified financial planners, and investment analysts who are passionate about sharing their knowledge with others.</p>

<h2>Disclaimer</h2>
<p>The information provided on this blog is for educational purposes only and should not be considered as professional financial advice. Please consult with a qualified financial advisor before making any investment decisions.</p>
                """
            },
            "contact": {
                "title": "Contact Us",
                "content": """
<h1>Contact Us</h1>
<p>We'd love to hear from you! Whether you have questions about our content, suggestions for topics, or just want to connect, feel free to reach out.</p>

<h2>Get in Touch</h2>
<div class="contact-info">
    <p><strong>Email:</strong> info@investmentblog.com</p>
    <p><strong>Phone:</strong> +1 (555) 123-4567</p>
    <p><strong>Address:</strong> 123 Financial Street, Investment City, IC 12345</p>
</div>

<h2>Business Hours</h2>
<p>Monday - Friday: 9:00 AM - 6:00 PM</p>
<p>Saturday: 10:00 AM - 4:00 PM</p>
<p>Sunday: Closed</p>

<h2>Follow Us</h2>
<p>Stay connected with us on social media for the latest updates and insights:</p>
<ul>
    <li><a href="#">Twitter</a></li>
    <li><a href="#">Facebook</a></li>
    <li><a href="#">LinkedIn</a></li>
    <li><a href="#">Instagram</a></li>
</ul>

<h2>Feedback</h2>
<p>Your feedback is important to us. If you have any suggestions on how we can improve our content or if you'd like to see specific topics covered, please let us know.</p>
                """
            },
            "privacy-policy": {
                "title": "Privacy Policy",
                "content": """
<h1>Privacy Policy</h1>
<p><strong>Last updated:</strong> [Date]</p>

<h2>Introduction</h2>
<p>This Privacy Policy describes how we collect, use, and protect your personal information when you visit our website and use our services.</p>

<h2>Information We Collect</h2>
<h3>Personal Information</h3>
<ul>
    <li>Name and contact information</li>
    <li>Email address</li>
    <li>Comments and feedback</li>
</ul>

<h3>Non-Personal Information</h3>
<ul>
    <li>Browser type and version</li>
    <li>Operating system</li>
    <li>Pages visited and time spent</li>
    <li>IP address</li>
</ul>

<h2>How We Use Your Information</h2>
<ul>
    <li>To provide and improve our services</li>
    <li>To respond to your inquiries</li>
    <li>To send newsletters and updates (with your consent)</li>
    <li>To analyze website usage and performance</li>
</ul>

<h2>Data Protection</h2>
<p>We implement appropriate security measures to protect your personal information against unauthorized access, alteration, disclosure, or destruction.</p>

<h2>Cookies</h2>
<p>We use cookies to enhance your browsing experience and analyze website traffic. You can control cookie settings through your browser preferences.</p>

<h2>Third-Party Services</h2>
<p>We may use third-party services such as Google Analytics and advertising networks. These services have their own privacy policies.</p>

<h2>Your Rights</h2>
<p>You have the right to:</p>
<ul>
    <li>Access your personal information</li>
    <li>Request corrections to your data</li>
    <li>Request deletion of your data</li>
    <li>Opt-out of marketing communications</li>
</ul>

<h2>Contact Us</h2>
<p>If you have any questions about this Privacy Policy, please contact us at privacy@investmentblog.com.</p>
                """
            },
            "disclaimer": {
                "title": "Disclaimer",
                "content": """
<h1>Disclaimer</h1>

<h2>Financial Advice Disclaimer</h2>
<p>The information provided on this website is for educational and informational purposes only. It should not be considered as professional financial, investment, or legal advice.</p>

<h2>No Guarantees</h2>
<p>While we strive to provide accurate and up-to-date information, we make no representations or warranties of any kind, express or implied, about the completeness, accuracy, reliability, suitability, or availability of the information contained on this website.</p>

<h2>Investment Risks</h2>
<p>All investments carry risk, including the potential loss of principal. Past performance does not guarantee future results. The value of investments can go down as well as up.</p>

<h2>Professional Advice</h2>
<p>Before making any financial decisions, please consult with a qualified financial advisor, accountant, or legal professional who can provide advice tailored to your specific situation.</p>

<h2>External Links</h2>
<p>This website may contain links to external websites. We are not responsible for the content or privacy practices of these third-party sites.</p>

<h2>Limitation of Liability</h2>
<p>In no event shall we be liable for any direct, indirect, incidental, special, or consequential damages arising out of or in connection with your use of this website or the information contained herein.</p>

<h2>Changes to This Disclaimer</h2>
<p>We reserve the right to update this disclaimer at any time without notice. Please check this page regularly for updates.</p>

<h2>Jurisdiction</h2>
<p>This disclaimer is governed by the laws of [Your Jurisdiction]. Any disputes shall be resolved in the courts of [Your Jurisdiction].</p>
                """
            }
        }
        
        # Create pages
        for page_name, page_data in pages.items():
            self.update_page(page_name, page_data["content"], page_data["title"])
    
    def update_page(self, page_name, content, title=None):
        """Update or create a static page"""
        if not title:
            title = page_name.replace("-", " ").title()
        
        page_content = f"""---
layout: default
title: {title}
permalink: /{page_name}/
---

{content}
"""
        
        with open(f"{self.pages_dir}/{page_name}.html", "w", encoding="utf-8") as f:
            f.write(page_content)
    
    def get_page_content(self, page_name):
        """Get content of a static page"""
        try:
            with open(f"{self.pages_dir}/{page_name}.html", "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            return f"<h1>{page_name.title()}</h1><p>Page content not found.</p>"
    
    def generate_sitemap(self, domain="https://example.com"):
        """Generate sitemap.xml"""
        sitemap_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
    <url>
        <loc>{domain}/</loc>
        <lastmod>{datetime.now().strftime('%Y-%m-%d')}</lastmod>
        <changefreq>daily</changefreq>
        <priority>1.0</priority>
    </url>
    <url>
        <loc>{domain}/about/</loc>
        <lastmod>{datetime.now().strftime('%Y-%m-%d')}</lastmod>
        <changefreq>monthly</changefreq>
        <priority>0.8</priority>
    </url>
    <url>
        <loc>{domain}/contact/</loc>
        <lastmod>{datetime.now().strftime('%Y-%m-%d')}</lastmod>
        <changefreq>monthly</changefreq>
        <priority>0.8</priority>
    </url>
    <url>
        <loc>{domain}/privacy-policy/</loc>
        <lastmod>{datetime.now().strftime('%Y-%m-%d')}</lastmod>
        <changefreq>monthly</changefreq>
        <priority>0.5</priority>
    </url>
    <url>
        <loc>{domain}/disclaimer/</loc>
        <lastmod>{datetime.now().strftime('%Y-%m-%d')}</lastmod>
        <changefreq>monthly</changefreq>
        <priority>0.5</priority>
    </url>
</urlset>"""
        
        with open("sitemap.xml", "w", encoding="utf-8") as f:
            f.write(sitemap_content)
        
        return sitemap_content
    
    def generate_rss_feed(self, domain="https://example.com", site_title="Investment Blog"):
        """Generate RSS feed"""
        rss_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
    <channel>
        <title>{site_title}</title>
        <link>{domain}</link>
        <description>Your trusted source for investment and financial advice</description>
        <language>id</language>
        <pubDate>{datetime.now().strftime('%a, %d %b %Y %H:%M:%S %z')}</pubDate>
        <lastBuildDate>{datetime.now().strftime('%a, %d %b %Y %H:%M:%S %z')}</lastBuildDate>
        <generator>Custom Article Generator</generator>
        <managingEditor>info@{domain.replace('https://', '').replace('http://', '')}</managingEditor>
        <webMaster>webmaster@{domain.replace('https://', '').replace('http://', '')}</webMaster>
        
        <!-- RSS items will be added dynamically -->
    </channel>
</rss>"""
        
        with open("feed.xml", "w", encoding="utf-8") as f:
            f.write(rss_content)
        
        return rss_content