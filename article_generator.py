import requests
import json
import os
import random
from datetime import datetime
from slugify import slugify
from langdetect import detect

class ArticleGenerator:
    def __init__(self):
        self.load_api_keys()
        self.current_key_index = 0
        
    def load_api_keys(self):
        """Load Gemini API keys from config"""
        try:
            with open('config.json', 'r') as f:
                config = json.load(f)
                self.api_keys = config.get('gemini', {}).get('api_keys', [])
        except FileNotFoundError:
            self.api_keys = []
    
    def get_next_api_key(self):
        """Get next API key in rotation"""
        if not self.api_keys:
            return None
        
        key = self.api_keys[self.current_key_index]
        self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
        return key
    
    def gemini_request(self, prompt, model="gemini-1.5-flash", max_retries=3):
        """Make request to Gemini API"""
        for attempt in range(max_retries):
            api_key = self.get_next_api_key()
            if not api_key:
                return None
            
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
            
            headers = {
                'Content-Type': 'application/json',
            }
            
            data = {
                "contents": [{
                    "parts": [{
                        "text": prompt
                    }]
                }]
            }
            
            try:
                response = requests.post(f"{url}?key={api_key}", headers=headers, json=data)
                
                if response.status_code == 200:
                    result = response.json()
                    if 'candidates' in result and len(result['candidates']) > 0:
                        return result['candidates'][0]['content']['parts'][0]['text']
                else:
                    print(f"API Error: {response.status_code} - {response.text}")
                    continue
                    
            except Exception as e:
                print(f"Request error: {str(e)}")
                continue
        
        return None
    
    def detect_language(self, text):
        """Detect language of text"""
        try:
            lang = detect(text)
            return 'Indonesian' if lang == 'id' else 'English'
        except:
            return 'Indonesian'
    
    def generate_title(self, subject, language="Indonesian"):
        """Generate SEO-optimized title"""
        prompt = f"""Generate a compelling, SEO-optimized title for an article about "{subject}" in {language}.
        
        Requirements:
        - Maximum 60 characters
        - Include relevant keywords
        - Make it engaging and click-worthy
        - Use numbers or power words when appropriate
        
        Return only the title, no additional text."""
        
        return self.gemini_request(prompt)
    
    def generate_content(self, title, subject, language="Indonesian"):
        """Generate article content"""
        prompt = f"""Write a comprehensive, SEO-optimized article about "{subject}" with the title "{title}" in {language}.

        Requirements:
        - Minimum 1500 words
        - Use proper HTML headings (h2, h3)
        - Include relevant keywords naturally
        - Add bullet points and numbered lists
        - Include actionable advice
        - Use engaging, conversational tone
        - Structure with introduction, main content, and conclusion
        - Add internal linking opportunities (use placeholder links)
        
        Focus on:
        - Investment strategies
        - Financial planning
        - Risk management
        - Market analysis
        - Practical tips
        
        Return only the HTML content, no additional text."""
        
        return self.gemini_request(prompt)
    
    def generate_meta_description(self, title, content):
        """Generate meta description"""
        prompt = f"""Create a compelling meta description for an article titled "{title}".
        
        Requirements:
        - Maximum 155 characters
        - Include main keyword
        - Encourage clicks
        - Summarize the article value
        
        Article excerpt: {content[:500]}...
        
        Return only the meta description, no additional text."""
        
        return self.gemini_request(prompt)
    
    def generate_tags(self, title, subject):
        """Generate relevant tags"""
        prompt = f"""Generate 8-10 relevant tags for an article titled "{title}" about "{subject}".
        
        Requirements:
        - Focus on investment and finance keywords
        - Include long-tail keywords
        - Use Indonesian terms when appropriate
        - Mix broad and specific tags
        
        Return as a JSON array of strings."""
        
        result = self.gemini_request(prompt)
        try:
            # Try to parse as JSON
            if result and result.strip().startswith('['):
                return json.loads(result)
            else:
                # Extract tags from text
                tags = []
                lines = result.split('\n')
                for line in lines:
                    if line.strip():
                        tag = line.strip().replace('-', '').replace('*', '').replace('"', '')
                        if tag:
                            tags.append(tag)
                return tags[:10]
        except:
            return ["investasi", "keuangan", "saham", "forex", "trading", "financial planning"]
    
    def generate_permalink(self, title):
        """Generate SEO-friendly permalink"""
        return slugify(title, max_length=50)
    
    def generate_article(self, subject, category="Investasi", language="Indonesian", domain="https://example.com"):
        """Generate complete article"""
        try:
            # Generate title
            title = self.generate_title(subject, language)
            if not title:
                title = subject
            
            # Generate content
            content = self.generate_content(title, subject, language)
            if not content:
                return None
            
            # Generate metadata
            meta_description = self.generate_meta_description(title, content)
            tags = self.generate_tags(title, subject)
            permalink = self.generate_permalink(title)
            
            # Create article structure
            article = {
                "title": title.strip(),
                "content": content,
                "meta_description": meta_description.strip() if meta_description else title[:155],
                "tags": tags,
                "permalink": permalink,
                "category": category,
                "language": language,
                "domain": domain,
                "generated_at": datetime.now().isoformat()
            }
            
            # Generate frontmatter
            frontmatter = self.generate_frontmatter(article)
            
            # Create markdown file content
            markdown_content = f"{frontmatter}\n\n{content}"
            
            # Save to file
            filename = f"{datetime.now().strftime('%Y-%m-%d')}-{permalink}.md"
            filepath = os.path.join('_posts', filename)
            
            # Create _posts directory if it doesn't exist
            os.makedirs('_posts', exist_ok=True)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            
            article['filename'] = filename
            article['filepath'] = filepath
            
            return article
            
        except Exception as e:
            print(f"Error generating article: {str(e)}")
            return None
    
    def generate_frontmatter(self, article):
        """Generate Jekyll frontmatter"""
        frontmatter = f"""---
layout: post
title: "{article['title']}"
date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} +0700
categories: [{article['category']}]
tags: {json.dumps(article['tags'])}
permalink: /{article['permalink']}/
description: "{article['meta_description']}"
lang: {article['language'].lower()}
author: "Investment Expert"
---"""
        return frontmatter
    
    def batch_generate(self, subjects, category="Investasi", language="Indonesian", domain="https://example.com"):
        """Generate multiple articles"""
        results = []
        
        for subject in subjects:
            article = self.generate_article(subject, category, language, domain)
            if article:
                results.append(article)
                print(f"Generated: {article['title']}")
            else:
                print(f"Failed to generate: {subject}")
        
        return results
    
    def get_random_subjects(self, count=5):
        """Get random subjects for article generation"""
        subjects = [
            "Investasi Saham untuk Pemula",
            "Strategi Trading Forex yang Menguntungkan",
            "Panduan Lengkap Investasi Cryptocurrency",
            "Reksadana vs Saham: Mana yang Lebih Baik?",
            "Cara Analisis Fundamental Saham",
            "Bitcoin Trading untuk Pemula",
            "Investasi Emas vs Properti",
            "Cara Membaca Grafik Saham",
            "Strategi Diversifikasi Portfolio",
            "Dollar Cost Averaging Strategy",
            "Investasi P2P Lending",
            "Cara Investasi di Pasar Modal",
            "Strategi Swing Trading",
            "Investasi Jangka Panjang vs Pendek",
            "Cara Mengelola Risiko Investasi",
            "Investasi Syariah yang Menguntungkan",
            "Trading Saham Harian",
            "Investasi untuk Pensiun",
            "Cara Memilih Broker Saham",
            "Investasi Obligasi Pemerintah"
        ]
        
        return random.sample(subjects, min(count, len(subjects)))