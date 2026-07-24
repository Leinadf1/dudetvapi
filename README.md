# DUDE TV API Scraper & Decryptor

This repository automatically fetches, decrypts, and hosts static JSON feeds from the DUDE TV API endpoints using GitHub Actions.

## How it Works

The scraper runs automated decryption:
1. **Automated Python Decryption**: Endpoints (categories, events, live matches, channel lists, and DRM headers) are fetched and decrypted directly using AES decryption with static credentials and dynamic IV handling.
2. **Branding & Sanitization**: All content is sanitized to replace legacy "SportzX" branding with "DUDE Tv".
3. **Consolidated Feeds**: Generates `events_with_channels.json`, a merged database of live events with active stream links, alongside dedicated subfolders (`cats/`, `channels/`).

All decrypted outputs are saved in the `public_decrypted/` directory, hosted via GitHub Pages to serve as a clean API.

## Repository Structure

- `fetch_and_decrypt.py`: Main automation script that fetches and decrypts all API feeds.
- `config.json`: Configuration specifying the target API URLs.
- `.github/workflows/scheduler.yml`: GitHub Actions workflow that runs the decryption script on a schedule and pushes updated data.
- `public_decrypted/`: Directory containing all decrypted static JSON files.

## Setup Instructions

### 1. Enable Workflow Write Permissions on GitHub
For the GitHub Actions workflow to push the decrypted feeds back to your repository:
1. Go to your repository **Settings** on GitHub.
2. In the left sidebar, click on **Actions** > **General**.
3. Scroll down to **Workflow permissions**.
4. Select **"Read and write permissions"** and click **Save**.

### 2. Enable GitHub Pages
To host the decrypted JSON feeds as a public API:
1. Go to your repository **Settings** > **Pages**.
2. Under **Build and deployment**, set **Source** to `Deploy from a branch`.
3. Select the `main` (or `master`) branch and click **Save**.
4. Your API will be live at: `https://<username>.github.io/<repo>/public_decrypted/`

### 3. Local Execution
To run on your local PC:
1. Install Python requirements:
   ```bash
   pip install -r requirements.txt
   ```
2. Run the script:
   ```bash
   python fetch_and_decrypt.py
   ```
