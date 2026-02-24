# NasGallery

<p align="center">
  <a href="https://github.com/xiaohu77/NasGallery">
    <img src="https://img.shields.io/github/stars/xiaohu77/NasGallery?style=social" alt="GitHub stars">
    <img src="https://img.shields.io/github/forks/xiaohu77/NasGallery?style=social" alt="GitHub forks">
    <img src="https://img.shields.io/github/license/xiaohu77/NasGallery" alt="License">
  </a>
  <br>
  <a href="https://github.com/xiaohu77/NasGallery/actions">
    <img src="https://img.shields.io/github/actions/workflow/status/xiaohu77/NasGallery/ci.yml" alt="Build status">
  </a>
  <img src="https://img.shields.io/github/languages/top/xiaohu77/NasGallery" alt="Language">
  <img src="https://img.shields.io/github/repo-size/xiaohu77/NasGallery" alt="Repo size">
</p>

> A modern web application for managing and viewing CBZ image archives with a beautiful gallery interface.

[English](./README_EN.md) | 简体中文

## ✨ Features

- 📚 **CBZ Archive Management** - Full support for CBZ (Comic Book ZIP) image archives
- 🖼️ **Beautiful Gallery** - Responsive masonry grid layout with lightbox viewing
- 🔍 **Smart Search** - Search albums by title, organization, model, or tags
- 🏷️ **Organization System** - Three-level classification: Organization / Model / Tags
- ⚡ **Fast Performance** - Multi-level caching system with thumbnail generation
- 📱 **PWA Support** - Installable web app with offline capabilities
- 🌙 **Dark Mode** - Built-in theme switching support
- 🔐 **Secure Authentication** - JWT-based authentication with role management
- 🚀 **Auto Scanning** - Automatic file system scanning for new content

## 🛠️ Tech Stack

### Backend
| Technology | Description |
|------------|-------------|
| [FastAPI](https://fastapi.tiangolo.com/) | Modern Python web framework |
| [SQLAlchemy](https://www.sqlalchemy.org/) | SQL toolkit and ORM |
| [Pydantic](https://docs.pydantic.dev/) | Data validation |
| [Pillow](https://python-pillow.org/) | Image processing |

### Frontend
| Technology | Description |
|------------|-------------|
| [React](https://react.dev/) | UI library |
| [TypeScript](https://www.typescriptlang.org/) | Type safety |
| [Vite](https://vitejs.dev/) | Build tool |
| [TailwindCSS](https://tailwindcss.com/) | Utility-first CSS |

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
- npm or yarn

### Installation

1. **Clone the repository**

```bash
git clone https://github.com/xiaohu77/NasGallery.git
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

# Initialize database
python -c "from app.database import init_db; init_db()"

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

1. The default admin credentials are:
   - Username: `admin`
   - Password: `admin123`

2. Log in and navigate to the scan page to index your CBZ files

3. Place your CBZ files in the `data/images` directory

## 📋 Album Metadata Requirements

### Metadata File

Each CBZ archive can contain a `metadata.json` file to define album metadata.

### metadata.json Format

```json
{
  "institution": "Organization Name",
  "model": "Model Name",
  "title": "Album Title",
  "description": "Album Description"
}
```

### Field Description

| Field | Required | Description |
|-------|----------|-------------|
| `institution` | Yes | Organization / Institution name |
| `model` | Yes | Model name |
| `title` | Yes | Album title |
| `description` | No | Album description |

### File Naming Convention

If no `metadata.json` exists inside the CBZ file, the system will try to parse metadata from the filename.

**Naming Format:**

```
Organization__OtherInfo__ModelName__PagesP.jpg
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
├── Uniqlo__John__75P.cbz
├── Uniqlo__John__80P.cbz
└── Organization__Model__100P/
    ├── metadata.json
    ├── 001.jpg
    ├── 002.jpg
    └── ...
```

### Auto Classification

The system automatically extracts the following tags from metadata:

- **Organization (org)**: Extracted from `institution` field
- **Model (model)**: Extracted from `model` field
- **Tags**: Matched keywords from `title` and `description`

Supported tag keywords: `美腿`, `巨乳`, `黑丝`, `足控`, `制服`, `高跟`, `cosplay`, `白丝`, `JK`, `教师`, `多人`, `女仆`, `护士`, `清纯`

## 📁 Project Structure

```
NasGallery/
├── backend/
│   ├── app/
│   │   ├── api/endpoints/     # API routes
│   │   ├── services/          # Business logic
│   │   ├── models.py          # Database models
│   │   ├── schemas.py         # Pydantic schemas
│   │   ├── database.py        # Database config
│   │   └── main.py            # App entry point
│   ├── data/                  # Data directory
│   │   ├── images/            # CBZ files
│   │   └── tmp/               # Cache files
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── components/        # React components
│   │   ├── pages/            # Page components
│   │   ├── hooks/            # Custom hooks
│   │   ├── contexts/         # React Context
│   │   ├── services/         # API services
│   │   └── types/            # TypeScript types
│   ├── public/
│   └── package.json
│
├── .env                       # Environment config
├── docker-compose.yml         # Docker Compose
├── Dockerfile                 # Docker image
└── README.md
```

## 📡 API Documentation

Once the server is running, visit:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `PROJECT_NAME` | Project name | `GirlAtlas` |
| `DATABASE_URL` | Database URL | `sqlite:///./data/nasgallery.db` |
| `SECRET_KEY` | JWT secret key | Auto-generated |
| `ADMIN_USERNAME` | Admin username | `admin` |
| `ADMIN_PASSWORD` | Admin password | `admin123` |
| `IMAGES_DIR` | CBZ files directory | `./data/images` |
| `VITE_API_BASE` | API base URL | `http://localhost:8000` |

## 🐳 Docker Deployment

```bash
# Build and run with Docker Compose
docker-compose up -d

# Or build individually
docker build -t nasgallery .
docker run -d -p 8000:8000 -v ./data:/app/data nasgallery
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

<p align="center">
  Made with ❤️ by <a href="https://github.com/xiaohu77">xiaohu77</a>
</p>

## ⭐ Star History

[![Star History Chart](https://api.star-history.com/svg?repos=xiaohu77/NasGallery&type=Date)](https://star-history.com/#xiaohu77/NasGallery&Timeline)
