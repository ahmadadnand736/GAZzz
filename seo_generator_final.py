#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import time
import json
import random
import datetime
import requests
import markdown
import concurrent.futures
import multiprocessing
from multiprocessing import Pool, Queue, Process, Manager
import xml.etree.ElementTree as ET
import frontmatter
import yaml
from slugify import slugify
from langdetect import detect
from langcodes import Language

# Constants
DEFAULT_DOMAIN = ""
OUTPUT_FOLDER = "_posts"  # Output directory for generated articles
IMAGES_FOLDER = "assets/image"  # Images folder in root directory
ARTICLE_LINKS_FILE = "article_links.json"

# Initialize API keys
api_keys = []
current_key_index = 0

# Global variables for multiprocessing
NUM_PROCESSES = 5
process_api_keys = {}  # Dictionary to assign API keys to processes

# Class to manage article links for internal linking
class ArticleLinksManager:
    def __init__(self, filename=ARTICLE_LINKS_FILE):
        self.filename = filename
        self.articles = self._load_articles()
    
    def _load_articles(self):
        if os.path.exists(self.filename):
            try:
                with open(self.filename, 'r', encoding='utf-8') as file:
                    return json.load(file)
            except:
                return []
        return []
    
    def save_articles(self):
        with open(self.filename, 'w', encoding='utf-8') as file:
            json.dump(self.articles, file, ensure_ascii=False, indent=2)
    
    def add_article(self, title, subject, permalink):
        # Check if article with this permalink already exists
        for article in self.articles:
            if article['permalink'] == permalink:
                return False
        
        # Add new article
        self.articles.append({
            'title': title,
            'subject': subject,
            'permalink': permalink,
            'timestamp': datetime.datetime.now().isoformat()
        })
        
        # Save to file
        self.save_articles()
        return True
    
    def get_related_articles(self, subject, current_permalink, max_links=3):
        # Get words from the subject
        subject_words = set(subject.lower().split())
        
        # Score articles based on relevance
        scored_articles = []
        for article in self.articles:
            # Skip the current article
            if article['permalink'] == current_permalink:
                continue
            
            # Calculate word overlap for relevance
            article_subject_words = set(article['subject'].lower().split())
            overlap = len(subject_words.intersection(article_subject_words))
            
            if overlap > 0:
                scored_articles.append({
                    'title': article['title'],
                    'permalink': article['permalink'],
                    'score': overlap
                })
        
        # Sort by relevance score (higher is more relevant)
        scored_articles.sort(key=lambda x: x['score'], reverse=True)
        
        # Return the top N most relevant articles
        return scored_articles[:max_links]

# Create an instance of ArticleLinksManager
article_links_manager = ArticleLinksManager()

# Function to read API keys from file
def read_api_keys(filename="apikey.txt"):
    if os.path.exists(filename):
        with open(filename, "r") as file:
            return [line.strip() for line in file if line.strip()]
    return []

# Function to switch to next API key
def switch_api_key(keys, current_index):
    if not keys:
        raise Exception("No API keys available")
    
    next_index = (current_index + 1) % len(keys)
    return keys[next_index], next_index

# Initialize API keys
api_keys = read_api_keys()
if not api_keys:
    print("Warning: No API keys found in apikey.txt")
    print("Please add your Gemini API key to apikey.txt")

# Progress bar function
def print_progress_bar(iteration, total, prefix='', suffix='', length=50, fill='█'):
    """
    Call in a loop to create terminal progress bar
    """
    percent = ("{0:.1f}").format(100 * (iteration / float(total)))
    filled_length = int(length * iteration // total)
    bar = fill * filled_length + '-' * (length - filled_length)
    print(f'\r{prefix} |{bar}| {percent}% {suffix}', end='')
    # Print New Line on Complete
    if iteration == total: 
        print()

# Function to make API requests to Gemini with maximum speed optimization
def assign_api_keys_to_processes():
    """Assign API keys to processes for parallel processing"""
    global process_api_keys
    if len(api_keys) < NUM_PROCESSES:
        print_status(f"Warning: Only {len(api_keys)} API keys available for {NUM_PROCESSES} processes", "warning")
        # Duplicate keys if we don't have enough
        extended_keys = api_keys * ((NUM_PROCESSES // len(api_keys)) + 1)
        for i in range(NUM_PROCESSES):
            process_api_keys[i] = extended_keys[i % len(extended_keys)]
    else:
        for i in range(NUM_PROCESSES):
            process_api_keys[i] = api_keys[i]

def get_process_api_key():
    """Get API key for current process"""
    process_id = multiprocessing.current_process().name
    # Extract process number from process name (e.g., "Process-1" -> 1)
    try:
        if "Process-" in process_id:
            process_num = int(process_id.split("-")[1]) - 1
        else:
            process_num = 0
        return process_api_keys.get(process_num, api_keys[0] if api_keys else None)
    except:
        return api_keys[0] if api_keys else None

def gemini_request(prompt, model="gemini-1.5-flash", max_retries=3, api_key=None):
    global api_keys, current_key_index
    
    # Use process-specific API key if available, otherwise use provided key or current key
    if api_key is None:
        api_key = get_process_api_key()
        if api_key is None and api_keys:
            api_key = api_keys[current_key_index % len(api_keys)]
    
    # Check if we have API keys
    if not api_keys:
        raise Exception("No API keys available. Please add your API key to apikey.txt")
    
    retry_count = 0
    
    while retry_count < max_retries:
        # Set up API request
        api_key = api_keys[current_key_index]
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        
        headers = {
            "Content-Type": "application/json",
            "Connection": "keep-alive"  # Reuse connections for faster requests
        }
        
        # Ultra-optimized configuration for speed
        data = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": prompt
                        }
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.8,  # Slightly higher for faster generation
                "topK": 20,  # Reduced for faster processing
                "topP": 0.9,  # Slightly reduced for speed
                "maxOutputTokens": 4096,  # Reduced from 8192 for faster response
                "candidateCount": 1  # Only generate one candidate for speed
            },
            "safetySettings": [
                {
                    "category": "HARM_CATEGORY_HARASSMENT",
                    "threshold": "BLOCK_ONLY_HIGH"  # Less restrictive for speed
                },
                {
                    "category": "HARM_CATEGORY_HATE_SPEECH",
                    "threshold": "BLOCK_ONLY_HIGH"
                },
                {
                    "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                    "threshold": "BLOCK_ONLY_HIGH"
                },
                {
                    "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                    "threshold": "BLOCK_ONLY_HIGH"
                }
            ]
        }
        
        try:
            # Reduced timeout for faster failure detection
            response = requests.post(url, headers=headers, json=data, timeout=15)
            response.raise_for_status()
            response_json = response.json()
            
            if "candidates" in response_json and len(response_json["candidates"]) > 0:
                text = response_json["candidates"][0]["content"]["parts"][0]["text"]
                
                # Minimal wait time - only rotate key, no sleep
                if len(api_keys) > 1:
                    api_key, current_key_index = switch_api_key(api_keys, current_key_index)
                
                # Eliminated sleep for maximum speed
                return text
            else:
                # No valid response, switch key immediately
                if len(api_keys) > 1:
                    api_key, current_key_index = switch_api_key(api_keys, current_key_index)
                retry_count += 1
        
        except requests.exceptions.HTTPError as e:
            error_str = str(e)
            
            # Handle rate limiting with immediate key switch
            if "429" in error_str:
                if len(api_keys) > 1:
                    api_key, current_key_index = switch_api_key(api_keys, current_key_index)
                    # Only minimal wait for rate limit
                    time.sleep(0.2)
                else:
                    # If only one key, short wait
                    time.sleep(1)
            else:
                # Other HTTP errors, immediate key switch
                if len(api_keys) > 1:
                    api_key, current_key_index = switch_api_key(api_keys, current_key_index)
            
            retry_count += 1
        
        except Exception as e:
            # General exception, immediate key switch
            if len(api_keys) > 1:
                api_key, current_key_index = switch_api_key(api_keys, current_key_index)
            retry_count += 1
    
    # Fallback strategy - try Flash model if Pro failed
    if model == "gemini-1.5-pro":
        return gemini_request(prompt, "gemini-1.5-flash", 2)  # Reduced retries for fallback
    
    # If all retries failed
    raise Exception(f"Failed to get response after {max_retries} attempts with different API keys")

# Function to detect language from text with improved accuracy
def detect_language(subject):
    try:
        # Ensure we have enough text for accurate detection
        if len(subject) < 20:
            # For short phrases, we need to expand the text
            expanded_text = subject + " " + subject  # Simple duplication
            lang_code = detect(expanded_text)
        else:
            lang_code = detect(subject)
            
        # Extra validation for common languages
        if lang_code in ['en', 'id', 'ms', 'nl', 'de', 'fr', 'es', 'it', 'pt', 'sv', 'no', 'da', 'fi']:
            language = Language.make(language=lang_code).display_name()
            return language
        else:
            # If detected language is uncommon, double-check with more context
            # Most content is likely English for investment topics
            if any(term in subject.lower() for term in ['invest', 'stock', 'market', 'finance', 'etf', 'fund', 'portfolio', 'wealth']):
                return "English"
            
            language = Language.make(language=lang_code).display_name()
            return language
    except:
        # Default to English as fallback
        return "English"

# Function to generate title using Gemini, optimized to match target subjects better
def generate_title(subject, language, model="gemini-1.5-flash"):
    # Check if the subject already looks like a well-formed title
    # If subject contains "How to" or ends with a question mark, it's likely already a good title
    if (subject.startswith("How to") or subject.startswith("Top") or 
        subject.startswith("Best") or subject.startswith("Step-by-Step") or
        "vs" in subject or ":" in subject or
        any(term in subject.lower() for term in ["guide", "beginners", "strategies"])):
        
        # If subject is already a well-formed title, just clean it up and return
        # This ensures we use exact keywords from subjects.txt when they're already in title format
        cleaned_title = subject.strip()
        if language != "English" and language != "Inggris":
            # Only for non-English languages, generate a localized title
            title_prompt = (
                f"Translate this title to {language}: '{subject}'\n\n"
                f"Make it sound natural in {language} while keeping the same meaning. "
                f"Keep it concise and maintain keywords. Return only the translated title."
            )
            try:
                response = gemini_request(title_prompt, model)
                translated_title = response.strip().replace('"', '').replace("'", "").split('\n')[0]
                return translated_title
            except:
                return cleaned_title
        else:
            # For English, just return the cleaned original subject
            return cleaned_title
    
    # For subjects that aren't already well-formed titles, generate a proper title
    title_prompt = (
        f"Write a professional, SEO-optimized article title in {language} about '{subject}'.\n\n"
        f"RULES:\n"
        f"1. IMPORTANT: The title MUST include the exact phrase \"{subject}\" or its key components\n"
        f"2. Format as a 'How to' guide or list if appropriate (like 'How to Invest in Stocks' or 'Top 5 Investment Strategies')\n"
        f"3. Keep it under 70 characters if possible\n" 
        f"4. If the subject is clear and concise, prioritize using it exactly as provided\n"
        f"5. Make it informative and specific rather than clickbait\n"
        f"6. If the language is English, use professional, educational tone\n"
        f"7. Include words like 'Guide', 'Complete', 'Ultimate', or 'Beginner's' if relevant\n\n"
        f"FORMAT THE TITLE EXACTLY LIKE THIS (no extra text): Title Here"
    )
    
    try:
        # Generate title via API request
        response = gemini_request(title_prompt, model)
        
        # Clean up title (remove quotes and extra formatting)
        title = response.strip().replace('"', '').replace("'", "")
        
        # Handle multi-paragraph responses (take only the first line)
        title = title.split('\n')[0]
        
        # Verify the title is relevant to the subject
        if subject.lower() not in title.lower() and len(subject) > 10:
            # If key subject terms are missing, try again with a more direct prompt
            simple_prompt = f"Create a title about '{subject}' that MUST include the exact phrase '{subject}'. Only return the title, nothing else."
            try:
                simple_response = gemini_request(simple_prompt, "gemini-1.5-flash")
                simple_title = simple_response.strip().replace('"', '').replace("'", "").split('\n')[0]
                
                # If the simple title contains the subject, use it instead
                if subject.lower() in simple_title.lower():
                    return simple_title
            except:
                pass  # If the simple approach fails, continue with the original title
        
        return title
            
    except Exception as e:
        # If using flash model and it fails, try pro model
        if model == "gemini-1.5-flash":
            return generate_title(subject, language, "gemini-1.5-pro")
        # If using pro model and it fails, return the subject as the title
        return subject

# Function to get HTML content from a URL with improved error handling
def get_html_content(url, headers=None):
    if headers is None:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.text
    except Exception as e:
        # Minimize console output - log errors only if debugging is needed
        # print(f"Error fetching URL {url}: {str(e)}")
        return None

# Function to validate image URL before downloading
def is_valid_image(url, min_size=10000):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        
        # First do a HEAD request to check basics without downloading the whole image
        response = requests.head(url, headers=headers, timeout=5)
        
        # Check status code
        if response.status_code != 200:
            return False
            
        # Check content type
        content_type = response.headers.get('Content-Type', '')
        if not content_type.startswith('image/'):
            return False
            
        # Check if the URL has a valid image extension
        valid_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
        has_valid_extension = any(url.lower().endswith(ext) for ext in valid_extensions) or any(f"{ext}?" in url.lower() for ext in valid_extensions)
        
        # Check content size to avoid empty or tiny images
        content_length = int(response.headers.get('Content-Length', 0))
        if content_length < min_size:  # Minimum size in bytes (10KB by default)
            return False
            
        # If it has passed all basic checks, do a small GET request to verify
        try:
            # Only download first 32KB to check if it's a valid image
            response = requests.get(url, headers=headers, timeout=5, stream=True)
            content = next(response.iter_content(32768))  # Get first 32KB chunk
            
            # Check for common image file signatures/magic numbers
            is_jpeg = content.startswith(b'\xff\xd8\xff')
            is_png = content.startswith(b'\x89PNG\r\n\x1a\n')
            is_gif = content.startswith(b'GIF87a') or content.startswith(b'GIF89a')
            is_webp = b'WEBP' in content[:20]
            
            return is_jpeg or is_png or is_gif or is_webp or has_valid_extension
            
        except:
            return False
            
    except:
        return False

# Function to search for images using Bing with improved validation
def get_images_from_bing(query):
    try:
        # Set up enhanced headers
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Referer': 'https://www.bing.com/',
            'Upgrade-Insecure-Requests': '1'
        }
        
        # Enhanced search URL with filters for better images
        search_url = f"https://www.bing.com/images/search?q={query}&FORM=HDRSC2&first=1&cw=1177&ch=778"
        
        # Get the HTML content
        html_content = get_html_content(search_url, headers)
        
        if not html_content:
            return []
        
        # Multiple regex patterns to catch different URL formats
        img_urls = []
        patterns = [
            r'murl&quot;:&quot;(.*?)&quot;',
            r'"murl":"(.*?)"',
            r'imgurl:(.*?)&amp;',
            r'mediaurl=(.*?)&'
        ]
        
        for pattern in patterns:
            found_urls = re.findall(pattern, html_content)
            img_urls.extend(found_urls)
        
        # Clean and deduplicate URLs
        img_urls = list(set([url.replace('\\u002f', '/').replace('\\/', '/') for url in img_urls if url]))
        
        if not img_urls:
            return []
        
        # Enhanced validation with better scoring
        valid_images = []
        processed_count = 0
        
        for url in img_urls[:15]:  # Check more URLs for better results
            if processed_count >= 8:  # Limit processing to avoid timeouts
                break
                
            processed_count += 1
            
            if is_valid_image(url, min_size=5000):  # Lower minimum size for more options
                # Score images based on URL quality indicators
                score = 0
                url_lower = url.lower()
                
                # Prefer certain domains and formats
                if any(domain in url_lower for domain in ['wikimedia', 'unsplash', 'pixabay', 'pexels']):
                    score += 3
                if any(ext in url_lower for ext in ['.jpg', '.jpeg', '.png']):
                    score += 2
                if 'thumb' not in url_lower and 'small' not in url_lower:
                    score += 1
                
                valid_images.append({
                    "url": url,
                    "title": f"{query} related image",
                    "source": "Bing",
                    "score": score
                })
                
                if len(valid_images) >= 6:
                    break
        
        # Sort by score and return best images
        valid_images.sort(key=lambda x: x['score'], reverse=True)
        return valid_images[:5]
    
    except Exception as e:
        print(f"Error searching Bing images: {e}")
        return []

# Function to search for images using Yahoo with improved validation
def get_images_from_yahoo(query):
    try:
        # Enhanced headers for Yahoo
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://search.yahoo.com/',
            'Cache-Control': 'no-cache'
        }
        
        # Enhanced search URL with better parameters
        search_url = f"https://images.search.yahoo.com/search/images?p={query}&fr=yfp-t&ei=UTF-8&n=60&x=wrt"
        
        # Get the HTML content of the search results page
        html_content = get_html_content(search_url, headers)
        
        if not html_content:
            return []
        
        # Multiple regex patterns for better Yahoo image extraction
        img_urls = []
        patterns = [
            r'"ou":"(https?://[^"]+\.(?:jpg|jpeg|png|gif|webp)[^"]*)"',
            r'"imgurl":"(https?://[^"]+\.(?:jpg|jpeg|png|gif|webp)[^"]*)"',
            r'<img[^>]+src="(https?://[^"]+\.(?:jpg|jpeg|png|gif|webp)[^"]*)"',
            r'data-src="(https?://[^"]+\.(?:jpg|jpeg|png|gif|webp)[^"]*)"'
        ]
        
        for pattern in patterns:
            found_urls = re.findall(pattern, html_content, re.IGNORECASE)
            img_urls.extend(found_urls)
        
        # Clean and filter URLs
        img_urls = list(set([url for url in img_urls if url and not any(skip in url.lower() 
                            for skip in ['icon', 'logo', 'avatar', 'thumb', 'small'])]))
        
        if not img_urls:
            return []
        
        # Enhanced validation with scoring
        valid_images = []
        processed_count = 0
        
        for url in img_urls[:12]:  # Check more URLs for better results
            if processed_count >= 6:
                break
                
            processed_count += 1
            
            if is_valid_image(url, min_size=5000):
                # Score images based on quality indicators
                score = 0
                url_lower = url.lower()
                
                if any(domain in url_lower for domain in ['wikimedia', 'unsplash', 'pixabay', 'pexels', 'flickr']):
                    score += 3
                if any(ext in url_lower for ext in ['.jpg', '.jpeg', '.png']):
                    score += 2
                if any(size_indicator in url_lower for size_indicator in ['large', 'big', 'full', 'original']):
                    score += 1
                
                valid_images.append({
                    "url": url,
                    "title": f"{query} related image",
                    "source": "Yahoo",
                    "score": score
                })
                
                if len(valid_images) >= 5:
                    break
        
        # Sort by score and return best images
        valid_images.sort(key=lambda x: x['score'], reverse=True)
        return valid_images[:5]
    
    except Exception as e:
        return []

# Function to search for images using both Bing and Yahoo with enhanced fallback
def get_images(query):
    print(f"🔍 Mencari gambar untuk: {query}")
    
    # Clean query for better search results
    clean_query = query.replace('"', '').replace("'", "").strip()
    
    # Try multiple search strategies for better results
    search_variations = [
        clean_query,
        f"{clean_query} high quality",
        f"{clean_query} professional",
        clean_query.split()[0] if len(clean_query.split()) > 1 else clean_query
    ]
    
    all_images = []
    
    for variation in search_variations:
        if len(all_images) >= 5:  # Stop if we have enough good images
            break
            
        try:
            # Use ThreadPoolExecutor for parallel search from both engines
            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
                bing_future = executor.submit(get_images_from_bing, variation)
                yahoo_future = executor.submit(get_images_from_yahoo, variation)
                
                # Get results with timeout
                bing_images = bing_future.result(timeout=15)
                yahoo_images = yahoo_future.result(timeout=15)
            
            # Combine and deduplicate results
            combined_images = bing_images + yahoo_images
            
            # Remove duplicates based on URL
            seen_urls = set()
            for img in combined_images:
                if img['url'] not in seen_urls:
                    seen_urls.add(img['url'])
                    all_images.append(img)
                    
        except Exception as e:
            print(f"⚠️ Error searching for {variation}: {e}")
            continue
    
    # Sort by score if available, otherwise by source preference
    all_images.sort(key=lambda x: (x.get('score', 0), x['source'] == 'Bing'), reverse=True)
    
    # Return top 3-5 best images
    final_images = all_images[:5] if all_images else []
    
    if final_images:
        print(f"✅ Ditemukan {len(final_images)} gambar valid")
        return final_images
    else:
        print("⚠️ Tidak ada gambar valid ditemukan")
        return []

# Function to generate SEO article using Gemini
def generate_article(title, subject, domain, permalink, language, model="gemini-1.5-flash", related_articles=None):
    # Add related articles information to prompt if available
    related_links_text = ""
    if related_articles and len(related_articles) > 0:
        related_links_text = "RELATED ARTICLES TO INCLUDE:\n"
        for i, article in enumerate(related_articles):
            related_links_text += f"{i+1}. Title: \"{article['title']}\", Link: {domain}{article['permalink']}\n"
        related_links_text += "Include these links naturally within the article content using relevant anchor text that relates to both the keyword and the destination article.\n\n"
    
    # Determine if we should force English content based on subject or language
    force_english = language.lower() == "english" or any(eng_term in subject.lower() for eng_term in ["seo", "digital marketing", "google", "content marketing", "social media", "analytics"])
    
    # Define article language requirements
    language_specific_instructions = ""
    if force_english:
        language_specific_instructions = (
            "ENGLISH CONTENT REQUIREMENTS:\n"
            "1. Write the entire article in professional, flawless English regardless of the keyword language.\n"
            "2. Use precise terminology and industry-standard vocabulary.\n"
            "3. Maintain a clear, authoritative tone that conveys expertise.\n"
            "4. For technical topics, use proper technical terms and explain them clearly.\n"
            "5. Use American English spelling and grammar conventions.\n\n"
        )
    
    # ULTRA-STREAMLINED PROMPT FOR MAXIMUM SPEED
    article_prompt = f"""Write comprehensive SEO article: "{title}"

FAST STRUCTURE:
1. Introduction (3 paragraphs) with [**{domain}**](https://{domain}) in first paragraph
2. [IMAGE: {subject} overview infographic]
3. 4-5 main sections with ## headings
4. [IMAGE: specific description] before each section (total 6 images)
5. Bold key terms: **{subject}**
6. 3000-4000 words total
7. Conclusion with [**{title}**]({domain}{permalink}) link

{related_links_text}

REQUIREMENTS:
- Write in {language}
- Include 3-4 external authority links
- Add 2-3 internal links to {domain} pages
- Use bullet points and numbered lists
- Professional, expert tone
- Cover {subject} comprehensively
- Place images before headings, not after

Write complete article now."""
    
    try:
        # Generate article via API request
        response = gemini_request(article_prompt, model)
        
        # Verify that we have enough image placeholders (minimum 5)
        image_placeholders = re.findall(r'\[IMAGE: (.*?)\]', response)
        
        # If we don't have enough image placeholders, add more with a follow-up request
        if len(image_placeholders) < 5:
            additional_images_needed = 7 - len(image_placeholders)
            
            additional_prompt = (
                f"I need {additional_images_needed} more image placeholder descriptions for an article about '{subject}' with title '{title}'.\n\n"
                f"The existing image descriptions in the article are:\n"
                f"{chr(10).join(['- ' + desc for desc in image_placeholders])}\n\n"
                f"Please provide {additional_images_needed} additional unique, specific image descriptions (format: [IMAGE: detailed description]) that would fit well in an article about {subject}.\n"
                f"Each description should be highly specific and detailed to enable finding relevant images."
            )
            
            try:
                # Get additional image descriptions
                additional_response = gemini_request(additional_prompt, "gemini-1.5-flash")
                
                # Extract the image descriptions using regex
                additional_descriptions = re.findall(r'\[IMAGE: (.*?)\]', additional_response)
                
                # If we didn't get properly formatted descriptions, try to extract any descriptions
                if not additional_descriptions:
                    # Look for numbered or bulleted items
                    lines = additional_response.strip().split('\n')
                    additional_descriptions = []
                    for line in lines:
                        # Remove numbering, bullets, or other prefixes
                        clean_line = re.sub(r'^[\d\-\*\.\s]+', '', line).strip()
                        if clean_line and len(clean_line) > 10:  # Ensure it's a substantive description
                            additional_descriptions.append(clean_line)
                
                # If we found additional descriptions, insert them into the article
                if additional_descriptions:
                    # Split the article into paragraphs
                    paragraphs = response.split('\n\n')
                    
                    # Find good positions to insert images (before headings, not in intro or conclusion)
                    positions = []
                    for i in range(len(paragraphs)):
                        # Look for headings that don't already have an image before them
                        if i > 2 and i < len(paragraphs) - 3:  # Skip intro and conclusion
                            if paragraphs[i].startswith('##') and '[IMAGE:' not in paragraphs[i-1]:
                                positions.append(i)
                    
                    # If we don't have enough positions, find more (e.g., after long paragraphs)
                    if len(positions) < len(additional_descriptions):
                        for i in range(len(paragraphs)):
                            if i > 2 and i < len(paragraphs) - 3:  # Skip intro and conclusion
                                if i not in positions and len(paragraphs[i]) > 200 and not paragraphs[i].startswith('#'):
                                    positions.append(i)
                                    if len(positions) >= len(additional_descriptions):
                                        break
                    
                    # Sort positions to maintain article flow
                    positions.sort()
                    
                    # Insert additional image placeholders
                    for i, pos in enumerate(positions[:len(additional_descriptions)]):
                        placeholder = f"[IMAGE: {additional_descriptions[i]}]"
                        paragraphs.insert(pos, placeholder)
                    
                    # Reconstruct article
                    response = '\n\n'.join(paragraphs)
            except Exception as e:
                # If adding more placeholders fails, continue with what we have
                print(f"Error adding additional image placeholders: {str(e)}")
        
        return response
            
    except Exception as e:
        print(f"\nError generating article: {str(e)}")
        # If using pro model and it fails, try flash model
        if model == "gemini-1.5-pro":
            print("Trying with gemini-1.5-flash instead...")
            return generate_article(title, subject, domain, permalink, language, "gemini-1.5-flash", related_articles)
        # If using flash model and it fails, raise the error
        raise e

# Function to replace image placeholders with real images
def find_existing_images_in_assets(count=1):
    """
    Find existing images in the assets folder.
    Returns a list of image paths relative to the site root.
    """
    # Ensure assets directories exist
    assets_dir = IMAGES_FOLDER
    os.makedirs(assets_dir, exist_ok=True)
    
    # List all files in the assets directory
    image_files = []
    for file in os.listdir(assets_dir):
        # Check if file is an image
        if file.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp')):
            image_files.append(f"/{assets_dir}/{file}")  # Path from site root
    
    # Sort by modification time (newest first)
    image_files.sort(key=lambda x: os.path.getmtime(x.lstrip('/')), reverse=True)
    
    # Return requested number of images or all if fewer exist
    return image_files[:count]

# Create a copy of the original function for downloading images
def replace_image_placeholders_download(article, subject, domain=DEFAULT_DOMAIN):
    """
    Replace image placeholders in an article with images downloaded to the assets folder.
    This version downloads images locally for better control over the assets.
    """
    # Ensure assets directories exist
    assets_dir = IMAGES_FOLDER
    os.makedirs(assets_dir, exist_ok=True)
    
    # Find all image placeholders
    pattern = r'\[IMAGE: (.*?)\]'
    image_descriptions = re.findall(pattern, article)
    
    # Track the first image path for the featured image
    featured_image = None
    
    if not image_descriptions:
        # If no placeholders found, use an existing image from assets
        existing_images = find_existing_images_in_assets(1)
        if existing_images:
            featured_image = existing_images[0]
        return article, featured_image
    
    # Store placeholder descriptions and search queries for parallel processing
    placeholders_data = []
    for i, description in enumerate(image_descriptions):
        # The query should be specific and include the subject and the description
        query = f"{subject} {description}"
        placeholders_data.append({
            'description': description,
            'query': query,
            'index': i
        })
    
    # Process placeholders and create image tags
    image_tags = {}
    
    # Function to process a single placeholder
    def process_placeholder(placeholder_data):
        description = placeholder_data['description']
        query = placeholder_data['query']
        index = placeholder_data['index']
        
        try:
            # Try the main query first (with more efficient querying)
            images = get_images(query)
            
            # If no images found, try alternative queries in sequence
            if not images:
                # Try just the description
                images = get_images(description)
                
            if not images:
                # Try just the subject
                images = get_images(subject)
                
            if not images:
                # Try a generic query
                images = get_images(f"{subject} image")
                
            if images and len(images) > 0:
                # Use the first valid image
                valid_image = images[0]
                img_url = valid_image['url']
                img_title = description
                
                # Create filename from subject and description
                domain_part = domain.replace('.', '-')
                keyword_title = slugify(f"{subject}-{description}")[:40]
                img_filename = f"{keyword_title}-{domain_part}-{index+1}.jpg"
                img_save_path = os.path.join(assets_dir, img_filename)
                img_rel_path = f"{IMAGES_FOLDER}/{img_filename}"
                
                # Ensure the path starts with a slash
                if not img_rel_path.startswith('/'):
                    img_rel_path = f"/{img_rel_path}"
                
                # Download and save the image
                headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
                img_response = requests.get(img_url, headers=headers, stream=True, timeout=10)
                
                if img_response.status_code == 200:
                    with open(img_save_path, 'wb') as img_file:
                        for chunk in img_response.iter_content(chunk_size=8192):
                            img_file.write(chunk)
                    
                    # Create markdown image tag
                    img_tag = f"![{img_title}]({img_rel_path})"
                    
                    # Return the image tag and path
                    return {
                        'description': description,
                        'img_tag': img_tag,
                        'img_path': img_rel_path,
                        'success': True
                    }
            
            # If no valid images were found or downloaded, use existing images
            existing_images = find_existing_images_in_assets(1)
            if existing_images:
                # Use an existing image from assets folder
                existing_img_path = existing_images[0]
                img_tag = f"![{description}]({existing_img_path})"
                
                return {
                    'description': description,
                    'img_tag': img_tag,
                    'img_path': existing_img_path,
                    'success': True
                }
            
            # If no images at all, create a placeholder
            return {
                'description': description,
                'img_tag': f"<!-- Image for {description} could not be retrieved -->",
                'img_path': None,
                'success': False
            }
            
        except Exception as e:
            # Error handling with minimal output
            return {
                'description': description,
                'img_tag': f"<!-- Error finding image: {description} -->",
                'img_path': None,
                'success': False
            }
    
    # Process placeholders in parallel with more workers for speed
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = []
        for placeholder_data in placeholders_data:
            futures.append(executor.submit(process_placeholder, placeholder_data))
        
        # Process results as they complete
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            if result:
                # Store image tag for later replacement
                image_tags[result['description']] = result['img_tag']
                
                # Set featured image if not already set and image was found successfully
                if featured_image is None and result['success'] and result['img_path']:
                    featured_image = result['img_path']
    
    # Replace all placeholders with their corresponding image tags
    modified_article = article
    for description, img_tag in image_tags.items():
        modified_article = modified_article.replace(f"[IMAGE: {description}]", img_tag)
    
    # Replace any remaining placeholders that weren't processed
    for description in image_descriptions:
        if description not in image_tags:
            modified_article = modified_article.replace(
                f"[IMAGE: {description}]", 
                f"<!-- Could not process image for: {description} -->"
            )
    
    return modified_article, featured_image

def replace_image_placeholders(article, subject, domain=DEFAULT_DOMAIN):
    """
    Replace image placeholders in an article with direct external image URLs.
    This optimized version uses external images without downloading them.
    """
    # Find all image placeholders
    pattern = r'\[IMAGE: (.*?)\]'
    image_descriptions = re.findall(pattern, article)
    
    # Track the first image URL for the featured image
    featured_image = None
    
    if not image_descriptions:
        return article, featured_image
    
    # Store placeholder descriptions and search queries for parallel processing
    placeholders_data = []
    for i, description in enumerate(image_descriptions):
        # The query should be specific and include the subject and the description
        query = f"{subject} {description}"
        placeholders_data.append({
            'description': description,
            'query': query,
            'index': i
        })
    
    # Process placeholders and create image tags
    image_tags = {}
    
    # Function to process a single placeholder
    def process_placeholder(placeholder_data):
        description = placeholder_data['description']
        query = placeholder_data['query']
        
        try:
            # Try the main query first (with more efficient querying)
            images = get_images(query)
            
            # If no images found, try alternative queries in sequence
            if not images:
                # Try just the description
                images = get_images(description)
                
            if not images:
                # Try just the subject
                images = get_images(subject)
                
            if not images:
                # Try a generic query
                images = get_images(f"{subject} image")
                
            if images and len(images) > 0:
                # Use the first valid image directly from source (no download)
                valid_image = images[0]
                img_url = valid_image['url']
                img_title = description
                
                # Create markdown image tag with the external image URL
                img_tag = f"![{img_title}]({img_url})"
                
                # Return the image tag and URL
                return {
                    'description': description,
                    'img_tag': img_tag,
                    'img_url': img_url,
                    'success': True
                }
            
            # If no images found, use a placeholder or fallback
            return {
                'description': description,
                'img_tag': f"<!-- No image found for: {description} -->",
                'img_url': None,
                'success': False
            }
            
        except Exception as e:
            # Error handling with minimal output
            return {
                'description': description,
                'img_tag': f"<!-- Error finding image: {description} -->",
                'img_url': None,
                'success': False
            }
    
    # Process placeholders in parallel with more workers for speed
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = []
        for placeholder_data in placeholders_data:
            futures.append(executor.submit(process_placeholder, placeholder_data))
        
        # Process results as they complete
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            if result:
                # Store image tag for later replacement
                image_tags[result['description']] = result['img_tag']
                
                # Set featured image if not already set and image was found successfully
                if featured_image is None and result['success'] and result['img_url']:
                    featured_image = result['img_url']
    
    # Replace all placeholders with their corresponding image tags
    modified_article = article
    for description, img_tag in image_tags.items():
        modified_article = modified_article.replace(f"[IMAGE: {description}]", img_tag)
    
    # Replace any remaining placeholders that weren't processed
    for description in image_descriptions:
        if description not in image_tags:
            modified_article = modified_article.replace(
                f"[IMAGE: {description}]", 
                f"<!-- Could not process image for: {description} -->"
            )
    
    return modified_article, featured_image

# Function to create Jekyll frontmatter
def generate_tags_from_title(title, subject):
    """
    Generate SEO-optimized tags from the title and subject of the article.
    This function uses title words as primary source for tags and supplements with subject words.
    It prioritizes longer phrases as they tend to be more specific keywords.
    """
    # Common words to exclude (both English and Indonesian)
    stop_words = [
        'yang', 'untuk', 'dengan', 'adalah', 'dari', 'cara', 'tips', 'trik',
        'dan', 'atau', 'jika', 'maka', 'namun', 'tetapi', 'juga', 'oleh',
        'the', 'and', 'that', 'this', 'with', 'for', 'from', 'how', 'what',
        'when', 'why', 'where', 'who', 'will', 'your', 'their', 'our', 'its'
    ]
    
    # Clean and normalize text
    clean_title = title.lower().replace(':', ' ').replace('-', ' ').replace(',', ' ').replace('.', ' ')
    clean_subject = subject.lower()
    
    # Extract potential multi-word phrases from title (2-3 words)
    title_parts = clean_title.split()
    title_phrases = []
    
    # Get 2-word phrases
    for i in range(len(title_parts) - 1):
        phrase = title_parts[i] + ' ' + title_parts[i + 1]
        if all(word not in stop_words for word in phrase.split()):
            title_phrases.append(phrase)
    
    # Get 3-word phrases
    for i in range(len(title_parts) - 2):
        phrase = title_parts[i] + ' ' + title_parts[i + 1] + ' ' + title_parts[i + 2]
        if all(word not in stop_words for word in phrase.split()):
            title_phrases.append(phrase)
    
    # Get single words from title
    title_words = [word.strip() for word in clean_title.split() 
                 if len(word.strip()) > 3 and word.lower() not in stop_words]
    
    # Get words from subject
    subject_words = [word.strip() for word in clean_subject.split() 
                    if len(word.strip()) > 3 and word.lower() not in stop_words]
    
    # Build final tag list prioritizing multi-word phrases
    all_tags = []
    
    # First add any 3-word phrases (usually most specific)
    three_word_phrases = [p for p in title_phrases if len(p.split()) == 3]
    all_tags.extend(three_word_phrases[:2])  # Up to 2 three-word phrases
    
    # Then add 2-word phrases
    two_word_phrases = [p for p in title_phrases if len(p.split()) == 2]
    all_tags.extend(two_word_phrases[:2])  # Up to 2 two-word phrases
    
    # Then add important single words
    remaining_slots = 5 - len(all_tags)
    if remaining_slots > 0:
        # Combine and remove duplicates (words already in phrases)
        single_words = []
        for word in title_words + subject_words:
            already_included = any(word in phrase for phrase in all_tags)
            if not already_included and word not in single_words:
                single_words.append(word)
        
        all_tags.extend(single_words[:remaining_slots])
    
    # Ensure we don't exceed 5 tags and we have at least 1 tag
    return all_tags[:5] if all_tags else [subject.split()[0]]

def validate_yaml_frontmatter(yaml_content):
    """Validate YAML frontmatter format"""
    try:
        # Extract YAML content between --- markers
        if yaml_content.startswith('---\n') and '\n---\n' in yaml_content:
            yaml_part = yaml_content.split('---\n', 1)[1].split('\n---\n', 1)[0]
            yaml.safe_load(yaml_part)
            return True
    except yaml.YAMLError:
        return False
    return False

def generate_frontmatter(title, subject, permalink, category=None, publisher="Mas DEEe", featured_image=None):
    """Generate valid Jekyll frontmatter with proper YAML formatting"""
    today = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S +0000')
    
    # Generate tags from title and subject
    tags = generate_tags_from_title(title, subject)
    
    # Use provided category or generate from subject if none provided
    if not category:
        main_category = subject.split()[0] if subject.split() else "blog"
    else:
        main_category = category
    
    # Properly escape strings for YAML
    def escape_yaml_string(text):
        """Properly escape strings for YAML"""
        if not text:
            return ""
        # Remove problematic characters and normalize
        text = str(text).strip()
        # Replace quotes and escape special characters
        text = text.replace('"', '').replace("'", "").replace('\\', '')
        return text
    
    clean_title = escape_yaml_string(title)
    clean_category = escape_yaml_string(main_category)
    clean_permalink = permalink if permalink.startswith('/') else f"/{permalink}"
    
    # Build frontmatter data structure first (for validation)
    frontmatter_data = {
        'layout': 'post',
        'title': clean_title,
        'date': today,
        'author': publisher,
        'categories': [clean_category],
        'tags': [escape_yaml_string(tag) for tag in tags],
        'description': f"{clean_title} - Complete guide and comprehensive analysis"[:147] + ("..." if len(f"{clean_title} - Complete guide and comprehensive analysis") > 150 else ""),
        'permalink': clean_permalink
    }
    
    # Add featured image if available
    if featured_image:
        frontmatter_data['image'] = featured_image
    
    # Generate YAML content manually with proper formatting
    content = "---\n"
    content += f"layout: post\n"
    content += f"title: \"{clean_title}\"\n"
    content += f"date: {today}\n"
    content += f"author: \"{publisher}\"\n"
    
    # Add categories with proper YAML array format (consistent with tags)
    content += f"categories:\n"
    content += f"  - \"{clean_category}\"\n"
    
    # Add tags with proper YAML array format
    content += f"tags:\n"
    for tag in tags:
        clean_tag = escape_yaml_string(tag)
        content += f"  - \"{clean_tag}\"\n"
    
    # Add meta description
    meta_desc = frontmatter_data['description']
    content += f"description: \"{meta_desc}\"\n"
    
    # Add featured image if available
    if featured_image:
        content += f"image: \"{featured_image}\"\n"
    
    content += f"permalink: {clean_permalink}\n"
    content += "---\n\n"
    
    # Validate the generated YAML
    if not validate_yaml_frontmatter(content):
        print_status("Warning: Generated YAML may have formatting issues, using fallback format", "warning")
        # Fallback to simpler format if validation fails
        content = "---\n"
        content += f"layout: post\n"
        content += f"title: {clean_title}\n"
        content += f"date: {today}\n"
        content += f"author: {publisher}\n"
        content += f"categories: [{clean_category}]\n"
        content += f"tags: {tags}\n"
        content += f"description: {meta_desc}\n"
        if featured_image:
            content += f"image: {featured_image}\n"
        content += f"permalink: {clean_permalink}\n"
        content += "---\n\n"
    
    return content

# Function to generate article with valid Jekyll frontmatter
def generate_seo_article(subject, domain=DEFAULT_DOMAIN, model_title="gemini-1.5-flash", model_article="gemini-1.5-flash", category=None, download_images=False, publisher="Mas DEEe", include_images=True):
    try:
        # Detect language from subject
        language = detect_language(subject)
        
        # Generate title
        title = generate_title(subject, language, model_title)
        
        # Generate permalink
        permalink = f"/{slugify(title)}"
        
        # Find related articles
        related_articles = article_links_manager.get_related_articles(subject, permalink)
        
        # Generate article content with related links
        article = generate_article(title, subject, domain, permalink, language, model_article, related_articles)
        
        # Handle images based on include_images parameter
        featured_image = None
        if include_images:
            # Replace image placeholders based on download_images setting
            if download_images:
                # Download images to assets folder
                article_with_images, featured_image = replace_image_placeholders_download(article, subject, domain)
            else:
                # Use external image URLs directly (faster)
                article_with_images, featured_image = replace_image_placeholders(article, subject, domain)
        else:
            # Remove all image placeholders for text-only articles
            import re
            article_with_images = re.sub(r'\[IMAGE: .*?\]', '', article)
            # Clean up any double line breaks left by image removal
            article_with_images = re.sub(r'\n\n\n+', '\n\n', article_with_images)
        
        # Generate Jekyll frontmatter with optional custom category and featured image
        frontmatter = generate_frontmatter(title, subject, permalink, category, publisher, featured_image)
        
        # Add <!--more--> tag after the first paragraph for Jekyll excerpt
        paragraphs = article_with_images.split('\n\n')
        if len(paragraphs) > 1:
            # Insert <!--more--> after first paragraph
            paragraphs.insert(1, '<!--more-->')
            article_with_images = '\n\n'.join(paragraphs)
        
        # Create full markdown document with valid frontmatter
        markdown_content = frontmatter + article_with_images
        
        # Add the article to our link manager for future reference
        article_links_manager.add_article(title, subject, permalink)
        
        return {
            "title": title,
            "article": article_with_images,
            "markdown": markdown_content,
            "permalink": permalink,
            "featured_image": featured_image
        }
        
    except Exception as e:
        return {"error": str(e)}

# Function to read subjects from file
def read_subjects_file(filename="subjects.txt"):
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as file:
            subjects = [line.strip() for line in file if line.strip()]
        return subjects
    return []

def get_existing_articles_from_posts():
    """Get list of existing articles from _posts folder"""
    existing_articles = []
    
    if not os.path.exists(OUTPUT_FOLDER):
        return existing_articles
    
    try:
        for filename in os.listdir(OUTPUT_FOLDER):
            if filename.endswith('.md'):
                filepath = os.path.join(OUTPUT_FOLDER, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as file:
                        content = file.read()
                        # Simple frontmatter parsing
                        if content.startswith('---'):
                            parts = content.split('---', 2)
                            if len(parts) >= 3:
                                frontmatter_text = parts[1]
                                # Extract tags from frontmatter
                                for line in frontmatter_text.split('\n'):
                                    if line.strip().startswith('tags:'):
                                        tags_part = line.split(':', 1)[1].strip()
                                        if tags_part.startswith('[') and tags_part.endswith(']'):
                                            # List format: tags: [tag1, tag2]
                                            tags_content = tags_part[1:-1]
                                            first_tag = tags_content.split(',')[0].strip().strip('"').strip("'")
                                            if first_tag:
                                                existing_articles.append(first_tag)
                                        else:
                                            # Single tag or simple format
                                            tag = tags_part.strip().strip('"').strip("'")
                                            if tag:
                                                existing_articles.append(tag)
                                        break
                                else:
                                    # If no tags found, extract from title
                                    for line in frontmatter_text.split('\n'):
                                        if line.strip().startswith('title:'):
                                            title = line.split(':', 1)[1].strip().strip('"').strip("'")
                                            # Extract key words from title
                                            title_words = title.lower().split()
                                            common_words = ['the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'how', 'what', 'where', 'when', 'why', 'guide', 'tips', 'best', 'top']
                                            key_words = [word for word in title_words if word not in common_words and len(word) > 2]
                                            if key_words:
                                                existing_articles.append(' '.join(key_words[:3]))
                                            break
                except Exception as e:
                    print(f"Error reading {filepath}: {str(e)}")
                    continue
    except Exception as e:
        print_status(f"Error scanning posts folder: {str(e)}", "error")
    
    return existing_articles

def get_existing_articles_from_links():
    """Get list of existing articles from article_links.json"""
    existing_subjects = []
    
    try:
        articles = article_links_manager.articles
        for article in articles:
            if 'subject' in article:
                existing_subjects.append(article['subject'])
    except Exception as e:
        print_status(f"Error reading article links: {str(e)}", "error")
    
    return existing_subjects

def filter_remaining_subjects(all_subjects):
    """Filter subjects to only include those that haven't been generated yet"""
    # Get existing articles from both sources
    existing_from_posts = get_existing_articles_from_posts()
    existing_from_links = get_existing_articles_from_links()
    
    # Combine and normalize existing subjects
    all_existing = set()
    for subject in existing_from_posts + existing_from_links:
        all_existing.add(subject.lower().strip())
    
    # Filter remaining subjects
    remaining_subjects = []
    for subject in all_subjects:
        subject_normalized = subject.lower().strip()
        
        # Check for exact match
        if subject_normalized not in all_existing:
            # Check for partial matches (in case of slight variations)
            is_similar = False
            for existing in all_existing:
                # Check if subjects are very similar (>80% word overlap)
                subject_words = set(subject_normalized.split())
                existing_words = set(existing.split())
                
                if subject_words and existing_words:
                    overlap = len(subject_words.intersection(existing_words))
                    similarity = overlap / max(len(subject_words), len(existing_words))
                    
                    if similarity > 0.8:  # 80% similarity threshold
                        is_similar = True
                        break
            
            if not is_similar:
                remaining_subjects.append(subject)
    
    return remaining_subjects

def process_single_subject(args):
    """Process a single subject - optimized for multiprocessing"""
    subject, domain, publisher, default_category, download_images, include_images, process_id = args
    
    try:
        # Generate the article
        result = generate_seo_article(
            subject=subject,
            domain=domain,
            model_title="gemini-1.5-flash",
            model_article="gemini-1.5-flash",
            category=default_category,
            download_images=download_images,
            publisher=publisher,
            include_images=include_images
        )
        
        if "error" in result:
            return {"subject": subject, "status": "error", "error": result["error"], "process_id": process_id}
        
        # Save the article to file
        filename = f"{datetime.datetime.now().strftime('%Y-%m-%d')}-{slugify(result['title'])}.md"
        filepath = os.path.join(OUTPUT_FOLDER, filename)
        
        with open(filepath, "w", encoding="utf-8") as file:
            file.write(result["markdown"])
        
        return {
            "subject": subject,
            "status": "success",
            "filename": filename,
            "title": result["title"],
            "process_id": process_id
        }
        
    except Exception as e:
        return {"subject": subject, "status": "error", "error": str(e), "process_id": process_id}

def parallel_batch_generate_seo_articles(domain=None, output_folder=OUTPUT_FOLDER, include_images=True):
    """Optimized parallel batch generation with 5 processes"""
    global process_api_keys
    
    # Ask for domain if not provided
    if domain is None:
        domain = input("\033[1;36mEnter your domain (default: " + DEFAULT_DOMAIN + "): \033[0m")
        if not domain.strip():
            domain = DEFAULT_DOMAIN
    
    # Ask for publisher name
    publisher = input("\033[1;36mEnter publisher name (default:  ): \033[0m")
    if not publisher.strip():
        publisher = " "
    
    # Ask for default category for all articles
    print("\033[1;36mCategory Options:\033[0m")
    print("1. Use automatic categories (derived from subject)")
    print("2. Enter a single category for all articles")
    
    category_choice = input("\033[1;36mSelect category option (1-2): \033[0m")
    default_category = None
    
    if category_choice == "2":
        default_category = input("\033[1;36mEnter the category for all articles: \033[0m")
        
    # Handle image options based on include_images parameter
    download_images = False
    if include_images:
        # Ask for image handling preference only if images are included
        print("\033[1;36mImage Options:\033[0m")
        print("1. Download images to assets/image folder (slower but self-hosted)")
        print("2. Use external image URLs directly (faster generation)")
        
        image_choice = input("\033[1;36mSelect image option (1-2, default: 2): \033[0m")
        download_images = image_choice == "1"
        
        if download_images:
            print_status("Will download images to assets/image folder", "info")
        else:
            print_status("Will use external image URLs (faster generation)", "info")
    else:
        print_status("Articles will be generated WITHOUT images", "info")
    
    # Ensure output directory exists
    os.makedirs(output_folder, exist_ok=True)
    
    # Read subjects from file
    subjects = read_subjects_file()
    if not subjects:
        print_status("No subjects found in subjects.txt file", "error")
        return
    
    # Filter out already generated subjects
    remaining_subjects = filter_remaining_subjects(subjects)
    
    if not remaining_subjects:
        print_status("All subjects have already been generated!", "success")
        return
    
    # Assign API keys to processes
    assign_api_keys_to_processes()
    
    print_status(f"Found {len(remaining_subjects)} subjects to process with {NUM_PROCESSES} parallel processes", "info")
    print_status(f"Domain: {domain}", "info")
    print_status(f"Publisher: {publisher}", "info")
    print_status(f"Download images: {'Yes' if download_images else 'No (external URLs)'}", "info")
    
    # Prepare arguments for multiprocessing
    process_args = []
    for i, subject in enumerate(remaining_subjects):
        process_id = i % NUM_PROCESSES
        process_args.append((subject, domain, publisher, default_category, download_images, include_images, process_id))
    
    # Start parallel processing
    start_time = time.time()
    success_count = 0
    error_count = 0
    
    print_status(f"Starting parallel generation with {NUM_PROCESSES} processes...", "info")
    
    # Use multiprocessing Pool for parallel execution
    try:
        with Pool(processes=NUM_PROCESSES) as pool:
            results = []
            
            # Submit all tasks
            async_results = [pool.apply_async(process_single_subject, (args,)) for args in process_args]
            
            # Process results as they complete
            for i, async_result in enumerate(async_results):
                try:
                    result = async_result.get(timeout=300)  # 5 minute timeout per article
                    results.append(result)
                    
                    if result["status"] == "success":
                        success_count += 1
                        print_status(f"✓ [{success_count + error_count}/{len(remaining_subjects)}] Process {result['process_id']}: {result['subject']} -> {result['filename']}", "success")
                    else:
                        error_count += 1
                        print_status(f"✗ [{success_count + error_count}/{len(remaining_subjects)}] Process {result['process_id']}: {result['subject']} - Error: {result['error']}", "error")
                    
                    # Update progress bar
                    print_progress_bar(success_count + error_count, len(remaining_subjects), 
                                     prefix='Progress:', suffix=f'Complete ({success_count} success, {error_count} errors)', length=50)
                    
                except Exception as e:
                    error_count += 1
                    print_status(f"✗ Process timeout or error: {str(e)}", "error")
    
    except Exception as e:
        print_status(f"Error in parallel processing: {str(e)}", "error")
        return
    
    # Final summary
    end_time = time.time()
    total_time = end_time - start_time
    
    print("\n" + "="*70)
    print_status("PARALLEL BATCH GENERATION COMPLETED!", "success")
    print_status(f"Total articles processed: {success_count + error_count}", "info")
    print_status(f"Successful generations: {success_count}", "success")
    print_status(f"Failed generations: {error_count}", "error" if error_count > 0 else "info")
    print_status(f"Total time: {total_time:.1f} seconds", "info")
    print_status(f"Average time per article: {total_time/(success_count + error_count):.1f} seconds", "info")
    print_status(f"Articles saved to: {output_folder}/", "info")
    print("="*70)
    
    if error_count > 0:
        print_status("Some articles failed to generate. Check the error messages above.", "warning")

# Function to batch process all subjects from subjects.txt (original sequential version)
def batch_generate_seo_articles(domain=None, output_folder=OUTPUT_FOLDER, include_images=True):
    # Ask for domain if not provided
    if domain is None:
        domain = input("\033[1;36mEnter your domain (default: " + DEFAULT_DOMAIN + "): \033[0m")
        if not domain.strip():
            domain = DEFAULT_DOMAIN
    
    # Ask for publisher name
    publisher = input("\033[1;36mEnter publisher name (default:  ): \033[0m")
    if not publisher.strip():
        publisher = " "
    
    # Ask for default category for all articles
    print("\033[1;36mCategory Options:\033[0m")
    print("1. Use automatic categories (derived from subject)")
    print("2. Enter a single category for all articles")
    print("3. Enter category for each article individually")
    
    category_choice = input("\033[1;36mSelect category option (1-3): \033[0m")
    default_category = None
    
    if category_choice == "2":
        default_category = input("\033[1;36mEnter the category for all articles: \033[0m")
        
    # Handle image options based on include_images parameter
    download_images = False
    if include_images:
        # Ask for image handling preference only if images are included
        print("\033[1;36mImage Options:\033[0m")
        print("1. Download images to assets/image folder (slower but self-hosted)")
        print("2. Use external image URLs directly (faster generation)")
        
        image_choice = input("\033[1;36mSelect image option (1-2, default: 2): \033[0m")
        
        if image_choice == "1":
            download_images = True
            print_status("Will download images to assets/image folder", "info")
        else:
            print_status("Will use external image URLs (faster generation)", "info")
    else:
        print_status("Articles will be generated WITHOUT images", "info")
    
    # Create output folder if it doesn't exist
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        print_status(f"Created output folder: {output_folder}", "success")
        
    # Create assets folder structure in root
    if not os.path.exists(IMAGES_FOLDER):
        os.makedirs(IMAGES_FOLDER)
        print_status(f"Created images folder: {IMAGES_FOLDER}", "success")
    
    # Read subjects from file
    all_subjects = read_subjects_file()
    if not all_subjects:
        print_status("No subjects found in subjects.txt. Please add subjects first.", "error")
        return []
    
    print_status(f"Found {len(all_subjects)} total keywords in subjects.txt", "info")
    
    # Filter to get only remaining subjects that haven't been generated
    remaining_subjects = filter_remaining_subjects(all_subjects)
    
    if not remaining_subjects:
        print_status("All subjects from subjects.txt have already been generated!", "success")
        print_status("Check _posts folder and article_links.json for existing articles.", "info")
        return []
    
    # Show summary of what will be processed
    existing_count = len(all_subjects) - len(remaining_subjects)
    print_status(f"Already generated: {existing_count} articles", "success")
    print_status(f"Remaining to generate: {len(remaining_subjects)} articles", "working")
    
    # Ask user if they want to continue with remaining subjects
    if existing_count > 0:
        print("\n\033[1;36mREMAINING SUBJECTS TO GENERATE:\033[0m")
        for i, subject in enumerate(remaining_subjects[:10], 1):  # Show first 10
            print(f"  {i}. {subject}")
        if len(remaining_subjects) > 10:
            print(f"  ... and {len(remaining_subjects) - 10} more")
        
        confirm = input(f"\n\033[1;36mContinue generating {len(remaining_subjects)} remaining articles? (y/n): \033[0m")
        if confirm.lower() not in ['y', 'yes']:
            print_status("Generation cancelled by user.", "info")
            return []
    
    subjects = remaining_subjects
    total_subjects = len(subjects)
    print_status(f"Target domain: {domain}", "info")
    print_status(f"Articles will be saved to: {output_folder}", "info")
    print_status("Starting article generation process...", "working")
    print("\n" + "=" * 80 + "\n")
    
    # Initialize list to track generated articles
    generated_articles = []
    errors = []
    start_time = time.time()
    
    # Process each subject
    for idx, subject in enumerate(subjects):
        try:
            # Print current status with nice formatting
            print(f"\033[1;36m[{idx+1}/{total_subjects}]\033[0m Processing keyword: \033[1;33m{subject}\033[0m")
            
            # Update progress bar
            print_progress_bar(idx, total_subjects, prefix='Progress:', 
                               suffix=f'{int((idx/total_subjects)*100)}%', length=50)
            
            # Ask for article-specific category if option 3 was selected
            article_category = default_category
            if category_choice == "3":
                article_category = input(f"\033[1;36mEnter category for article about '{subject}' (leave empty for auto): \033[0m")
                if not article_category.strip():
                    article_category = None
            
            # Generate SEO article with appropriate category and image options
            print_status(f"Generating article for: {subject}", "working")
            if article_category:
                print_status(f"Using category: {article_category}", "info")
            result = generate_seo_article(subject, domain, "gemini-1.5-flash", "gemini-1.5-flash", article_category, download_images, publisher, include_images)
            
            if "error" in result:
                print_status(f"Error generating article: {result['error']}", "error")
                errors.append(f"{subject}: {result['error']}")
                continue

            title = result["title"]
            markdown_content = result["markdown"]
            
            # Create date prefix for Jekyll post
            date_prefix = datetime.datetime.now().strftime('%Y-%m-%d-')
            
            # File paths for markdown post in Jekyll format
            file_md = os.path.join(output_folder, f"{date_prefix}{slugify(title)}.md")

            # Save markdown file with frontmatter
            with open(file_md, "w", encoding="utf-8") as md_file:
                md_file.write(markdown_content)

            # Add to generated articles list
            generated_articles.append({
                "subject": subject,
                "title": title,
                "file": file_md,
                "permalink": result["permalink"],
                "category": article_category if article_category else subject.split()[0] if subject.split() else subject
            })
            
            # Show success message
            print_status(f"Generated: {title}", "success")
            print_status(f"Saved to: {file_md}", "info")
            print_status(f"Permalink: {domain}{result['permalink']}", "info")
            print("\n" + "-" * 80 + "\n")
            
            # Reduced delay for faster generation
            time.sleep(0.3)
            
        except Exception as e:
            print_status(f"Error: {str(e)}", "error")
            errors.append(f"{subject}: {str(e)}")
            print("\n" + "-" * 80 + "\n")
    
    # Complete the progress bar
    print_progress_bar(total_subjects, total_subjects, prefix='Progress:', 
                      suffix='100%', length=50)
    
    # Calculate elapsed time
    elapsed_time = time.time() - start_time
    minutes, seconds = divmod(elapsed_time, 60)
    
    # Display summary
    print("\n\033[1;36m" + "=" * 40 + " GENERATION SUMMARY " + "=" * 40 + "\033[0m\n")
    
    print_status(f"Total keywords processed: {total_subjects}", "info")
    print_status(f"Successfully generated: {len(generated_articles)}", "success" if generated_articles else "error")
    print_status(f"Errors: {len(errors)}", "error" if errors else "success")
    print_status(f"Time elapsed: {int(minutes)} minutes, {int(seconds)} seconds", "info")
    
    # Display status for each article
    if generated_articles:
        print("\n\033[1;32m✓ GENERATED ARTICLES:\033[0m")
        for i, article in enumerate(generated_articles):
            print(f"  \033[1;32m{i+1}.\033[0m \033[1m{article['title']}\033[0m")
            print(f"     \033[90mKeyword: {article['subject']}\033[0m")
            print(f"     \033[90mCategory: {article['category']}\033[0m")
            print(f"     \033[90mSaved to: {article['file']}\033[0m")
            print(f"     \033[90mPermalink: {domain}{article['permalink']}\033[0m")
        
    # Display errors if any
    if errors:
        print("\n\033[1;31m✗ ERRORS:\033[0m")
        for i, error in enumerate(errors):
            print(f"  \033[1;31m{i+1}.\033[0m {error}")
    
    # Final status message
    print("\n" + "-" * 80)
    if generated_articles:
        print_status(f"Generation complete! {len(generated_articles)} articles created successfully.", "success")
    else:
        print_status("No articles were generated. Please check the errors above.", "error")
    print("-" * 80 + "\n")
    
    # Return the generated articles list
    return generated_articles

# Function to display CLI header with style
def display_header():
    # Clear screen first
    os.system('cls' if os.name == 'nt' else 'clear')
    
    # Display header with box drawing characters
    print("\n")
    print("╔══════════════════════════════════════════════════════════════════════════╗")
    print("║                                                                          ║")
    print("║  \033[1;36mSEO ARTICLE GENERATOR ULTIMATE v3.0 Fast Gacor\033[0m                                   ║")
    print("║  \033[90mPowered by Gemini 1.5 Pro AI & Dual-Engine Image Search\033[0m                 ║")
    print("║                                                                          ║")
    print("╚══════════════════════════════════════════════════════════════════════════╝")
    print("\n")

# Function to display status with colors and symbols
def print_status(message, status="info"):
    if status == "success":
        print(f"\033[1;32m✓ {message}\033[0m")
    elif status == "error":
        print(f"\033[1;31m✗ {message}\033[0m")
    elif status == "warning":
        print(f"\033[1;33m⚠ {message}\033[0m")
    elif status == "info":
        print(f"\033[1;34mℹ {message}\033[0m")
    elif status == "working":
        print(f"\033[1;35m⚙ {message}\033[0m")
    else:
        print(f"  {message}")

# Function to show main menu and get user choice
def show_menu():
    print("\n\033[1;36m" + "=" * 40 + " ARTICLE GENERATOR " + "=" * 40 + "\033[0m\n")
    print("  1. Generate SEO Articles (with Images)")
    print("  2. Generate SEO Articles (No Images)")
    print("  3. \033[1;32m🚀 Generate SEO Articles - Parallel Mode (with Images)\033[0m")
    print("  4. \033[1;32m🚀 Generate SEO Articles - Parallel Mode (No Images)\033[0m")
    print("  0. Exit\n")
    
    choice = input("\033[1;36mEnter your choice (0-4): \033[0m")
    return choice.strip()



# Main function
def main():
    # Display header
    display_header()
    
    # Print application information
    print("  Professional CLI SEO Article Generator")
    print("  Optimized for 5000-7500 word in-depth articles with comprehensive analysis")
    print("  Choose between articles with images or text-only articles")
    print("  Dual Image Search: Bing + Yahoo with parallel processing for speed")
    print("  Manual Domain Input & Custom Category Support")
    print("  Enhanced language detection for better title matching\n")
    
    # Check if API keys are available
    if not api_keys:
        print_status("No API keys found in apikey.txt", "error")
        print_status("Please add your Gemini API key to apikey.txt", "info")
        return
    
    print_status(f"Found {len(api_keys)} API key(s) in apikey.txt", "success")
    
    while True:
        choice = show_menu()
        
        if choice == "0":
            print_status("Exiting program...", "info")
            break
        
        elif choice == "1":
            # Generate articles with images (Sequential)
            print_status("Initializing article generation with images...", "working")
            time.sleep(1)
            batch_generate_seo_articles(include_images=True)
        
        elif choice == "2":
            # Generate articles without images (Sequential)
            print_status("Initializing article generation without images...", "working")
            time.sleep(1)
            batch_generate_seo_articles(include_images=False)
        
        elif choice == "3":
            # Generate articles with images (Parallel)
            print_status("🚀 Initializing PARALLEL article generation with images (5x Faster)...", "working")
            print_status("Using 5 processes with 1 API key per process for maximum speed!", "info")
            time.sleep(1)
            parallel_batch_generate_seo_articles(include_images=True)
        
        elif choice == "4":
            # Generate articles without images (Parallel)
            print_status("🚀 Initializing PARALLEL article generation without images (5x Faster)...", "working")
            print_status("Using 5 processes with 1 API key per process for maximum speed!", "info")
            time.sleep(1)
            parallel_batch_generate_seo_articles(include_images=False)
        
        else:
            print_status("Invalid choice. Please enter a number between 0 and 4.", "error")
        
        # Wait for user to continue
        input("\n\033[1;36mPress Enter to continue...\033[0m")

# Entry point
if __name__ == "__main__":
    main()