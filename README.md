# Historical Image Dataset Crawler (2010-2025)

This project is a multi-threaded, fault-tolerant Python tool that aggregates historical images from multiple sources (Wikimedia & Bing). 

### Features
- **Multi-threading:** High-speed downloads using `ThreadPoolExecutor`.
- **Data Integrity:** EXIF metadata validation for temporal consistency.
- **Robustness:** Fallback mechanisms between multiple data providers.
- **Automated Metadata:** Synchronizes file system timestamps with historical data.

### Setup
`pip install -r requirements.txt`
`python3 elite_dataset.py`
