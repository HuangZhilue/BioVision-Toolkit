# BioVision-Toolkit

![Developed by AI Agent](https://img.shields.io/badge/Developed_with-AI_Agent-blueviolet?style=for-the-badge)

[English](README_en.md) | [简体中文](README.md)

A species identification system powered by the local BioCLIP model, integrating the iNaturalist API for professional flora and fauna recognition. This project supports fully localized/offline execution and comes with a suite of mini-tools for batch image tagging and media publishing.

## 🌟 Core Features

1. **📸 AI Species Identification (Professional Offline Version)**
   - Upload images of plants or animals for fast identification using the local BioCLIP model.
   - Supports drag-and-drop bounding box selection for the specific subject you want to identify.
   - **Taxonomic Filtering**: Precisely select the broad biological category (e.g., plants, birds, insects). If identifying the exact "species" is not possible, the system will attempt to narrow it down to the "genus" or "family".
   - **Regional Restriction**: Specify a province or pinpoint a location on the map. The system will automatically downrank species never recorded in that area, significantly boosting the accuracy of local species identification.

![Offline AI Species Identification](sample/离线识别主界面与框选功能.png)

2. **🌐 AI Species Identification (Online Backup Version)**
   - Serves as a supplement to the offline version, useful when local resources are limited or alternative API support is required.

![Online AI Species Identification](sample/在线识别界面.png)

3. **🏷️ Kestrel Batch Labeling**
   - Efficiently manage and batch-process image datasets, quickly appending labels to species data.

![Kestrel Batch Labeling](sample/Kestrel批量打标.png)

4. **📝 Bilibili Publisher Assistant**
   - Designed specifically for Bilibili creators, helping to quickly generate and publish dynamic posts or video content related to species identification.

![Bilibili Publisher Assistant](sample/Bilibili发布助手.png)

## 🚀 Quick Start

This project provides two deployment methods: **Docker** (Recommended) and **Windows Native**.

### Method 1: Docker Deployment (Recommended)
The project comes with a fully configured Docker environment, allowing direct deployment while avoiding complex dependency configurations.

1. **Prerequisites**: Ensure your device has [Docker](https://www.docker.com/) and [Docker Compose](https://docs.docker.com/compose/) installed.
2. **Start the Service**: Run the following command in the project root directory to start the application in the background:
   ```bash
   docker-compose up -d --build
   ```
3. **Access the System**: Once started, please visit 👉 **[http://localhost:29844/](http://localhost:29844/)** in your browser.

### Method 2: Windows Native (No Docker)
If you do not have Docker installed, you can use a one-click startup script on Windows. The script will automatically create a virtual environment and install the required dependencies.

1. **Prerequisites**: Ensure your system has **Python 3.8 or above** installed, and check the `Add to PATH` option during installation.
2. **Start the Service**: Double-click the `start.bat` file in the project root directory. On the first run, it will automatically download dependencies and enter an interactive console menu with the following options:
   - `[1]` 🚀 Start Web Service
   - `[2]` 🔄 Rebuild the Ultimate Database
   - `[3]` 🖼️ Download Missing Bird Images
3. **Access the System**: After entering `1` to start the service, please visit 👉 **[http://127.0.0.1:8000/](http://127.0.0.1:8000/)** in your browser.
   *(Note: The local native startup defaults to port 8000, differentiating it from the Docker version's 29844)*

## ⚙️ Get iNaturalist Token
To fully utilize the API's capabilities, it is recommended to configure an iNaturalist Token:
- Please log in and visit the [iNaturalist API Token page](https://www.inaturalist.org/users/api_token) to obtain it.

## 🛠️ Tech Stack
- **Backend**: Python, FastAPI, BioCLIP (PyTorch)
- **Deployment**: Docker / Docker Compose
- **Other Mechanisms**: Automated offline database downloading/building, APScheduler-based background maintenance tasks, etc.
