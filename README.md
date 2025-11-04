
# TalentAI Pro

A comprehensive microservices-based talent management platform designed for recruiters and candidates to manage job postings, applications, resume parsing, and AI-powered matching.

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Technology Stack](#technology-stack)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Running Services](#running-services)
- [Development Workflow](#development-workflow)
- [API Documentation](#api-documentation)
- [Testing](#testing)
- [Deployment](#deployment)
- [Contributing](#contributing)
- [License](#license)

## Overview

TalentAI Pro is a full-stack application that streamlines the recruitment process through:

- User authentication and role-based access control
- Job posting and application management
- Resume parsing and skill extraction using NLP
- ML-powered job-resume matching algorithm
- Real-time notifications and analytics
- AI-powered interview system
- Workflow orchestration

## Architecture

The application follows a microservices architecture with a shared data layer:

```

API Gateway (Port 8000)
|
+-- Auth Service (Port 8001)
+-- Job Service (Port 8002)
+-- Resume Parser (Port 8003)
+-- Matching Engine (Port 8004)
+-- Notification Service (Port 8005)
+-- Analytics Service (Port 8006)
+-- AI Interview Service (Port 8007)
+-- Workflow Service (Port 8008)

```

Shared Infrastructure:
- PostgreSQL Database
- Redis Cache
- Elasticsearch
- Next.js Frontend (Port 3000)

## Technology Stack

### Backend
- Python 3.13+
- FastAPI (async framework)
- SQLAlchemy (ORM)
- Pydantic (data validation)
- Poetry (dependency management)
- Pytest (testing)

### Frontend
- Next.js 14+
- React 18+
- TypeScript
- TailwindCSS

### Infrastructure
- PostgreSQL 15+
- Redis 7+
- Elasticsearch 8+
- Docker & Docker Compose
- Nginx (API Gateway)

### ML & NLP
- spaCy (Named Entity Recognition)
- PyPDF2 (PDF parsing)
- python-docx (DOCX parsing)
- pytesseract (OCR)

## Project Structure

```

talentai-pro/
├── backend/
│   ├── services/
│   │   ├── auth_service/
│   │   ├── job_service/
│   │   ├── resume_parser_service/
│   │   ├── matching_engine_service/
│   │   ├── notification_service/
│   │   ├── analytics_service/
│   │   ├── ai_interview_service/
│   │   └── workflow_service/
│   ├── shared/
│   │   ├── common/
│   │   └── ml_core/
│   └── scripts/
├── frontend/
│   ├── src/
│   ├── public/
│   └── package.json
├── docs/
├── docker-compose.yml
├── nginx.conf
└── .gitignore

```


## Prerequisites

- Python 3.13+
- Node.js 18+
- Docker & Docker Compose
- Git
- PostgreSQL 15+
- Redis 7+
- Elasticsearch 8+

## Installation

### 1. Clone Repository

```

git clone [https://github.com/yourname/talentai-pro.git](https://github.com/yourname/talentai-pro.git)
cd talentai-pro

```

### 2. Configure Git

```

git config user.name "Your Name"
git config user.email "[your.email@example.com](mailto:your.email@example.com)"

```

### 3. Backend Setup

```

cd backend/services/auth_service
poetry install
poetry run pytest tests/ -v

```

Repeat for each service directory.

### 4. Frontend Setup

```

cd frontend
npm install
npm run dev

```

### 5. Environment Configuration

Create `.env` file in project root:

```

Database
DATABASE_URL=

Redis
REDIS_URL=

JWT
SECRET_KEY=your-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

Frontend
NEXT_PUBLIC_API_URL=

```

## Running Services

### Using Docker Compose (Recommended)

```

docker-compose up -d

```

Verify services:

```

curl [http://localhost:8000/health](http://localhost:8000/health) # Gateway
curl [http://localhost:8001/health](http://localhost:8001/health) # Auth Service
curl [http://localhost:8002/health](http://localhost:8002/health) # Job Service
curl [http://localhost:3000](http://localhost:3000) # Frontend

```

### Manual Service Start

```

Terminal 1: Auth Service
cd backend/services/auth_service
poetry run uvicorn app.main:app --host 0.0.0.0 --port 8001

Terminal 2: Job Service
cd backend/services/job_service
poetry run uvicorn app.main:app --host 0.0.0.0 --port 8002

Terminal 3: Frontend
cd frontend
npm run dev

```

## API Documentation

### Auth Service
- POST `/api/v1/auth/register` - Register user
- POST `/api/v1/auth/login` - Login user
- POST `/api/v1/auth/refresh` - Refresh token
- POST `/api/v1/auth/logout` - Logout user

### Job Service
- POST `/api/v1/jobs` - Create job
- GET `/api/v1/jobs` - List jobs
- GET `/api/v1/jobs/{id}` - Get job details
- PUT `/api/v1/jobs/{id}` - Update job
- DELETE `/api/v1/jobs/{id}` - Delete job
- POST `/api/v1/jobs/{id}/apply` - Apply for job

For full API documentation, see `docs/API.md`.

## Testing

### Run All Tests

```

cd backend/services/job_service
poetry run pytest tests/ -v
poetry run pytest tests/ --cov=app --cov-report=html

```

### Code Quality

```

poetry run black app/ tests/
poetry run isort app/ tests/
poetry run flake8 app/ tests/
poetry run mypy app/ --ignore-missing-imports

```

### Test Coverage Requirements

- Minimum 80% code coverage
- All critical paths tested
- Integration tests for service communication

## Deployment

### Prerequisites
- AWS account (or alternative cloud provider)
- Docker registry access
- CI/CD pipeline (GitHub Actions)

### Deployment Steps

```

1. Push to main branch
2. Tag release: git tag -a v1.0.0 -m "Release"
3. Push tags: git push origin v1.0.0
4. CI/CD pipeline builds and deploys
5. Monitor logs and metrics

```

See `docs/DEPLOYMENT.md` for detailed deployment guide.

## Contributing

1. Create feature branch: `git checkout -b feature/your-feature`
2. Make changes and commit with clear messages
3. Push to GitHub: `git push origin feature/your-feature`
4. Create Pull Request with description
5. Request review from team members
6. After approval, merge to develop
7. Delete feature branch after merge

### Commit Message Format

```

feat(service): Add new feature
fix(service): Fix bug
docs(service): Update documentation
test(service): Add tests
chore(service): Update dependencies

```

### Code Standards

- Follow PEP 8 for Python
- Use type hints
- Maintain test coverage above 80%
- Document complex functions
- No direct commits to main or develop

## Status

### Completed Phases
- Phase 1: Auth Service (Complete)
- Phase 2: Job Service (Complete)

### In Progress
- Phase 3: Resume Parser Service
- Phase 4: Matching Engine

### Planned
- Phase 5: Analytics Service
- Phase 6: Notification Service
- Phase 7: AI Interview Service
- Phase 8: Workflow Service

## License

MIT License - See `LICENSE.md` for details

## Support

For issues, bugs, or questions:
1. Check existing GitHub Issues
2. Create new Issue with detailed description
3. Contact team via Slack channel

## Team

- Satyam Sharma (Lead Developer)
- Team Members (Contributor)

---

Last Updated: November 2025  
Version: 1.0.0
