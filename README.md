# 📺 DUDE TV API Scraper & Decryptor

[![Run Feed Processor](https://github.com/mdjamsad9/dudetvapi/actions/workflows/scheduler.yml/badge.svg)](https://github.com/mdjamsad9/dudetvapi/actions/workflows/scheduler.yml)
[![Telegram Channel](https://img.shields.io/badge/Telegram-Join%20Channel-blue?style=for-the-badge&logo=telegram)](https://t.me/dude_tv)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg?style=for-the-badge)](https://opensource.org/licenses/MIT)

This repository provides an automated, high-performance solution that fetches, decrypts, and hosts static JSON feeds from the DUDE TV API endpoints. Operating entirely through GitHub Actions, it hosts a clean, fully-decrypted version of categories, live matches, TV channels, DRM headers, and stream parameters.

---

## ⚡ Key Features

* **Dynamic Domain Resolution**: Automatically parses `appPref.xml` from the running emulator to identify the active Firebase Remote Config domain (e.g., `cdn-stream.top`), ensuring zero-downtime when API endpoints change.
* **Dual-Stage Decryption**: Handles both standard AES-CBC `0x02` dynamic IV encryption directly in Python and custom `DEADBEEF` format payloads via a native JNI emulation fallback.
* **High-Speed Caching**: Features parallel HTTP payloads retrieval and hash-based caching to skip unchanged channel payloads, dropping processing times by up to 70%.
* **Automatic Sanitization**: Cleans and replaces all legacy "SportzX" branding with "DUDE Tv" automatically in the JSON responses.
* **DRM clearKey Extractor**: Extracts playback licenses and Key-ID mapping for encrypted live events and premium streams.

---

## 📁 Repository Structure

* [`fetch_and_decrypt.py`](file:///c:/Users/mdjam/OneDrive/Desktop/sportzx_smali/api_processor_template/fetch_and_decrypt.py): The core orchestration script managing HTTP fetching, emulator interactions, and encryption parsing.
* [`config.json`](file:///c:/Users/mdjam/OneDrive/Desktop/sportzx_smali/api_processor_template/config.json): Central settings file defining targeted endpoints and AES decryption keys.
* [`DUDETv_3.0v.apk`](file:///c:/Users/mdjam/OneDrive/Desktop/sportzx_smali/api_processor_template/DUDETv_3.0v.apk): The official companion application APK installed on the runner for JNI decryption context.
* [`.github/workflows/scheduler.yml`](file:///c:/Users/mdjam/OneDrive/Desktop/sportzx_smali/api_processor_template/.github/workflows/scheduler.yml): CI/CD schedule that boots up an Android Emulator, starts Frida services, and automatically updates the endpoints.
* `public_decrypted/`: The output directory containing structured, static, and production-ready JSON API endpoints.

---

## 📡 Live Decrypted Endpoints (GitHub Pages API)

All endpoints are hosted and served via GitHub Pages at:
`https://mdjamsad9.github.io/dudetvapi/public_decrypted/`

| Endpoint File | Description | Output URL |
|---|---|---|
| **Categories Menu** | Main channel categories | [cats.json](https://mdjamsad9.github.io/dudetvapi/public_decrypted/cats.json) |
| **Sports Channels** | TV channels listed under Sports | [sports.json](https://mdjamsad9.github.io/dudetvapi/public_decrypted/sports.json) |
| **Live Matches** | Current & upcoming match events | [events.json](https://mdjamsad9.github.io/dudetvapi/public_decrypted/events.json) |
| **Combined Database** | Consolidated event list with resolved stream keys | [events_with_channels.json](https://mdjamsad9.github.io/dudetvapi/public_decrypted/events_with_channels.json) |
| **Match Highlights** | Recent sports replays and highlights | [highlights.json](https://mdjamsad9.github.io/dudetvapi/public_decrypted/highlights.json) |
| **TV Channel Streams** | Specific stream directories per ID | `channels/{id}.json` (e.g. [channels/1.json](https://mdjamsad9.github.io/dudetvapi/public_decrypted/channels/1.json)) |

---

## 🛠️ Local Running & Testing

To execute the scraper locally on your machine:

1. **Pre-requisites**:
   * Setup an Android Emulator running **Pixel 4, API 33** (rooted).
   * Ensure `adb` is installed and in your environment PATH.

2. **Clone and Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Install the Companion APK**:
   ```bash
   adb install -g DUDETv_3.0v.apk
   ```
   *Open the app on the emulator once to let it register and download Remote Config details.*

4. **Run the script**:
   ```bash
   python fetch_and_decrypt.py
   ```

---

## 💬 Community

Get real-time updates, chat with other developers, and report domain or stream issues directly on our Telegram channel:

👉 **[Join DUDE TV Telegram Channel](https://t.me/dude_tv)**

---

## ☕ Support the Project (Donations)

If this API Scraper helps you maintain your projects, streams, or apps, consider buying us a coffee! Your support keeps the domain tracking servers and automation scripts running 24/7.

### 🪙 Supported Cryptocurrencies

| Platform / Network | Wallet Address / Pay ID |
| :--- | :--- |
| **Bitcoin (BTC)** <br> *Bitcoin Mainnet Network* | `12zBsP3LBp352tqCsENS997j1AoCybtW6M` |
| **Binance Pay** <br> *Direct User-to-User Transfer* | **Pay ID:** `1247002770` |

---
*Created and maintained by developers, for developers.*
