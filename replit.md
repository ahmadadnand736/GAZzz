# SEO Content Generator

## Overview

This is a Python-based SEO content generator that creates automated blog posts and articles using AI (Google's Gemini API). The system is designed to generate high-quality, SEO-optimized content for investment and finance topics, with built-in Jekyll integration for static site generation.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Core Architecture
The application follows a script-based architecture with the following key components:

1. **Content Generation Engine**: Python script that leverages Google's Gemini API for content creation
2. **Static Site Framework**: Jekyll-based blog structure with custom layouts
3. **Content Management**: File-based storage system for articles and metadata
4. **SEO Optimization**: Built-in SEO features including meta tags, structured data, and social sharing

### Technology Stack
- **Backend**: Python 3.x
- **AI Service**: Google Gemini API (multiple API keys for scaling)
- **Static Site Generator**: Jekyll
- **Content Format**: Markdown with YAML frontmatter
- **Styling**: Custom CSS within Jekyll layouts

## Key Components

### 1. Content Generation System
- **Main Script**: `seo_generator_final.py` - Core content generation logic
- **API Key Management**: Rotation system using multiple Google Gemini API keys from `apikey.txt`
- **Subject Management**: Topic sourcing from `subjects.txt` file
- **Multiprocessing Support**: Concurrent content generation for improved performance

### 2. Jekyll Integration
- **Layout System**: Custom Jekyll layouts in `_layouts/` directory
- **Post Structure**: Generated content stored in `_posts/` directory
- **Asset Management**: Images stored in `assets/image/` directory
- **SEO Features**: Open Graph meta tags, structured data, and social sharing integration

### 3. Content Management
- **Article Links Manager**: Internal linking system for SEO enhancement
- **Metadata Tracking**: JSON-based article tracking in `article_links.json`
- **Content Organization**: Automated categorization and tagging

## Data Flow

1. **Topic Selection**: System reads topics from `subjects.txt`
2. **Content Generation**: Python script calls Google Gemini API to generate articles
3. **Content Processing**: Generated content is formatted with Jekyll frontmatter
4. **File Creation**: Articles saved as Markdown files in `_posts/` directory
5. **Link Management**: Article metadata stored in `article_links.json` for internal linking
6. **Site Generation**: Jekyll processes files to create static website

## External Dependencies

### APIs and Services
- **Google Gemini API**: Primary AI service for content generation
- **Multiple API Keys**: Load balancing across different API keys for scaling

### Python Libraries
- `requests`: API communication
- `markdown`: Content processing
- `frontmatter`: YAML frontmatter handling
- `slugify`: URL-friendly slug generation
- `langdetect`: Language detection
- `langcodes`: Language code handling

### Jekyll Dependencies
- Jekyll static site generator
- Custom layouts and templates
- SEO optimization plugins

## Deployment Strategy

### Local Development
- Python script execution for content generation
- Jekyll serve for local testing
- File-based content management

### Production Considerations
- **API Key Management**: Secure storage and rotation of Google Gemini API keys
- **Content Scaling**: Multiprocessing support for high-volume content generation
- **SEO Optimization**: Built-in meta tags, structured data, and social sharing
- **Static Site Deployment**: Jekyll-compatible with GitHub Pages, Netlify, or similar platforms

### Key Features
- **Automated Content Generation**: AI-powered article creation
- **SEO Optimization**: Built-in SEO best practices
- **Internal Linking**: Automatic cross-referencing between articles
- **Multi-language Support**: Language detection and proper handling
- **Social Sharing**: Open Graph integration for social media
- **Responsive Design**: Mobile-friendly layout system

### Architecture Benefits
- **Scalability**: Multiple API keys and multiprocessing support
- **SEO-First**: Built-in optimization features
- **Maintainability**: Clean separation between content generation and presentation
- **Flexibility**: Easy to modify topics, templates, and output formats
- **Performance**: Static site generation for fast loading times