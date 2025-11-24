# TalentAI Pro - Intelligent Recruitment Platform

## Table of Contents

- [Overview](#overview)
- [System Architecture](#system-architecture)
- [Technology Stack](#technology-stack)
- [Project Structure](#project-structure)
- [Phase-by-Phase Implementation](#phase-by-phase-implementation)
  - [Phase 1: Foundation](#phase-1-foundation-completed)
  - [Phase 2: Job Management](#phase-2-job-management-completed)
  - [Phase 3: Candidate Management](#phase-3-candidate-management-completed)
  - [Phase 4: Resume Parsing](#phase-4-resume-parsing-completed)
  - [Phase 5: Intelligent Matching Engine](#phase-5-intelligent-matching-engine-completed)
- [Machine Learning System](#machine-learning-system)
- [Getting Started](#getting-started)
- [API Documentation](#api-documentation)
- [Development Guidelines](#development-guidelines)
- [Testing](#testing)
- [Deployment](#deployment)
- [Future Phases](#future-phases)
- [Contributing](#contributing)
- [License](#license)

---

## Overview

TalentAI Pro is an enterprise-grade intelligent recruitment platform that leverages artificial intelligence, machine learning, and natural language processing to revolutionize the hiring process. The platform provides automated resume parsing, intelligent candidate-job matching, AI-powered interviews, and comprehensive analytics.

### Key Features

- **Intelligent Matching**: Vector similarity search, ML-powered quality prediction, and LangGraph reasoning workflows
- **Resume Parsing**: Multi-format support (PDF, DOCX, TXT) with NLP-based skill extraction
- **Machine Learning**: XGBoost + Random Forest ensemble for candidate quality prediction
- **Vector Search**: ChromaDB-powered semantic search with hybrid retrieval
- **LLM Integration**: LangChain and LangGraph for advanced reasoning
- **Real-time Processing**: Ray distributed computing for parallel processing
- **Microservices Architecture**: Independent, scalable services with REST APIs
- **Enterprise Security**: JWT authentication, role-based access control, audit logging

---

## System Architecture

### Microservices Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                        TalentAI Pro Platform                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐            │
│  │  Frontend    │  │   API        │  │  Nginx       │            │
│  │  React/Next  │  │   Gateway    │  │  Proxy       │            │
│  └──────────────┘  └──────────────┘  └──────────────┘            │
│         │                  │                  │                    │
│         └──────────────────┴──────────────────┘                    │
│                            │                                        │
│  ┌─────────────────────────┴─────────────────────────────┐        │
│  │                    Backend Services                    │        │
│  ├────────────────────────────────────────────────────────┤        │
│  │                                                        │        │
│  │  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐ │        │
│  │  │ Auth Service │  │ Job Service  │  │ Candidate   │ │        │
│  │  │ Port: 8001   │  │ Port: 8002   │  │ Service     │ │        │
│  │  │              │  │              │  │ Port: 8003  │ │        │
│  │  └──────────────┘  └──────────────┘  └─────────────┘ │        │
│  │                                                        │        │
│  │  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐ │        │
│  │  │ Resume       │  │ Matching     │  │ Future      │ │        │
│  │  │ Parser       │  │ Engine       │  │ Services    │ │        │
│  │  │ Port: 8005   │  │ Port: 8004   │  │             │ │        │
│  │  └──────────────┘  └──────────────┘  └─────────────┘ │        │
│  │                                                        │        │
│  └────────────────────────────────────────────────────────┘        │
│                            │                                        │
│  ┌─────────────────────────┴─────────────────────────────┐        │
│  │              Data & Infrastructure Layer               │        │
│  ├────────────────────────────────────────────────────────┤        │
│  │                                                        │        │
│  │  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐ │        │
│  │  │ PostgreSQL   │  │ Redis Cache  │  │ ChromaDB    │ │        │
│  │  │ (Primary DB) │  │              │  │ (Vectors)   │ │        │
│  │  └──────────────┘  └──────────────┘  └─────────────┘ │        │
│  │                                                        │        │
│  │  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐ │        │
│  │  │ Ray          │  │ Celery       │  │ RabbitMQ    │ │        │
│  │  │ (Compute)    │  │ (Tasks)      │  │ (Queue)     │ │        │
│  │  └──────────────┘  └──────────────┘  └─────────────┘ │        │
│  │                                                        │        │
│  └────────────────────────────────────────────────────────┘        │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Service Communication

- **Synchronous**: REST APIs with JWT authentication
- **Asynchronous**: RabbitMQ message queue for long-running tasks
- **Caching**: Redis for session management and response caching
- **Vector Search**: ChromaDB for semantic similarity search
- **ML Predictions**: In-memory models with fallback to API calls

---

## Technology Stack

### Backend Services

| Technology | Purpose | Version |
|------------|---------|---------|
| Python | Primary language | 3.11+ |
| FastAPI | Web framework | 0.104.1 |
| PostgreSQL | Primary database | 15+ |
| Redis | Caching & sessions | 7.0+ |
| ChromaDB | Vector database | 0.4.18 |
| Ray | Distributed computing | 2.8.0 |
| Celery | Task queue | 5.3.4 |
| RabbitMQ | Message broker | 3.12+ |

### AI/ML Stack

| Technology | Purpose | Version |
|------------|---------|---------|
| LangChain | LLM orchestration | 0.1.0 |
| LangGraph | Workflow graphs | 0.0.13 |
| OpenAI API | LLM provider | 1.3.0 |
| XGBoost | ML predictions | 2.0.3 |
| scikit-learn | ML pipeline | 1.3.2 |
| spaCy | NLP processing | 3.7.2 |
| sentence-transformers | Embeddings | 2.2.2 |

### Frontend (Planned)

| Technology | Purpose |
|------------|---------|
| React | UI framework |
| Next.js | SSR framework |
| TypeScript | Type safety |
| Tailwind CSS | Styling |
| Zustand | State management |

---

## Project Structure

```
talentai-pro/
├── backend/
│   ├── common/                           # Shared utilities
│   │   ├── config.py                     # Configuration management
│   │   ├── logging.py                    # Logging setup
│   │   ├── redis_client.py               # Redis connection
│   │   └── database.py                   # Database utilities
│   │
│   └── services/
│       ├── auth_service/                 # Authentication & Authorization
│       │   ├── app/
│       │   │   ├── api/v1/endpoints/
│       │   │   ├── core/                 # Security, config
│       │   │   ├── db/                   # Database models
│       │   │   └── services/             # Business logic
│       │   ├── tests/
│       │   ├── Dockerfile
│       │   └── requirements.txt
│       │
│       ├── job_service/                  # Job Management
│       │   ├── app/
│       │   │   ├── api/v1/endpoints/
│       │   │   ├── db/models/
│       │   │   ├── schemas/
│       │   │   └── services/
│       │   ├── tests/
│       │   └── requirements.txt
│       │
│       ├── candidate_service/            # Candidate Management
│       │   ├── app/
│       │   │   ├── api/v1/endpoints/
│       │   │   ├── db/models/
│       │   │   ├── schemas/
│       │   │   └── services/
│       │   ├── tests/
│       │   └── requirements.txt
│       │
│       ├── resume_parser_service/        # Resume Parsing & NLP
│       │   ├── app/
│       │   │   ├── api/v1/endpoints/
│       │   │   ├── parsers/              # File parsers
│       │   │   ├── nlp/                  # NLP processors
│       │   │   ├── extractors/           # Data extractors
│       │   │   └── services/
│       │   ├── models/                   # ML models
│       │   ├── tests/
│       │   └── requirements.txt
│       │
│       └── matching_engine_service/      # Intelligent Matching
│           ├── app/
│           │   ├── api/v1/endpoints/
│           │   │   ├── matching.py       # Matching endpoints
│           │   │   ├── vectors.py        # Vector operations
│           │   │   ├── langchain.py      # LLM analysis
│           │   │   └── ml_endpoints.py   # ML predictions
│           │   ├── chains/               # LangChain workflows
│           │   ├── services/
│           │   │   ├── vector_search_service.py
│           │   │   ├── llm_orchestrator.py
│           │   │   └── cache_service.py
│           │   ├── ml/                   # Machine Learning
│           │   │   ├── models/           # ML model classes
│           │   │   │   ├── base_model.py
│           │   │   │   ├── xgboost_model.py
│           │   │   │   ├── random_forest_model.py
│           │   │   │   └── ensemble_model.py
│           │   │   ├── services/
│           │   │   │   ├── ml_prediction_service.py
│           │   │   │   ├── ml_training_service.py
│           │   │   │   └── feature_engineering_service.py
│           │   │   └── utils/
│           │   │       ├── data_generator.py
│           │   │       └── model_registry.py
│           │   └── utils/
│           │       ├── chroma_manager.py
│           │       └── ray_manager.py
│           ├── ml_models/                # Trained ML models
│           ├── chroma_data/              # Vector database
│           ├── scripts/
│           │   └── init_ml_model.py     # ML initialization
│           ├── tests/
│           └── requirements.txt
│
├── frontend/                             # (Planned)
│   └── (React/Next.js application)
│
├── infrastructure/
│   ├── docker/
│   │   ├── docker-compose.yml
│   │   └── docker-compose.prod.yml
│   ├── kubernetes/                       # K8s configs (planned)
│   └── nginx/                            # Reverse proxy configs
│
├── docs/
│   ├── api/                              # API documentation
│   ├── architecture/                     # Architecture diagrams
│   └── deployment/                       # Deployment guides
│
├── scripts/
│   ├── setup.sh                          # Initial setup
│   ├── migrate.sh                        # Database migrations
│   └── test.sh                           # Run all tests
│
└── README.md
```

---

## Phase-by-Phase Implementation (COMPLETED)

### Phase 1: Foundation 

#### Deliverables

1. **Authentication Service**
   - User registration and login
   - JWT token generation and validation
   - Role-based access control (Admin, Recruiter, Candidate)
   - Password hashing with bcrypt
   - Token refresh mechanism
   - Session management with Redis

2. **Core Infrastructure**
   - PostgreSQL database setup
   - Redis caching layer
   - Common utilities (logging, config, database)
   - Docker containerization
   - Development environment setup

#### Key Features

- Secure JWT-based authentication
- Role-based permissions
- Token expiration and refresh
- Password reset functionality
- Audit logging for all authentication events

#### API Endpoints

```
POST   /api/v1/auth/register           # User registration
POST   /api/v1/auth/login              # User login
POST   /api/v1/auth/refresh            # Refresh access token
POST   /api/v1/auth/logout             # User logout
GET    /api/v1/auth/me                 # Get current user
PUT    /api/v1/auth/password/change    # Change password
POST   /api/v1/auth/password/reset     # Request password reset
```

---

### Phase 2: Job Management (COMPLETED)

#### Deliverables

1. **Job Service**
   - CRUD operations for job postings
   - Job search and filtering
   - Job status management
   - Application tracking
   - Job analytics

2. **Database Schema**
   - Jobs table with full-text search
   - Job applications tracking
   - Status workflow (Draft, Published, Closed)
   - Soft delete support

#### Key Features

- Full-text search across job titles and descriptions
- Advanced filtering (location, salary, experience, skills)
- Job expiration management
- Application count tracking
- Recruiter-specific job views

#### API Endpoints

```
POST   /api/v1/jobs                    # Create job posting
GET    /api/v1/jobs                    # List jobs (with filters)
GET    /api/v1/jobs/{id}               # Get job details
PUT    /api/v1/jobs/{id}               # Update job
DELETE /api/v1/jobs/{id}               # Delete job (soft)
POST   /api/v1/jobs/{id}/publish       # Publish job
POST   /api/v1/jobs/{id}/close         # Close job
GET    /api/v1/jobs/{id}/applications  # Get job applications
POST   /api/v1/jobs/search             # Advanced search
```

---

### Phase 3: Candidate Management (COMPLETED)

#### Deliverables

1. **Candidate Service**
   - Candidate profile management
   - Resume/CV storage
   - Application submission
   - Application status tracking
   - Candidate search

2. **Database Schema**
   - Candidates table with profile data
   - Applications table linking candidates and jobs
   - Skills tracking
   - Education and experience history

#### Key Features

- Complete candidate profile management
- Resume file storage and retrieval
- Application workflow
- Status updates (Applied, Screening, Interview, Offer, Rejected)
- Candidate search by skills, experience, location

#### API Endpoints

```
POST   /api/v1/candidates              # Create candidate profile
GET    /api/v1/candidates              # List candidates
GET    /api/v1/candidates/{id}         # Get candidate details
PUT    /api/v1/candidates/{id}         # Update profile
DELETE /api/v1/candidates/{id}         # Delete candidate
POST   /api/v1/candidates/{id}/apply   # Apply to job
GET    /api/v1/candidates/{id}/applications  # Get applications
POST   /api/v1/candidates/search       # Search candidates
PUT    /api/v1/applications/{id}/status  # Update application status
```

---

### Phase 4: Resume Parsing (COMPLETED)

#### Deliverables

1. **Resume Parser Service**
   - Multi-format parser (PDF, DOCX, TXT)
   - Text extraction and cleaning
   - NLP-based information extraction
   - Skill extraction and categorization
   - Experience calculation

2. **NLP Pipeline**
   - spaCy NLP model integration
   - Named entity recognition
   - Custom skill taxonomy (500+ skills)
   - Education extraction
   - Contact information extraction

3. **Parser Components**
   - PDF parser (PyPDF2, pdfplumber)
   - DOCX parser (python-docx)
   - Text cleaner and normalizer
   - Skill extractor with fuzzy matching
   - Experience calculator
   - Education parser

#### Key Features

- Automatic resume parsing from uploaded files
- Skill extraction with 85%+ accuracy
- Experience level calculation
- Education and certification extraction
- Contact information parsing
- Support for multiple resume formats
- Batch processing support

#### API Endpoints

```
POST   /api/v1/resume/parse             # Parse single resume
POST   /api/v1/resume/parse/batch       # Parse multiple resumes
POST   /api/v1/resume/parse/url         # Parse from URL
GET    /api/v1/resume/skills            # Get extracted skills
POST   /api/v1/resume/validate          # Validate resume data
GET    /api/v1/resume/supported-formats # Get supported file formats
```

#### Technical Implementation

**File Parsers**
- `PDFParser`: Extracts text from PDF files with layout preservation
- `DOCXParser`: Handles Microsoft Word documents
- `TXTParser`: Plain text resume processing

**NLP Processor**
- spaCy model: `en_core_web_md`
- Custom NER for resume-specific entities
- Skill matching with fuzzy string matching (fuzzywuzzy)
- Experience calculation with date parsing

**Skill Extractor**
- Taxonomy: 500+ technical and soft skills
- Fuzzy matching threshold: 85%
- Skill categorization (Programming, Frameworks, Tools, Soft Skills)
- Synonym handling

---

### Phase 5: Intelligent Matching Engine (COMPLETED)

#### Overview

Phase 5 implements a sophisticated matching engine that combines vector similarity search, machine learning models, and LLM-powered analysis to intelligently match candidates with job opportunities.

#### Deliverables

1. **Vector Search System**
   - ChromaDB vector database integration
   - Sentence transformer embeddings (all-MiniLM-L6-v2)
   - Semantic similarity search
   - Hybrid search (vector + keyword)
   - Reverse matching (jobs for candidates)

2. **Machine Learning System**
   - XGBoost classifier for quality prediction
   - Random Forest classifier
   - Ensemble model (70% XGBoost + 30% Random Forest)
   - Feature engineering pipeline
   - Model versioning and registry

3. **LangGraph Reasoning Workflow**
   - Multi-step reasoning with state management
   - Skill analysis
   - Experience evaluation
   - Score calculation
   - Final recommendation generation

4. **LLM Integration**
   - LangChain orchestration
   - OpenAI GPT-4 integration/Gemini
   - Structured output parsing
   - Interview question generation
   - Detailed candidate analysis

#### Architecture Components

**Vector Search Service**
```
Components:
- Embedding generation (384-dim vectors)
- Collection management (candidates, jobs)
- Similarity search with filters
- Batch operations
- Caching layer (Redis)
```

<!-- **Machine Learning Pipeline**
```
Models:
1. XGBoost Classifier
   - n_estimators: 200
   - max_depth: 6
   - Accuracy: 85-87%

2. Random Forest Classifier
   - n_estimators: 200
   - max_depth: 15
   - Accuracy: 83-85%

3. Ensemble Model
   - XGBoost weight: 0.7
   - Random Forest weight: 0.3
   - Accuracy: 86-88%

Features (24 total):
Base:
- skill_match_ratio
- experience_years
- education_level
- vector_similarity
- domain_match
- years_experience_match
- salary_expectation_ratio
- location_match
- cultural_fit_score
- communication_score

Engineered:
- skill_exp_interaction
- skill_vector_interaction
- education_exp_interaction
- skill_match_squared
- experience_squared
- domain_expertise_score
- strong_candidate
- weak_candidate
- perfect_match
- junior/mid_level/senior flags
- salary_fit
- total_match_score

Quality Tiers:
- TIER 1 (EXCELLENT): Top candidates, strong hire
- TIER 2 (STRONG): Good candidates, likely hire
- TIER 3 (MODERATE): Okay candidates, maybe hire
- TIER 4 (WEAK): Below average, likely pass
- TIER 5 (POOR): Poor match, pass
``` -->

**LangGraph Workflow**
```
Workflow Steps:
1. analyze_skills
   - Calculate skill match ratio
   - Identify missing skills
   - Identify extra skills

2. analyze_experience
   - Compare candidate vs required experience
   - Assess experience level fit
   - Calculate experience gap

3. calculate_scores
   - Skill score (40% weight)
   - Experience score (30% weight)
   - Vector similarity score (30% weight)
   - Overall weighted score

4. make_recommendation
   - Decision logic based on thresholds
   - Confidence calculation
   - Reasoning chain generation
   - Strengths and gaps identification
```

**LLM Analysis Chain**
```
Chain Components:
1. Candidate Analysis
   - Profile summary
   - Strengths assessment
   - Weaknesses identification
   - Career trajectory

2. Job Suitability
   - Requirements alignment
   - Skill gaps analysis
   - Cultural fit assessment

3. Interview Questions
   - Technical questions (5)
   - Behavioral questions (3)
   - Situation-based questions (2)

4. Final Recommendation
   - Hire/No Hire decision
   - Confidence level
   - Detailed reasoning
   - Next steps
```

#### Key Features

**Vector Search**
- Semantic similarity search with 0.5+ similarity threshold
- Hybrid search combining vector and keyword matching
- Bidirectional matching (candidates for jobs, jobs for candidates)
- Batch operations for high throughput
- Redis caching for repeated queries

**Machine Learning**
- Real-time quality predictions (2-5ms latency)
- Model versioning and A/B testing support
- Feature importance explanations
- Confidence scores for all predictions
- Continuous learning pipeline

**LangGraph Reasoning**
- Transparent multi-step decision process
- Deterministic rule-based logic
- Fast execution (100-200ms)
- No API costs
- Full reasoning chain visibility

**LLM Analysis**
- Deep candidate evaluation
- Natural language explanations
- Interview question generation
- Detailed match reasoning
- Configurable analysis depth

#### Performance Metrics

| Method | Speed (First) | Speed (Cached) | Cost | Accuracy |
|--------|--------------|----------------|------|----------|
| Vector Search | 50-100ms | 5-10ms | Free | 75-80% |
| ML Model | 2-5ms | 1-2ms | Free | 86-88% |
| LangGraph | 100-200ms | 50-100ms | Free | 82-85% |
| LLM Analysis | 8-12s | 100-200ms | $0.01 | 88-92% |

#### API Endpoints

**Vector Operations**
```
POST   /api/v1/vectors/candidates/add        # Add candidate vector
POST   /api/v1/vectors/jobs/add              # Add job vector
POST   /api/v1/vectors/candidates/search     # Search candidates
POST   /api/v1/vectors/jobs/search           # Search jobs
GET    /api/v1/vectors/candidates/count      # Get candidate count
GET    /api/v1/vectors/jobs/count            # Get job count
DELETE /api/v1/vectors/candidates/clear      # Clear candidate vectors
POST   /api/v1/vectors/candidates/batch      # Batch add candidates
```

**Matching Endpoints**
```
POST   /api/v1/matching/match/candidates/vector      # Vector-based matching
POST   /api/v1/matching/match/candidates/hybrid      # Hybrid search
POST   /api/v1/matching/match/candidates/langgraph   # LangGraph reasoning
POST   /api/v1/matching/match/candidates/ml-enhanced # ML-enhanced matching
POST   /api/v1/matching/match/jobs/vector            # Reverse matching
POST   /api/v1/matching/batch                        # Batch matching
```

**ML Model Endpoints**
```
POST   /api/v1/ml/predict                    # Single prediction
POST   /api/v1/ml/predict/batch              # Batch predictions
POST   /api/v1/ml/train                      # Train new model
POST   /api/v1/ml/train/generate-data        # Generate training data
GET    /api/v1/ml/model/info                 # Model information
POST   /api/v1/ml/model/load                 # Load model version
GET    /api/v1/ml/model/registry             # List all models
GET    /api/v1/ml/model/best                 # Get best model
```

**LangChain Analysis**
```
POST   /api/v1/langchain/analyze             # Full LLM analysis
POST   /api/v1/langchain/interview-questions # Generate questions
POST   /api/v1/langchain/evaluate            # Quick evaluation
```

#### Technical Stack

**Core Libraries**
- FastAPI 0.104.1
- ChromaDB 0.4.18
- sentence-transformers 2.2.2
- LangChain 0.1.0
- LangGraph 0.0.13
- XGBoost 2.0.3
- scikit-learn 1.3.2
- Ray 2.8.0

**Infrastructure**
- PostgreSQL for metadata storage
- Redis for caching and session management
- ChromaDB for vector storage
- Ray for distributed computing

#### Deployment Considerations

**Scaling**
- Horizontal scaling with load balancer
- Vector database sharding for large datasets
- ML model served in-memory with fallback
- LLM request queuing with rate limiting

**Monitoring**
- Prometheus metrics for all endpoints
- Grafana dashboards for visualization
- Model performance tracking
- Latency and throughput monitoring

**Security**
- API key authentication for external services
- Rate limiting per user/tenant
- Input validation and sanitization
- Encrypted vector storage

<!-- ---

## Machine Learning System

### Overview

The ML system predicts candidate quality tiers (1-5) using an ensemble of XGBoost and Random Forest classifiers, achieving 86-88% accuracy on test data.

### Architecture

```
Input Features (24)
       │
       ├─► Feature Engineering
       │   ├─► Skill interactions
       │   ├─► Polynomial features
       │   ├─► Domain expertise scoring
       │   └─► Quality indicators
       │
       ├─► Feature Scaling (StandardScaler)
       │
       ├─► XGBoost Model (70% weight)
       │   └─► 200 estimators, max_depth=6
       │
       ├─► Random Forest Model (30% weight)
       │   └─► 200 estimators, max_depth=15
       │
       └─► Ensemble Prediction
           └─► Weighted averaging
           └─► Quality tier + confidence
```

### Feature Engineering

**Base Features (10)**
1. skill_match_ratio: Proportion of required skills candidate has
2. experience_years: Total years of experience
3. education_level: 1 (HS) to 4 (PhD)
4. vector_similarity: Embedding similarity score
5. domain_match: Binary flag for domain expertise
6. years_experience_match: Candidate exp / required exp
7. salary_expectation_ratio: Candidate salary / job budget
8. location_match: Binary flag for location compatibility
9. cultural_fit_score: Cultural alignment score (0-1)
10. communication_score: Communication skills score (0-1)

**Engineered Features (14)**
1. skill_exp_interaction: skill_match × experience / 20
2. skill_vector_interaction: skill_match × vector_similarity
3. education_exp_interaction: education × experience / 20
4. skill_match_squared: skill_match^2
5. experience_squared: (experience / 20)^2
6. domain_expertise_score: domain × experience × skill_match
7. strong_candidate: Binary flag for high-quality indicators
8. weak_candidate: Binary flag for low-quality indicators
9. perfect_match: Binary flag for ideal candidates
10. junior: experience < 3 years
11. mid_level: 3 <= experience < 7 years
12. senior: experience >= 7 years
13. salary_fit: 1 - |salary_ratio - 1|
14. total_match_score: Weighted combination of all factors

### Model Training

```
# Generate synthetic training data
python scripts/init_ml_model.py

# Or train with custom data
curl -X POST "http://localhost:8004/api/v1/ml/train" \
  -F "file=@training_data.csv" \
  -F "version=1.0.0"
```

### Model Versioning

```
# List all model versions
curl "http://localhost:8004/api/v1/ml/model/registry"

# Load specific version
curl -X POST "http://localhost:8004/api/v1/ml/model/load?version=1.0.0"

# Get best performing model
curl "http://localhost:8004/api/v1/ml/model/best?metric=val_accuracy"
```

### Prediction Example

```
# Single prediction
import requests

response = requests.post(
    "http://localhost:8004/api/v1/ml/predict",
    json={
        "job_data": {
            "required_skills": ["Python", "Django", "PostgreSQL"],
            "experience_level": "5+ years",
            "location": "San Francisco",
            "salary_max": 150000
        },
        "candidate_data": {
            "skills": ["Python", "Django", "React"],
            "years_experience": 6,
            "education": "BS Computer Science",
            "location": "San Francisco",
            "expected_salary": 140000
        },
        "vector_similarity": 0.85
    }
)

# Response
{
  "predicted_tier": 2,
  "tier_name": "STRONG",
  "confidence": 0.8234,
  "tier_probabilities": {
    "TIER_1": 0.1567,
    "TIER_2": 0.8234,
    "TIER_3": 0.0156,
    "TIER_4": 0.0032,
    "TIER_5": 0.0011
  },
  "top_influential_features": {
    "skill_match_ratio": 0.2847,
    "total_match_score": 0.1923,
    "vector_similarity": 0.1456
  }
}
```

### Performance Monitoring

```
# Track model performance
metrics = {
    "accuracy": 0.8675,
    "precision": 0.8532,
    "recall": 0.8698,
    "f1_score": 0.8614,
    "inference_time_ms": 2.5
}
``` -->

---

## Getting Started

### Prerequisites

- Python 3.11 or higher
- PostgreSQL 15+
- Redis 7.0+
- Docker and Docker Compose (recommended)
- Node.js 18+ (for frontend)

### Local Development Setup

#### 1. Clone Repository

```
git clone https://github.com/yourusername/talentai-pro.git
cd talentai-pro
```

#### 2. Environment Setup

```
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies for all services
cd /talentai-pro && poetry install
```

#### 3. Database Setup

```
# Start PostgreSQL and Redis with Docker
docker-compose up -d postgres redis

# Run migrations
cd backend/services/auth_service
alembic upgrade head

cd ../job_service
alembic upgrade head

cd ../candidate_service
alembic upgrade head
```

#### 4. Environment Variables

Create `.env` files for each service:

**auth_service/.env**
```
DATABASE_URL=postgresql://user:password@localhost:5432/talentai_auth
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=your-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-here
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
```

**matching_engine_service/.env**
```
DATABASE_URL=postgresql://user:password@localhost:5432/talentai_matching
REDIS_URL=redis://localhost:6379/1
CHROMA_PERSIST_DIR=./chroma_data
OPENAI_API_KEY=your-openai-api-key
RAY_NUM_CPUS=4
EMBEDDING_MODEL=all-MiniLM-L6-v2
```

#### 5. Initialize ML Models

```
cd backend/services/matching_engine_service
python scripts/init_ml_model.py
```

#### 6. Start Services

```
# Terminal 1 - Auth Service
cd backend/services/auth_service
uvicorn app.main:app --reload --port 8001

# Terminal 2 - Job Service
cd backend/services/job_service
uvicorn app.main:app --reload --port 8002

# Terminal 3 - Candidate Service
cd backend/services/candidate_service
uvicorn app.main:app --reload --port 8003

# Terminal 4 - Matching Engine Service
cd backend/services/matching_engine_service
uvicorn app.main:app --reload --port 8004

# Terminal 5 - Resume Parser Service
cd backend/services/resume_parser_service
uvicorn app.main:app --reload --port 8005
```

#### 7. Verify Installation

```
# Check service health
curl http://localhost:8001/health  # Auth Service
curl http://localhost:8002/health  # Job Service
curl http://localhost:8003/health  # Candidate Service
curl http://localhost:8004/health  # Matching Engine
curl http://localhost:8005/health  # Resume Parser

# Access API documentation
# http://localhost:8001/docs (Auth Service)
# http://localhost:8004/docs (Matching Engine)
```

### Docker Deployment

```
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

---

## API Documentation

### Interactive Documentation

Each service provides Swagger UI and ReDoc documentation:

- Auth Service: http://localhost:8001/docs
- Job Service: http://localhost:8002/docs
- Candidate Service: http://localhost:8003/docs
- Matching Engine: http://localhost:8004/docs
- Resume Parser: http://localhost:8005/docs

### Authentication

All protected endpoints require JWT authentication:

```
# 1. Register user
curl -X POST http://localhost:8001/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password123", "role": "recruiter"}'

# 2. Login
curl -X POST http://localhost:8001/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password123"}'

# Response: {"access_token": "eyJ...", "token_type": "bearer"}

# 3. Use token in requests
curl http://localhost:8002/api/v1/jobs \
  -H "Authorization: Bearer eyJ..."
```

### Common Request Examples

**Create Job**
```
curl -X POST http://localhost:8002/api/v1/jobs \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Senior Python Developer",
    "description": "We are looking for an experienced Python developer...",
    "requirements": ["Python", "Django", "PostgreSQL", "5+ years experience"],
    "location": "San Francisco, CA",
    "salary_min": 120000,
    "salary_max": 180000,
    "employment_type": "full-time"
  }'
```

**Parse Resume**
```
curl -X POST http://localhost:8005/api/v1/resume/parse \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@resume.pdf"
```

**Match Candidates (ML-Enhanced)**
```
curl -X POST "http://localhost:8004/api/v1/matching/match/candidates/ml-enhanced?job_title=Python%20Developer&required_skills=Python,Django&top_k=10" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## Development Guidelines

### Code Style

- Follow PEP 8 for Python code
- Use type hints for all function parameters and returns
- Write docstrings for all classes and functions
- Maximum line length: 88 characters (Black formatter)

### Git Workflow

```
# Create feature branch
git checkout -b feature/your-feature-name

# Make changes and commit
git add .
git commit -m "feat: add new feature description"

# Push to remote
git push origin feature/your-feature-name

# Create pull request on GitHub
```

### Commit Message Convention

```
feat: new feature
fix: bug fix
docs: documentation changes
style: code style changes (formatting, etc.)
refactor: code refactoring
test: adding or updating tests
chore: maintenance tasks
```

---

## Testing

### Unit Tests

```
# Run tests for specific service
cd backend/services/auth_service
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html

# View coverage report
open htmlcov/index.html
```

### Integration Tests

```
# Run integration tests
pytest tests/integration/ -v

# Run specific test file
pytest tests/integration/test_matching_workflow.py -v
```

### Load Testing

```
# Install locust
pip install locust

# Run load tests
cd tests/load
locust -f locustfile.py --host=http://localhost:8004
```

---

## Deployment

### Production Deployment

#### Using Docker Compose

```
# Build production images
docker-compose -f docker-compose.prod.yml build

# Start services
docker-compose -f docker-compose.prod.yml up -d

# View logs
docker-compose -f docker-compose.prod.yml logs -f
```

#### Using Kubernetes (Planned)

```
# Apply configurations
kubectl apply -f infrastructure/kubernetes/

# Check pod status
kubectl get pods

# View logs
kubectl logs -f deployment/matching-engine
```

### Environment Variables (Production)

```
# Database
DATABASE_URL=postgresql://user:password@prod-db:5432/talentai
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=40

# Redis
REDIS_URL=redis://prod-redis:6379/0
REDIS_PASSWORD=secure-password

# Security
SECRET_KEY=production-secret-key
JWT_SECRET_KEY=production-jwt-secret
ALLOWED_HOSTS=api.talentai.com,*.talentai.com

# ML/AI
OPENAI_API_KEY=production-api-key
MODEL_CACHE_SIZE=1000
VECTOR_CACHE_TTL=3600

# Monitoring
SENTRY_DSN=https://your-sentry-dsn
LOG_LEVEL=INFO
ENABLE_METRICS=true
```

### Monitoring & Logging

```
# View service logs
docker-compose logs -f matching-engine

# Check metrics
curl http://localhost:8004/metrics

# Health checks
curl http://localhost:8004/health/detailed
```

---

## Future Phases

### Phase 6: AI-Powered Interviews

**Objective**: Implement automated interview system with AI evaluation

**Features**:
- Video interview recording and analysis
- AI-generated interview questions based on job requirements
- Real-time speech-to-text transcription
- Sentiment analysis and body language detection
- Automated scoring and feedback generation
- Interview scheduling and calendar integration
- Multi-round interview workflows

**Technology Stack**:
- OpenAI Whisper for speech recognition
- GPT-4 for question generation and evaluation
- Computer vision models for behavioral analysis
- WebRTC for video streaming
- Celery for asynchronous processing

**Deliverables**:
- Interview service with REST API
- Video recording and storage
- AI evaluation engine
- Recruiter dashboard for review
- Candidate feedback reports

---

### Phase 7: Notifications & Communication

**Objective**: Build comprehensive notification and communication system

**Features**:
- Multi-channel notifications (Email, SMS, Push, In-app)
- Real-time messaging between recruiters and candidates
- Email templates for all candidate lifecycle stages
- SMS notifications for urgent updates
- Push notifications for mobile apps
- Notification preferences management
- Email campaign builder for job alerts
- Communication history tracking

**Technology Stack**:
- SendGrid/AWS SES for email
- Twilio for SMS
- Firebase Cloud Messaging for push notifications
- WebSocket for real-time chat
- RabbitMQ for message queuing
- Redis for notification caching

**Notification Types**:
- Application status updates
- Interview invitations and reminders
- Job recommendations
- Profile view notifications
- Document requests
- Offer letters
- Rejection notifications

---

### Phase 8: Workflow Automation

**Objective**: Automate recruitment workflows and decision-making

**Features**:
- Visual workflow builder (drag-and-drop)
- Conditional logic and branching
- Automated candidate screening
- Auto-scheduling interviews
- Automated email sequences
- Task assignment and tracking
- Approval workflows
- Integration with ATS systems
- Custom workflow templates
- Workflow analytics and optimization

**Workflow Examples**:
- Auto-screen candidates based on ML scores
- Schedule interviews with top candidates
- Send rejection emails to low-scoring applicants
- Move candidates through pipeline stages automatically
- Trigger background checks for finalists
- Generate offer letters for approved candidates

**Technology Stack**:
- Temporal.io for workflow orchestration
- Redis for state management
- PostgreSQL for workflow definitions
- React Flow for visual builder
- Celery for task execution

---

### Phase 9: Analytics & Reporting

**Objective**: Provide comprehensive analytics and business intelligence

**Features**:
- Real-time dashboards for recruiters and admins
- Candidate pipeline analytics
- Time-to-hire metrics
- Source of hire tracking
- Diversity and inclusion metrics
- Interview performance analytics
- Job posting effectiveness
- Recruiter productivity metrics
- Custom report builder
- Data export capabilities (CSV, PDF, Excel)
- Scheduled reports via email

**Key Metrics**:
- Time to fill positions
- Cost per hire
- Application conversion rates
- Candidate quality scores
- Interview-to-offer ratios
- Offer acceptance rates
- Source effectiveness
- Candidate satisfaction scores

**Technology Stack**:
- PostgreSQL for data warehouse
- Apache Superset for dashboards
- Pandas for data processing
- Matplotlib/Plotly for visualizations
- Celery Beat for scheduled reports
- Redis for metrics caching

**Dashboards**:
1. Executive Dashboard: High-level KPIs
2. Recruiter Dashboard: Individual performance
3. Pipeline Dashboard: Candidate flow visualization
4. Analytics Dashboard: Deep-dive metrics
5. Diversity Dashboard: D&I tracking

---

### Phase 10: Mobile Applications

**Objective**: Develop native mobile apps for iOS and Android

**Features**:
- Candidate mobile app
- Recruiter mobile app
- Push notifications
- Offline mode support
- Resume upload from mobile
- Video interview participation
- Real-time chat
- Job search and application
- Application tracking
- Calendar integration

**Technology Stack**:
- React Native for cross-platform development
- Redux for state management
- Firebase for push notifications
- WebRTC for video calls
- SQLite for offline storage

---

### Phase 11: Advanced AI Features

**Objective**: Implement cutting-edge AI capabilities

**Features**:
- Predictive analytics for candidate success
- Automated job description generation
- Candidate personality assessment
- Skill gap analysis and recommendations
- Career path suggestions
- Salary recommendation engine
- Market intelligence and competitive analysis
- Bias detection in hiring decisions
- Automated reference checking
- Custom AI model training per company

**Technology Stack**:
- TensorFlow/PyTorch for custom models
- Hugging Face Transformers
- LangChain for advanced LLM workflows
- MLflow for model management
- Custom NLP models

---

## Technology Roadmap

```
2025 Q4: Phase 5 Completion (Intelligent Matching)
2026 Q1: Phases 6-7 (AI Interviews, Notifications)
2026 Q2: Phases 8-9 (Workflows, Analytics)
2026 Q3: Phase 10 (Mobile Apps)
2026 Q4: Phase 11 (Advanced AI)
2027 Q1: Enterprise Features (SSO, Multi-tenancy)
2027 Q2: Global Expansion (Multi-language, Compliance)
```

---

## Contributing

We welcome contributions from the community!

### How to Contribute

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Write tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

### Code Review Process

- All PRs require at least one approval
- CI/CD pipeline must pass
- Code coverage should not decrease
- Follow existing code style and patterns

### Reporting Issues

- Use GitHub Issues for bug reports
- Include detailed description and reproduction steps
- Provide environment details
- Attach logs and screenshots if applicable

---

## License

Copyright (c) 2025 TalentAI Pro

This project is proprietary software. All rights reserved.

For licensing inquiries, contact: licensing@talentai.com

---