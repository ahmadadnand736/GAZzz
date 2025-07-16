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
import xml.etree.ElementTree as ET
import frontmatter
from slugify import slugify
from langdetect import detect
from langcodes import Language

# Constants
DEFAULT_DOMAIN = "bloggers.web.id"
OUTPUT_FOLDER = "_posts"  # Output directory for generated articles
IMAGES_FOLDER = "assets/image"  # Images folder in root directory
ARTICLE_LINKS_FILE = "article_links.json"

# Initialize API keys
api_keys = []
current_key_index = 0

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

# Function to make API requests to Gemini
def gemini_request(prompt, model="gemini-1.5-flash", max_retries=5):
    global api_keys, current_key_index
    
    # Check if we have API keys
    if not api_keys:
        raise Exception("No API keys available. Please add your API key to apikey.txt")
    
    retry_count = 0
    
    while retry_count < max_retries:
        # Set up API request
        api_key = api_keys[current_key_index]
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        
        headers = {
            "Content-Type": "application/json"
        }
        
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
                "temperature": 0.7,
                "topK": 40,
                "topP": 0.95,
                "maxOutputTokens": 8192,
                "stopSequences": []
            },
            "safetySettings": [
                {
                    "category": "HARM_CATEGORY_HARASSMENT",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                },
                {
                    "category": "HARM_CATEGORY_HATE_SPEECH",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                },
                {
                    "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                },
                {
                    "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                }
            ]
        }
        
        try:
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            response_json = response.json()
            
            if "candidates" in response_json and len(response_json["candidates"]) > 0:
                text = response_json["candidates"][0]["content"]["parts"][0]["text"]
                
                # Always rotate API key after a successful request and wait 2 seconds
                api_key, current_key_index = switch_api_key(api_keys, current_key_index)
                print(f"API key rotated to maintain rate limits. Waiting 2 seconds...")
                time.sleep(2)
                
                return text
            else:
                # No valid response, switch key and retry
                api_key, current_key_index = switch_api_key(api_keys, current_key_index)
                print(f"API key rotated due to empty response. Waiting 2 seconds...")
                time.sleep(2)
                retry_count += 1
        
        except requests.exceptions.HTTPError as e:
            error_str = str(e)
            
            # Handle rate limiting specifically
            if "429" in error_str and "Too Many Requests" in error_str:
                # Switch to next API key
                api_key, current_key_index = switch_api_key(api_keys, current_key_index)
                
                # Add exponential backoff wait time based on retry count
                wait_time = (2 ** retry_count) * 2  # 2, 4, 8, 16, 32 seconds
                print(f"Rate limit reached. Switching API key and waiting {wait_time:.1f} seconds before retrying...")
                time.sleep(wait_time)
            else:
                # Other HTTP error, switch key and retry
                api_key, current_key_index = switch_api_key(api_keys, current_key_index)
                print(f"API error: {error_str}. Trying with a different API key. Waiting 2 seconds...")
                time.sleep(2)
            
            retry_count += 1
        
        except Exception as e:
            # General exception, switch key and retry
            api_key, current_key_index = switch_api_key(api_keys, current_key_index)
            print(f"Unexpected error: {str(e)}. Trying with a different API key. Waiting 2 seconds...")
            time.sleep(2)
            retry_count += 1
    
    # If all retries failed with gemini-1.5-pro, try with gemini-1.5-flash
    if model == "gemini-1.5-pro":
        print(f"Failed with {model} after {max_retries} attempts. Trying with gemini-1.5-flash instead...")
        return gemini_request(prompt, "gemini-1.5-flash", max_retries)
    
    # If we've exhausted all retries and even the fallback model failed
    raise Exception(f"Failed to get response after {max_retries} attempts with different API keys")

# Function to detect language from text
def detect_language(subject):
    try:
        lang_code = detect(subject)
        language = Language.make(language=lang_code).display_name()
        return language
    except:
        return "English"

# Function to generate title using Gemini
def generate_title(subject, language, model="gemini-1.5-flash"):
    title_prompt = (
        f"Write a catchy and SEO-optimized article title in {language} about '{subject}'.\n\n"
        f"RULES:\n"
        f"1. Make it attention-grabbing and click-worthy without being clickbait\n"
        f"2. Include the main keyword \"{subject}\" or a closely related term\n"
        f"3. Keep it under 60 characters if possible\n"
        f"4. Make sure it's in {language} language\n"
        f"5. Add a subtitle separated by a colon or dash if appropriate\n"
        f"6. Do not include unnecessary punctuation or all caps\n"
        f"7. If the language is English, make the title more professional and concise\n"
        f"8. For English titles, use power words that drive engagement and clicks\n\n"
        f"FORMAT THE TITLE EXACTLY LIKE THIS (no extra text): Title Here"
    )
    
    try:
        # Generate title via API request
        response = gemini_request(title_prompt, model)
        
        # Clean up title (remove quotes and extra formatting)
        title = response.strip().replace('"', '').replace("'", "")
        
        # Handle multi-paragraph responses (take only the first line)
        title = title.split('\n')[0]
        
        return title
            
    except Exception as e:
        print(f"\nError generating title: {str(e)}")
        # If using flash model and it fails, try pro model
        if model == "gemini-1.5-flash":
            print("Trying with gemini-1.5-pro instead...")
            return generate_title(subject, language, "gemini-1.5-pro")
        # If using pro model and it fails, raise the error
        raise e

# Function to get HTML content from a URL
def get_html_content(url, headers=None):
    if headers is None:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"Error fetching URL {url}: {str(e)}")
        return None

# Function to search for images using Bing
def get_images_from_bing(query):
    try:
        # Set up the headers for the request
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        
        # Construct search URL
        search_url = f"https://www.bing.com/images/search?q={query}&first=1"
        
        # Get the HTML content of the search results page
        html_content = get_html_content(search_url, headers)
        
        if not html_content:
            print(f"Failed to get HTML content from Bing for query: {query}")
            return []
        
        # Extract image URLs using regex
        img_urls = re.findall(r'murl&quot;:&quot;(.*?)&quot;', html_content)
        
        if not img_urls or len(img_urls) == 0:
            print(f"No image URLs found from Bing for query: {query}")
            return []
        
        # Create image objects from the URLs (up to 5 images)
        images = []
        for i, url in enumerate(img_urls[:5]):
            images.append({
                "url": url,
                "title": f"{query} image {i+1}",
                "source": "Bing"
            })
        
        print(f"Successfully found {len(images)} images from Bing for query: {query}")
        return images
    
    except Exception as e:
        print(f"Error in get_images_from_bing for query '{query}': {str(e)}")
        return []

# Function to search for images using Yahoo
def get_images_from_yahoo(query):
    try:
        # Set up the headers for the request
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        
        # Construct search URL
        search_url = f"https://images.search.yahoo.com/search/images?p={query}"
        
        # Get the HTML content of the search results page
        html_content = get_html_content(search_url, headers)
        
        if not html_content:
            print(f"Failed to get HTML content from Yahoo for query: {query}")
            return []
        
        # Extract image URLs using regex - adapt this regex pattern for Yahoo's HTML structure
        img_urls = re.findall(r'<img[^>]+src="([^"]+)"[^>]*class="process[^>]*>', html_content)
        
        if not img_urls or len(img_urls) == 0:
            # Try alternative pattern
            img_urls = re.findall(r'<img[^>]+data-src="([^"]+)"[^>]*class="process[^>]*>', html_content)
        
        if not img_urls or len(img_urls) == 0:
            # Try another alternative pattern
            img_urls = re.findall(r'<img[^>]+src="([^"]+)"[^>]*>', html_content)
            # Filter out small images and icons
            img_urls = [url for url in img_urls if not ('icon' in url.lower() or 'logo' in url.lower())]
            
        if not img_urls or len(img_urls) == 0:
            print(f"No image URLs found from Yahoo for query: {query}")
            return []
        
        # Create image objects from the URLs (up to 5 images)
        images = []
        for i, url in enumerate(img_urls[:5]):
            images.append({
                "url": url,
                "title": f"{query} image {i+1}",
                "source": "Yahoo"
            })
        
        print(f"Successfully found {len(images)} images from Yahoo for query: {query}")
        return images
    
    except Exception as e:
        print(f"Error in get_images_from_yahoo for query '{query}': {str(e)}")
        return []

# Function to search for images using both Bing and Yahoo
def get_images(query):
    # Try Bing first
    bing_images = get_images_from_bing(query)
    
    # If Bing returned enough images, use them
    if len(bing_images) >= 3:
        return bing_images
    
    # Otherwise, try Yahoo
    yahoo_images = get_images_from_yahoo(query)
    
    # Combine the results
    all_images = bing_images + yahoo_images
    
    # If we still don't have enough images, try with a simplified query
    if len(all_images) < 2:
        # Simplify the query by taking just the first 2-3 words
        simplified_query = ' '.join(query.split()[:3])
        print(f"Trying simplified query: {simplified_query}")
        
        # Try Bing with simplified query
        bing_simple_images = get_images_from_bing(simplified_query)
        
        # Try Yahoo with simplified query
        yahoo_simple_images = get_images_from_yahoo(simplified_query)
        
        # Add to the combined results
        all_images = all_images + bing_simple_images + yahoo_simple_images
    
    return all_images

# Function to generate SEO article using Gemini
def generate_article(title, subject, domain, permalink, language, model="gemini-1.5-pro", related_articles=None):
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
    
    article_prompt = (
        f"Write an extremely comprehensive and in-depth SEO-optimized article for the following title: \"{title}\"\n\n"
        f"FORMAT REQUIREMENTS:\n"
        f"1. Start with an engaging 3-4 paragraph introduction that includes the domain name '{domain}' as a BOLD HYPERLINK only ONCE in the first paragraph. Format it as [**{domain}**](https://{domain}). This automatically creates both bold and hyperlink.\n"
        f"2. Immediately after the introduction, insert an image placeholder with format: [IMAGE: {subject} overview infographic].\n"
        f"3. Create a deep hierarchical structure with H2, H3, and H4 headings (use markdown format: ##, ###, ####). START with H2 headings after the introduction, and use H3 and H4 for more detailed subsections.\n"
        f"4. Create a minimum of 4000 words (target range: 4000-7000 words) with detailed professional-level analysis for each heading section.\n"
        f"5. Bold 5-7 primary and secondary keywords related to '{subject}' throughout the article for SEO optimization. These should appear naturally in the text, especially at the beginning of paragraphs.\n"
        f"6. Include exactly 6-7 image placeholders throughout the article using format: [IMAGE: detailed description related to the heading], but ALWAYS place these image placeholders BEFORE their related headings, not after.\n"
        f"7. DO NOT include any image placeholders in the conclusion section or at the very end of the article.\n" 
        f"8. End with a warm, personalized conclusion paragraph that directly addresses the reader, followed by a friendly call-to-action paragraph with a bold internal link to '[**{domain}{permalink}**](https://{domain}{permalink})' using the article title as anchor text.\n\n"
        f"{language_specific_instructions}"
        f"{related_links_text}"
        f"CONTENT REQUIREMENTS:\n"
        f"1. Make each section extremely detailed, professional, and comprehensive - cover the topic '{subject}' with expert-level depth and analysis.\n"
        f"2. Include real-world examples, case studies, statistics, and actionable step-by-step instructions with specific details and metrics when possible.\n"
        f"3. Write in a professional, authoritative {language} tone that establishes genuine expertise. Address readers directly using 'you' and 'your' to increase engagement.\n"
        f"4. Add 6-8 external links to highly authoritative sources (major publications, university studies, industry leaders) with descriptive anchor text.\n"
        f"5. Maintain a keyword density of 2-3% for the main keyword '{subject}'. Aim for the main keyword to appear approximately 1-2 times per 100 words. This creates optimal density without keyword stuffing.\n"
        f"6. Heavily optimize for LSI (Latent Semantic Indexing) keywords by incorporating 10-15 semantically related terms to '{subject}' throughout the article. These should appear naturally within the content.\n"
        f"7. Create advanced internal linking: Convert 7-8 appropriate LSI keywords or phrases into internal links pointing to: [**{domain}/keyword-phrase**](https://{domain}/keyword-phrase) - replace spaces with hyphens in the URL portion.\n"
        f"8. For related articles provided, include links to them using descriptive anchor text that naturally fits within the content, with at least one link in each major section.\n"
        f"9. DO NOT include table of contents - start directly with the first major H2 section after the introduction and infographic.\n"
        f"10. Include multiple professional-quality formatted elements: 2-3 bulleted lists, 2-3 numbered lists, and at least one detailed comparison table or data table formatted with markdown.\n"
        f"11. Make each H2, H3, and H4 heading compelling, specific, and keyword-optimized. Follow SEO best practices: include numbers in some headings, use 'how to,' 'why,' or question formats in others, and keep headings under 60 characters.\n"
        f"12. For each heading section, start with a concise topic sentence that summarizes the section, followed by a detailed, data-backed explanation (250-400 words per H2 section).\n"
        f"13. Develop a clear hierarchy: Each H2 should have 2-3 H3 subsections, and at least one H3 should contain 1-2 H4 subsections for even more detailed analysis.\n"
        f"14. DO NOT include FAQ sections - directly incorporate questions and their detailed answers into the relevant sections as regular paragraphs and headings.\n"
        f"15. When mentioning specific tools, resources, or techniques, provide expert insights about their implementation, advantages, limitations, and competitive alternatives.\n"
        f"16. Include practical examples for immediate implementation in each section, with clear steps and expected outcomes.\n"
        f"17. Add current industry trends, future predictions backed by research, and expert insights in the relevant industry. Include recent statistics or developments (2023-2025) where appropriate.\n"
        f"18. Create a logical flow between sections, with clear transitions that connect each topic to the main subject and to adjacent headings.\n"
        f"19. Ensure each H2 section is comprehensive enough to stand alone as a mini-article on its subtopic, while still contributing to the overall narrative.\n"
        f"20. If you want to include an image for the final section before conclusion, place it BEFORE the heading, not after it.\n"
        f"21. For technical or complex topics, include practical applications or simplified explanations to make the content accessible while maintaining its professional depth."
    )
    
    try:
        # Generate article via API request
        response = gemini_request(article_prompt, model)
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

def replace_image_placeholders(article, subject, domain=DEFAULT_DOMAIN):
    # Ensure assets directories exist
    assets_dir = IMAGES_FOLDER
    os.makedirs(assets_dir, exist_ok=True)
    
    # Find all image placeholders
    pattern = r'\[IMAGE: (.*?)\]'
    image_descriptions = re.findall(pattern, article)
    
    # Track the first image path for the featured image
    featured_image = None
    
    if not image_descriptions:
        # If no placeholders found, try to use an existing image from assets
        existing_images = find_existing_images_in_assets(1)
        if existing_images:
            featured_image = existing_images[0]
            print(f"No image placeholders found, using existing image: {featured_image}")
        return article, featured_image
    
    # Replace each placeholder with an image
    modified_article = article
    for i, description in enumerate(image_descriptions):
        # We'll use the first image as the featured image for the frontmatter
        try:
            # The query should be specific and include the subject and the description
            query = f"{subject} {description}"
            
            # Use our combined image search function
            images = get_images(query)
            
            # Try up to 3 times with different queries if needed
            attempts = 0
            while not images and attempts < 3:
                attempts += 1
                if attempts == 1:
                    # Try just the description
                    query = description
                elif attempts == 2:
                    # Try the subject
                    query = subject
                else:
                    # Try a more generic term related to the subject
                    query = f"{subject} image"
                
                print(f"Retry {attempts} for image search with query: '{query}'")
                images = get_images(query)
            
            if images and len(images) > 0:
                # Find a supported image format from the available images
                valid_image = None
                for img in images:
                    img_url = img['url']
                    # Check if the URL contains valid image format indicators
                    if (img_url.endswith('.jpg') or img_url.endswith('.jpeg') or 
                        img_url.endswith('.png') or img_url.endswith('.gif') or 
                        '.jpg?' in img_url or '.jpeg?' in img_url or '.png?' in img_url or 
                        '/photo/' in img_url or '/image/' in img_url):
                        valid_image = img
                        break
                
                # If no valid images found, use the first one
                if valid_image is None and images:
                    valid_image = images[0]
                
                # If we have a valid image, use it
                if valid_image:
                    img_url = valid_image['url']
                    img_title = f"{description}"
                    img_source = valid_image.get('source', 'Image Search')
                else:
                    # No images available
                    raise Exception("No valid images found")
                
                # Create a filename with the format: keyword-title-domain-number.jpg
                # Format domain as bloggers-web-id (replacing dots with hyphens)
                domain_part = domain.replace('.', '-')  # Convert dots to hyphens (e.g., "bloggers-web-id")
                # Combine subject and description to create the keyword part
                keyword_title = slugify(f"{subject}-{description}")[:40]  # Limit length to avoid excessively long filenames
                img_filename = f"{keyword_title}-{domain_part}-{i+1}.jpg"
                img_save_path = os.path.join(assets_dir, img_filename)
                img_rel_path = f"{IMAGES_FOLDER}/{img_filename}"
                
                # Download and save the image
                try:
                    # Set up request headers
                    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
                    
                    # Download the image
                    img_response = requests.get(img_url, headers=headers, stream=True, timeout=10)
                    img_response.raise_for_status()
                    
                    # Save the image to assets folder
                    with open(img_save_path, 'wb') as img_file:
                        for chunk in img_response.iter_content(chunk_size=8192):
                            img_file.write(chunk)
                    
                    print(f"Successfully downloaded image for '{description}' to {img_save_path}")
                    
                    # Create markdown image tag with local path (ensuring it starts with a slash for absolute path)
                    if not img_rel_path.startswith('/'):
                        img_rel_path = f"/{img_rel_path}"
                    img_tag = f"![{img_title}]({img_rel_path})"
                    
                    # Store the local path to the image rather than the URL
                    if featured_image is None:
                        # Check if the image URL is valid and supported
                        if img_url and (img_url.endswith('.jpg') or img_url.endswith('.jpeg') or 
                                       img_url.endswith('.png') or img_url.endswith('.gif') or 
                                       'image' in img_url.lower()):
                            # Use the local image path from assets for the featured image
                            featured_image = f"/{img_rel_path}"  # Use relative path from site root
                            print(f"Set featured image: {img_rel_path}")
                        else:
                            print(f"Skipping unsupported image format: {img_url}")
                    
                    # Replace the placeholder with the image tag
                    modified_article = modified_article.replace(f"[IMAGE: {description}]", img_tag)
                    print(f"Successfully added image for '{description}' from {img_source}")
                
                except Exception as e:
                    print(f"Error downloading image for '{description}': {str(e)}")
                    
                    # Try to find an existing image in the assets folder to use instead
                    existing_images = find_existing_images_in_assets(1)
                    if existing_images:
                        # Use an existing image from assets folder
                        existing_img_path = existing_images[0]
                        print(f"Using existing image from assets folder: {existing_img_path}")
                        img_tag = f"![{img_title}]({existing_img_path})"
                        
                        # Use this as featured image if we don't have one yet
                        if featured_image is None:
                            featured_image = existing_img_path
                            print(f"Set featured image (from assets): {existing_img_path}")
                    else:
                        # If no existing images, create a fallback reference
                        domain_part = domain.replace('.', '-')  # Convert dots to hyphens
                        filename = f"{slugify(description)}-{domain_part}-fallback.jpg"
                        img_rel_path = f"{IMAGES_FOLDER}/{filename}"
                        
                        # Try to get any existing image from the assets folder rather than using a placeholder
                        all_assets = find_existing_images_in_assets(5)  # Get up to 5 existing images
                        if all_assets:
                            # Use an existing image from the assets folder
                            random_img = random.choice(all_assets)  # Pick a random image for variety
                            # Ensure the path starts with a slash for absolute path
                            if not random_img.startswith('/'):
                                random_img = f"/{random_img}"
                            img_tag = f"![{img_title}]({random_img})"
                            print(f"Using existing scraped image: {random_img}")
                        else:
                            # If no images at all, create a text-only reference
                            img_tag = f"<!-- Image for {img_title} could not be retrieved -->"
                            print("No images available in assets folder")
                        
                        # Still use the relative path format for consistency
                        if featured_image is None:
                            featured_image = f"/{img_rel_path}"
                            print(f"Set featured image (fallback path): {img_rel_path}")
                    
                    # Replace the placeholder with the appropriate image tag
                    modified_article = modified_article.replace(f"[IMAGE: {description}]", img_tag)
                    print(f"Replaced image placeholder with fallback for '{description}'")
                
            else:
                # If all attempts failed, keep the placeholder but mark it
                print(f"Failed to find any images for '{description}' after multiple attempts")
                modified_article = modified_article.replace(
                    f"[IMAGE: {description}]", 
                    f"<!-- Could not find image for: {description} -->"
                )
        
        except Exception as e:
            print(f"Error replacing image placeholder '{description}': {str(e)}")
            # Mark the error in a comment
            modified_article = modified_article.replace(
                f"[IMAGE: {description}]", 
                f"<!-- Error finding image: {description} - {str(e)} -->"
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

def generate_frontmatter(title, subject, permalink, category=None, publisher="Mas DEEe", featured_image=None):
    today = datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S+00:00')
    
    # Generate tags from title and subject
    tags = generate_tags_from_title(title, subject)
    
    # Use provided category or generate from subject if none provided
    if not category:
        main_category = subject.split()[0] if subject.split() else subject
    else:
        main_category = category
    
    # Create frontmatter content as string
    content = "---\n"
    content += f"title: {title}\n"
    content += f"date: {today}\n"
    content += f"publisher: {publisher}\n"
    content += f"layout: post\n"
    
    # Add featured image if available
    if featured_image:
        content += f"image: {featured_image}\n"
    
    content += "tag:\n"
    for tag in tags:  # Using tags generated from title and subject
        content += f"  - {tag}\n"
    content += f"permalink: {permalink}\n"
    content += "categories:\n"
    content += f"  - {main_category}\n"
    content += "---\n\n"
    
    return content

# Function to generate article with Jekyll frontmatter
def generate_seo_article(subject, domain=DEFAULT_DOMAIN, model_title="gemini-1.5-flash", model_article="gemini-1.5-flash", category=None, publisher="Mas DEEe"):
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
        
        # Replace image placeholders with real images
        article_with_images, featured_image = replace_image_placeholders(article, subject, domain)
        
        # Generate Jekyll frontmatter with optional custom category and featured image
        frontmatter = generate_frontmatter(title, subject, permalink, category, publisher, featured_image)
        
        # Add <!--more--> tag after the first paragraph
        paragraphs = article_with_images.split('\n\n')
        if paragraphs:
            paragraphs[0] += '\n\n<!--more-->\n\n'
            article_with_images = '\n\n'.join(paragraphs)
        
        # Create full markdown document with frontmatter
        markdown_content = frontmatter + article_with_images
        
        # Add the article to our link manager for future reference
        article_links_manager.add_article(title, subject, permalink)
        
        return {
            "title": title,
            "article": article_with_images,
            "markdown": markdown_content,
            "permalink": permalink
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

# Function to batch process all subjects from subjects.txt
def batch_generate_seo_articles(domain=None, output_folder=OUTPUT_FOLDER):
    # Ask for domain if not provided
    if domain is None:
        domain = input("\033[1;36mEnter your domain (default: " + DEFAULT_DOMAIN + "): \033[0m")
        if not domain.strip():
            domain = DEFAULT_DOMAIN
    
    # Ask for publisher name
    publisher = input("\033[1;36mEnter publisher name (default: Mas DEEe): \033[0m")
    if not publisher.strip():
        publisher = "Mas DEEe"
    
    # Ask for default category for all articles
    print("\033[1;36mCategory Options:\033[0m")
    print("1. Use automatic categories (derived from subject)")
    print("2. Enter a single category for all articles")
    print("3. Enter category for each article individually")
    
    category_choice = input("\033[1;36mSelect category option (1-3): \033[0m")
    default_category = None
    
    if category_choice == "2":
        default_category = input("\033[1;36mEnter the category for all articles: \033[0m")
    
    # Create output folder if it doesn't exist
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        print_status(f"Created output folder: {output_folder}", "success")
        
    # Create assets folder structure in root
    if not os.path.exists(IMAGES_FOLDER):
        os.makedirs(IMAGES_FOLDER)
        print_status(f"Created images folder: {IMAGES_FOLDER}", "success")
    
    # Read subjects from file
    subjects = read_subjects_file()
    if not subjects:
        print_status("No subjects found in subjects.txt. Please add subjects first.", "error")
        return []
    
    total_subjects = len(subjects)
    print_status(f"Found {total_subjects} keywords in subjects.txt", "success")
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
            
            # Generate SEO article with appropriate category
            print_status(f"Generating article for: {subject}", "working")
            if article_category:
                print_status(f"Using category: {article_category}", "info")
            result = generate_seo_article(subject, domain, "gemini-1.5-flash", "gemini-1.5-flash", article_category, publisher)
            
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
            
            # Small delay to avoid hitting API rate limits
            time.sleep(1.5)
            
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
    print("║  \033[1;36mSEO ARTICLE GENERATOR ULTIMATE v1.0\033[0m                                   ║")
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
    print("\n\033[1;36m" + "=" * 40 + " MAIN MENU " + "=" * 40 + "\033[0m\n")
    print("  1. Generate SEO Articles")
    print("  2. Export Articles to HTML")
    print("  3. Export Articles to WordPress XML")
    print("  4. Export Articles to Blogspot XML")
    print("  5. Export All Formats (HTML, WordPress & Blogspot XML)")
    print("  0. Exit\n")
    
    choice = input("\033[1;36mEnter your choice (0-5): \033[0m")
    return choice.strip()

# Function to run the export process
def run_export(export_type="all"):
    print_status("Starting export process...", "working")
    
    # Import the export module
    try:
        import importlib
        # Try to import markdown_to_html_xml, if it fails, print a warning
        markdown_to_html_xml = None
        try:
            import markdown_to_html_xml as md_module
            # Reload the module to ensure we have the latest version
            importlib.reload(md_module)
            markdown_to_html_xml = md_module
        except ImportError:
            print_status("markdown_to_html_xml module not found. Export features may not work properly.", "warning")
            return
        
        if export_type == "html" or export_type == "all":
            print_status("Converting articles to HTML...", "working")
            posts = markdown_to_html_xml.process_markdown_files_to_html()
            if posts:
                print_status(f"Successfully exported {len(posts)} articles to HTML", "success")
            else:
                print_status("No articles were exported to HTML", "error")
        
        if export_type == "wordpress" or export_type == "all":
            print_status("Generating WordPress XML export...", "working")
            # First ensure we have HTML files
            if export_type == "wordpress":
                posts = markdown_to_html_xml.process_markdown_files_to_html()
            
            # Skip WordPress XML generation for now as it's not implemented
            print_status("WordPress XML export is not implemented yet", "info")
        
        if export_type == "blogspot" or export_type == "all":
            print_status("Generating Blogspot XML export...", "working")
            # First ensure we have HTML files
            if export_type == "blogspot":
                posts = markdown_to_html_xml.process_markdown_files_to_html()
            else:
                # Process markdown files again to ensure we have the latest data
                posts = markdown_to_html_xml.process_markdown_files_to_html()
            
            if posts:
                result = markdown_to_html_xml.generate_blogspot_xml(posts)
                if result:
                    print_status("Blogspot XML export created successfully", "success")
                else:
                    print_status("Failed to create Blogspot XML export", "error")
            else:
                print_status("No articles available for Blogspot XML export", "error")
        
        print_status("Export process completed", "success")
    
    except ImportError:
        print_status("Export module not found. Please make sure markdown_to_html_xml.py exists.", "error")
    except Exception as e:
        print_status(f"Error during export: {str(e)}", "error")

# Main function
def main():
    # Display header
    display_header()
    
    # Print application information
    print("  Professional SEO Article Generator with Image Integration")
    print("  Optimized for 3500-6000 word in-depth articles with comprehensive heading structure")
    print("  Dual Image Search: Bing + Yahoo for optimal image matching with content")
    print("  NEW: Manual Domain Input & Custom Category Support")
    print("  NEW: Automatic Tag Generation from Article Title")
    print("  NEW: Export to HTML and XML (WordPress & Blogspot)\n")
    
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
            # Generate articles
            print_status("Initializing article generation engine...", "working")
            time.sleep(1)  # Brief wait for professional appearance
            batch_generate_seo_articles()
        
        elif choice == "2":
            # Export to HTML
            run_export("html")
        
        elif choice == "3":
            # Export to WordPress XML
            run_export("wordpress")
        
        elif choice == "4":
            # Export to Blogspot XML
            run_export("blogspot")
        
        elif choice == "5":
            # Export all formats
            run_export("all")
        
        else:
            print_status("Invalid choice. Please enter a number between 0 and 5.", "error")
        
        # Wait for user to continue
        input("\n\033[1;36mPress Enter to continue...\033[0m")

# Entry point
if __name__ == "__main__":
    main()