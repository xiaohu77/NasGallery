# NasGallery

> A modern web application for managing and viewing CBZ image archives with a beautiful gallery interface.

## ✨ Why NasGallery?

Most image management solutions (like Google Photos, Nextcloud Gallery) are designed for general-purpose photos and don't suit the niche of managing anime/fan-created image archives. NasGallery is purpose-built for CBZ-format doujinshi collections, offering differentiated capabilities:

| Feature | NasGallery | Google Photos | Nextcloud Gallery | Calibre-Web |
|---------|-----------|--------------|-------------------|-------------|
| CBZ comic format support | ✅ Native parsing | ❌ | ❌ | ❌ |
| Doujinshi metadata (org/model/cosplayer/character) | ✅ Auto-extract | ❌ | ❌ | ❌ |
| CLIP Chinese semantic search | ✅ Chinese-optimized | ❌ | ❌ | ❌ |
| Scheduled auto-scan + AI vectorization | ✅ | ❌ | ❌ | ❌ |
| PWA offline access | ✅ | ❌ | ✅ | ❌ |
| Multi-level cache + thumbnails | ✅ | ✅ | ✅ | ❌ |
| Docker one-click deployment | ✅ | ❌ | ✅ | ✅ |
| Auto memory release (AI model) | ✅ Process restart on timeout | N/A | N/A | N/A |

### Key Advantages

**1. Purpose-built for Doujinshi Collections**
- CBZ comic format with embedded `metadata.json` auto-parsing
- Classification dimensions: Organization (ORG), Model, Cosplayer, Character
- Adapted to anime fandom naming conventions (`OrgName__ModelName__XXP.cbz`)

**2. Chinese Semantic AI Search**
- Chinese-CLIP powered natural language image search
- Describe scenes in plain Chinese: "穿红色连衣裙的女孩", "海边风景"
- Intel/NVIDIA GPU acceleration with OpenVINO and CUDA support

**3. Lazy Loading + On-demand Loading**
- Masonry grid with infinite scroll, handles large datasets smoothly
- Thumbnail pre-generation + multi-level caching
- AI model loaded on-demand, auto-unload after 30 min idle, process restart frees memory

**4. Out-of-the-box Deployment**
- Docker one-click deployment, no manual configuration
- Scheduled tasks auto-execute (daily 4:00 AM scan + AI vectorization)
- Alembic database migration runs automatically on startup

## ✨ Core Features

- 📚 **CBZ Archive Management** - Full support for CBZ (Comic Book ZIP) image archives
- 🖼️ **Beautiful Gallery** - Responsive masonry grid layout with lightbox viewing
- 🔍 **Smart Search** - Search albums by title, organization, model, or tags
- 🤖 **AI Semantic Search** - CLIP-based natural language image search
- 🏷️ **Organization System** - Primary classification: All Albums / Organization / Model / Cosplayer / Character
- ⚡ **High Performance** - Multi-level caching with thumbnail generation
- 📱 **PWA Support** - Installable web app with offline capabilities
- 🌙 **Dark Mode** - Built-in theme switching support
- 🔐 **Secure Authentication** - JWT-based authentication with role management
- 🚀 **Auto Scanning** - Async scanning tasks with pause/resume/cancel support
- 🎮 **GPU Acceleration** - Intel GPU (OpenVINO) and NVIDIA GPU (CUDA) support
- ⏰ **Scheduled Scanning** - Daily auto-scan at 4:00 AM (file scan + AI vectorization)

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
- npm or yarn

### Installation

1. **Clone the repository**

```bash
git clone https://github.com/wwgxx/NasGallery.git
cd NasGallery
```

2. **Backend Setup**

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# (Optional) Configure environment
cp ../.env.example .env
# Edit .env with your settings
```

3. **Frontend Setup**

```bash
cd frontend

# Install dependencies
npm install

# (Optional) Configure environment
cp .env.example .env
# Edit .env with your API URL
```

### Running the Application

**Backend:**

```bash
cd backend
python run.py
# or
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at `http://localhost:8000`

**Frontend:**

```bash
cd frontend
npm run dev
```

The app will be available at `http://localhost:5173`

### Initial Setup

1. Default admin credentials:
   - Username: `admin`
   - Password: `admin123`

2. Log in and navigate to Settings → Scan to index your CBZ files

3. Place your CBZ files in the `data/images` directory

## 📋 Album Metadata Requirements

### Metadata File

Each CBZ archive can contain a `metadata.json` file to define album metadata.

### metadata.json Format

```json
{
  "institution": "Organization Name",
  "model": "Model Name",
  "cosplayer": "Cosplayer Name",
  "character": "Character Name",
  "title": "Album Title",
  "description": "Album Description"
}
```

### Field Description

| Field | Required | Description |
|-------|----------|-------------|
| `institution` | No | Organization / Institution name |
| `model` | No | Model name |
| `cosplayer` | No | Cosplayer name |
| `character` | No | Character name |
| `title` | Yes | Album title |
| `description` | No | Album description |

### File Naming Convention

If no `metadata.json` exists inside the CBZ file, the system will try to parse metadata from the filename.

**Naming Format:**

```
Organization__OtherInfo__ModelName__PagesP.cbz
```

**Example:**

```
Uniqlo__2024.01.15__John__75P.cbz
```

Parsed result:
- Organization: `Uniqlo`
- Model: `John`

### Directory Structure

```
data/images/
├── org/                    # Organized by organization
│   ├── Uniqlo/
│   │   ├── Uniqlo__John__75P.cbz
│   │   └── Uniqlo__Jane__80P.cbz
│   └── ...
├── model/                  # Organized by model
│   ├── John/
│   │   └── John__PhotoSet__100P.cbz
│   └── ...
├── cosplayer/              # Organized by cosplayer
│   ├── cosplayer_name/
│   │   └── cosplay_album.cbz
│   └── ...
├── character/              # Organized by character
│   ├── character_name/
│   │   └── character_album.cbz
│   └── ...
└── Organization__Model__100P/    # Folder albums
    ├── metadata.json
    ├── 001.jpg
    ├── 002.jpg
    └── ...
```

### Auto Classification

The system automatically extracts the following tags from metadata and directory structure:

- **Organization (org)**: From `institution` field or `org/` directory
- **Model (model)**: From `model` field or `model/` directory
- **Cosplayer (cosplayer)**: From `cosplayer` field or `cosplayer/` directory
- **Character (character)**: From `character` field or `character/` directory
- **Tags**: Matched keywords from `title` and `description`

Supported tag keywords: landscape, portrait, anime, CG, impasto, oil painting, comic, watercolor, Chinese painting

## 🔧 Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `PROJECT_NAME` | Project name | `NasGallery` |
| `DATABASE_URL` | Database URL | `sqlite:///./data/nasgallery.db` |
| `SECRET_KEY` | JWT secret key | Auto-generated |
| `ADMIN_USERNAME` | Admin username | `admin` |
| `ADMIN_PASSWORD` | Admin password | `admin123` |
| `IMAGES_DIR` | CBZ files directory | `./data/images` |
| `VITE_API_BASE` | API base URL | `http://localhost:8000` |
| `TAG_KEYWORDS` | Tag keywords (comma separated) | landscape, portrait, anime, CG, impasto, oil painting, comic, watercolor, Chinese painting |

## 🔄 Database Migration

The project uses Alembic for database version management.

```bash
cd backend

# Generate migration
alembic revision --autogenerate -m "description"

# Apply migration
alembic upgrade head

# Rollback migration
alembic downgrade -1

# View migration status
alembic current
alembic history
```

**First deployment:** Migrations run automatically on app startup, no manual action needed.

## 🤖 AI Search Setup (Optional)

AI search requires additional setup:

1. **Download Chinese-CLIP Model**

```bash
# Create model directory
mkdir -p backend/data/ai_models/chinese-clip

# Download base model (~754MB)
cd backend/data/ai_models/chinese-clip
wget https://huggingface.co/Xenova/chinese-clip-vit-base-patch16/resolve/main/onnx/model.onnx -O model.onnx

# Download tokenizer
mkdir -p tokenizer
wget https://huggingface.co/bert-base-chinese/resolve/main/vocab.txt -O tokenizer/vocab.txt
```

2. **Install GPU Acceleration (Optional)**

```bash
# Intel GPU (OpenVINO) - Recommended for integrated graphics
pip install onnxruntime-openvino

# NVIDIA GPU (CUDA) - Requires NVIDIA GPU
pip install onnxruntime-gpu
```

3. **Initialize AI Vectors**

Navigate to Settings → AI Search → Click "Scan"

4. **Using AI Search**

Click the 💡 icon in the search box to switch to AI search mode and enter natural language descriptions

## 🐳 Docker Deployment

```bash
# Build and run with Docker Compose
docker-compose up -d

# Or build individually
docker build -t nasgallery .
docker run -d -p 8000:8000 -v ./data:/app/data nasgallery
```

## 📁 Live Demo

https://nasgallery.xiaohu777.cn/
Username: admin Password: admin123

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 👨‍💻 About Author

| Info | Content |
|------|---------|
| Author | 程序员零一 |
| GitHub | [@xiaohu77](https://github.com/xiaohu77) |

<p align="center">
  Made with ❤️ by <a href="https://github.com/xiaohu77">程序员零一</a>
</p>

## ⭐ Star History

[![Star History Chart](https://api.star-history.com/svg?repos=xiaohu77/NasGallery&type=Date)](https://star-history.com/#xiaohu77/NasGallery&Timeline)
