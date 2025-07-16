# Cloudflare API Token Setup Instructions

## Problem
The current API token doesn't have sufficient permissions to deploy workers. We need to create a new token with proper permissions.

## Solution Steps

### 1. Create New API Token

1. Go to [Cloudflare Dashboard](https://dash.cloudflare.com/profile/api-tokens)
2. Click "Create Token"
3. Click "Custom token" → "Get started"

### 2. Configure Token Permissions

**Zone permissions:**
- Zone:Zone:Read
- Zone:Zone Settings:Read

**Account permissions:**
- Account:Cloudflare Workers:Edit
- Account:Account Settings:Read

**Account Resources:**
- Include: All accounts

**Zone Resources:**
- Include: All zones

### 3. Generate and Copy Token

1. Click "Continue to summary"
2. Click "Create Token"
3. **Copy the token immediately** (you won't see it again)

### 4. Update Configuration

Replace the API token in your Streamlit app configuration with the new token.

## Current Target Worker

- **Worker Name**: weathered-bonus-2b87
- **Target URL**: https://weathered-bonus-2b87.ahmadadnand736.workers.dev
- **Account ID**: a418be812e4b0653ca1512804285e4a0

## Next Steps

After updating the token:
1. Go to "Konfigurasi API" in the Streamlit app
2. Update the API token field
3. Save configuration
4. Go to "Deploy Worker" section
5. Click "Deploy Worker"

The system will deploy your article generator to the weathered-bonus-2b87 worker subdomain.