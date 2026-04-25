# Crowdfund Backend

A production-ready REST API backend for a crowdfunding platform, built with Django 5 and Django REST Framework. It supports user authentication with email activation, project management, donations, ratings, comments, and media uploads — all deployed via Docker to AWS EC2.

---

## Table of Contents

- [Tech Stack](#tech-stack)
- [Architecture Overview](#architecture-overview)
- [Features](#features)
- [API Reference](#api-reference)
- [Data Models](#data-models)
- [Getting Started](#getting-started)
- [Environment Variables](#environment-variables)
- [Docker](#docker)
- [CI/CD](#cicd)
- [Project Structure](#project-structure)

---

## Tech Stack

| Layer            | Technology                                                 |
| ---------------- | ---------------------------------------------------------- |
| Framework        | Django 5.2 + Django REST Framework                         |
| Auth             | JWT via `djangorestframework-simplejwt` (httpOnly cookies) |
| Database         | PostgreSQL (Supabase-hosted)                               |
| Media Storage    | Cloudinary                                                 |
| Email            | Brevo (SMTP)                                               |
| Containerization | Docker                                                     |
| CI/CD            | GitHub Actions → AWS EC2                                   |

---

## Architecture Overview

The project follows a modular Django app structure. Each domain has its own app under `apps/`:

```
config/          → Django settings & root URL router
apps/
  authentication/  → Custom User model, JWT cookie auth, email activation
  profiles/        → User profile management & public profiles
  projects/        → Projects, categories, tags, images, ratings, comments, reports
  donations/       → Donation creation and retrieval
  core/            → Reserved for shared utilities (currently a placeholder)
```

Authentication uses a **custom `CookieJWTAuthentication`** class that reads JWT tokens from httpOnly cookies instead of the `Authorization` header, improving XSS resistance. CSRF protection is also enabled for cookie-based flows.

---

## Features

### Authentication

- User registration with **email activation** (signed token, 24-hour expiry)
- **Resend activation** email with a 2-minute cooldown to prevent abuse
- Login/logout with **httpOnly JWT cookies** (access + refresh tokens)
- Silent **token refresh** via cookie
- Email enumeration protection on sensitive endpoints

### User Profiles

- View and update your own profile (name, phone, birthdate, country, Facebook URL, avatar)
- **Delete account** (requires password confirmation; blocked if active projects or donations exist)
- Public profile view for any user by ID
- View any user's public (pending) projects

### Projects

- Full CRUD — only the project owner can edit or cancel
- **Cancel protection**: cannot cancel a project that has received more than 25% of its funding target
- Projects move through statuses: `pending` → `finished` / `canceled` / `banned`
- Upload up to **4 images** per project
- Attach up to **10 tags** per project (auto-created if new)
- Assign to a **category**
- Mark projects as **featured**
- **Star ratings** (1–5) — one per user, updateable
- **Report/flag** a project (toggle — report again to unflag)
- **Similar projects** by shared tags
- **Homepage feed**: latest, featured, and top-rated projects + all categories
- **Search** by title, details, category, tags, or creator name; filter by category

### Comments

- Post top-level comments on any project
- **Threaded replies** (one level deep — replies cannot be nested further)
- Edit and delete your own comments
- **Report/flag** a comment (toggle)

### Donations

- Donate to any `pending` project
- Automatically caps donations at the remaining target balance
- Project status auto-transitions to `finished` when the target is reached
- View your own donation history, or donations per project

---

## API Reference

All endpoints are prefixed with `/api/`.

### Auth — `/api/auth/`

| Method | Endpoint                  | Auth     | Description                                       |
| ------ | ------------------------- | -------- | ------------------------------------------------- |
| POST   | `auth/register/`          | Public   | Register a new user                               |
| GET    | `auth/activate/<token>/`  | Public   | Activate account via email token                  |
| POST   | `auth/resend-activation/` | Public   | Resend activation email                           |
| POST   | `auth/login/`             | Public   | Login, sets JWT cookies                           |
| POST   | `auth/logout/`            | Public   | Logout, clears cookies & blacklists refresh token |
| GET    | `auth/me/`                | Required | Get current user's basic info                     |
| POST   | `auth/token/refresh/`     | Public   | Refresh access token from cookie                  |

### Profiles — `/api/users/`

| Method | Endpoint               | Auth     | Description                  |
| ------ | ---------------------- | -------- | ---------------------------- |
| GET    | `users/me/`            | Required | Get own profile              |
| PATCH  | `users/me/`            | Required | Update own profile           |
| DELETE | `users/me/`            | Required | Delete own account           |
| GET    | `users/<id>/`          | Public   | Get public profile           |
| GET    | `users/me/projects/`   | Required | Get own projects             |
| GET    | `users/me/donations/`  | Required | Get own donations            |
| GET    | `users/<id>/projects/` | Public   | Get a user's public projects |

### Projects — `/api/projects/`

| Method | Endpoint                         | Auth     | Description                                             |
| ------ | -------------------------------- | -------- | ------------------------------------------------------- |
| GET    | `projects/`                      | Public   | List all projects                                       |
| POST   | `projects/`                      | Required | Create a project                                        |
| GET    | `projects/<id>/`                 | Public   | Get a project                                           |
| PUT    | `projects/<id>/`                 | Owner    | Replace a project                                       |
| PATCH  | `projects/<id>/`                 | Owner    | Partially update a project                              |
| DELETE | `projects/<id>/`                 | Owner    | Cancel a project                                        |
| GET    | `projects/home/`                 | Public   | Homepage feed (latest, featured, top-rated, categories) |
| GET    | `projects/search/`               | Public   | Search & filter projects                                |
| GET    | `projects/<id>/similar/`         | Public   | Get similar projects by tags                            |
| POST   | `projects/<id>/rate/`            | Required | Rate a project (or update rating)                       |
| POST   | `projects/<id>/report/`          | Required | Flag/unflag a project                                   |
| GET    | `projects/categories/`           | Public   | List categories                                         |
| POST   | `projects/categories/`           | Required | Create a category                                       |
| GET    | `projects/tags/`                 | Public   | List tags                                               |
| POST   | `projects/tags/`                 | Required | Create a tag                                            |
| GET    | `projects/<id>/images/`          | Public   | List project images                                     |
| POST   | `projects/<id>/images/`          | Required | Add images to project                                   |
| DELETE | `projects/<id>/images/<img_id>/` | Required | Delete a specific image                                 |
| GET    | `projects/<id>/comments/`        | Public   | List project comments                                   |
| POST   | `projects/<id>/comments/`        | Required | Post a comment                                          |
| PATCH  | `comments/<id>/`                 | Owner    | Edit own comment                                        |
| DELETE | `comments/<id>/`                 | Owner    | Delete own comment                                      |
| POST   | `comments/<id>/report/`          | Required | Flag/unflag a comment                                   |

### Donations — `/api/donations/`

| Method | Endpoint                  | Auth     | Description                        |
| ------ | ------------------------- | -------- | ---------------------------------- |
| GET    | `donations/`              | Required | List current user's donations      |
| GET    | `donations/<project_id>/` | Required | Get user's donations for a project |
| POST   | `donations/<project_id>/` | Required | Donate to a project                |

---

## Data Models

```
User
├── email (unique login field)
├── first_name, last_name
├── mobile_number (Egyptian format: 01x-xxxxxxxx)
├── profile_pic (Cloudinary)
├── birthdate, country, fb_profile
├── role (admin / user)
└── is_activated, joined_at

Project
├── title, details, start_date, end_date
├── target (float), current_money (float)
├── status (pending / finished / canceled / banned)
├── is_featured (bool)
├── category → Category
├── tags → [Tag] (M2M, up to 10)
├── images → [Image] (up to 4, stored on Cloudinary)
└── user → User

Donation
├── amount
├── project → Project (PROTECT)
└── user → User (PROTECT)

Comment
├── content
├── parent → Comment (nullable, for replies — 1 level only)
├── project → Project
└── user → User

ProjectRating     → (project, user) unique; stars 1–5
ProjectReport     → (project, user) unique; toggle flag
CommentReport     → (comment, user) unique; toggle flag
Category          → name
Tag               → name (unique)
```

---

## Getting Started

### Prerequisites

- Python 3.12+
- PostgreSQL (or a Supabase connection string)
- A Cloudinary account
- A Brevo (or compatible SMTP) account for email

### Local Setup

```bash
# 1. Clone the repository
git clone https://github.com/mohamedabdelhaq-123/crowdfund-backend.git
cd crowdfund-backend

# 2. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment variables
cp .env.example .env
# Edit .env with your credentials (see Environment Variables below)

# 5. Apply migrations
python manage.py migrate

# 6. (Optional) Seed the database with sample data
python seed_data.py

# 7. Create a superuser for Django Admin
python manage.py createsuperuser

# 8. Run the development server
python manage.py runserver
```

The API will be available at `http://localhost:8000`.

> **Note:** In `DEBUG=True` mode, activation tokens are also printed to the terminal, so you can activate accounts without needing a real email setup.

---

## Environment Variables

Copy `.env.example` to `.env` and fill in the values:

```env
# Django
SECRET_KEY=your-very-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0
FRONTEND_URL=http://localhost:5173        # Used for CORS and activation email links

# PostgreSQL / Supabase
DB_HOST=xxxx.pooler.supabase.com
DB_NAME=postgres
DB_USER=postgres.xxxxxxxxx
DB_PASSWORD=your-database-password
DB_PORT=6543

# Email (Brevo SMTP)
EMAIL_HOST=smtp-relay.brevo.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-brevo-username
EMAIL_HOST_PASSWORD=your-brevo-password
EMAIL_USE_TLS=True
DEFAULT_FROM_EMAIL=your@email.com

# Cloudinary
CLOUDINARY_CLOUD_NAME=your-cloud-name
CLOUDINARY_API_KEY=your-api-key
CLOUDINARY_API_SECRET=your-api-secret
```

---

## Docker

The project includes a `Dockerfile` for containerized deployment. It runs migrations automatically on startup.

```bash
# Build the image
docker build -t crowdfund-backend .

# Run the container
docker run -p 8000:8000 crowdfund-backend
```

For multi-service orchestration (backend + frontend), keep `docker-compose.yml` in a separate infra/deployment repo (or directly on the server), since backend and frontend live in separate repositories.

**Note:** Both `crowdfund-backend` and `crowdfund-frontend` repositories must exist in the same parent directory as the `docker-compose.yml` file for the build contexts (`./crowdfund-backend` and `./crowdfund-frontend`) to work correctly.

Example shared `docker-compose.yml`:

```yaml
services:
  backend:
    build:
      context: ./crowdfund-backend
    container_name: crowdfund-backend
    env_file:
      - ./crowdfund-backend/.env
    ports:
      - "8000:8000"
    volumes:
      - ./crowdfund-backend:/app

  frontend:
    build:
      context: ./crowdfund-frontend
    container_name: crowdfund-frontend
    depends_on:
      - backend
    ports:
      - "5173:5173"
    volumes:
      - ./crowdfund-frontend:/app
      - frontend_node_modules:/app/node_modules

volumes:
  frontend_node_modules:
```

Run from the directory that contains both repos and `docker-compose.yml`:

```bash
docker compose up -d --build
```

---

## CI/CD

Deployments to AWS EC2 are automated via **GitHub Actions** (`.github/workflows/deploy-ec2.yml`).

**Trigger:** Any push to the `dev` branch, or a manual `workflow_dispatch`.

**Pipeline steps:**

1. SSH into the EC2 instance using stored secrets
2. Pull the latest code from `origin/dev`
3. Rebuild and restart only the `backend` Docker service (`docker compose up -d --build --no-deps backend`)
4. Prune unused Docker images, builder cache, and volumes to save disk space

A file lock (`/tmp/crowdfund-deploy.lock`) serializes concurrent backend/frontend deployments on the same host.

**Required GitHub Secrets:**

| Secret             | Description                                     |
| ------------------ | ----------------------------------------------- |
| `EC2_HOST`         | Public IP or domain of the EC2 instance         |
| `EC2_USER`         | SSH username (e.g., `ubuntu`)                   |
| `EC2_SSH_KEY`      | Private SSH key for authentication              |
| `EC2_PROJECT_PATH` | Absolute path to the project root on the server |

---

## Project Structure

```
crowdfund-backend/
├── config/
│   ├── settings.py          # All Django settings
│   └── urls.py              # Root URL configuration
├── apps/
│   ├── authentication/      # Custom User model, JWT cookie auth, email activation
│   ├── profiles/            # Profile view/update, public profiles, account deletion
│   ├── projects/            # Projects, categories, tags, images, ratings, comments, reports
│   ├── donations/           # Donation logic with target enforcement
│   └── core/                # Placeholder for shared utilities
├── Dockerfile
├── requirements.txt
├── seed_data.py
└── .env.example
```

---

## Notes & Assumptions

- The `seed_data.py` file is a binary/compiled file and its exact contents were not available for analysis. It is assumed to populate the database with sample projects, users, and categories for development purposes.
- The `core` app is currently empty and appears to be reserved for future shared logic or utilities.
- The production domain is `crowdfund.duckdns.org`, as inferred from CORS and CSRF settings.
- JWT cookies are configured with `SameSite=None; Secure=True` in production and `SameSite=Lax` in development, compatible with a separate React frontend origin.

## Team Members

Rana Mohamed Abd Elhalim
Mohamed Khaled Hussein
Mohamed Sameh Mostafa Mohamed Elkholy
Mohamed Abdelhaq Mohamed
Andrew Emad Morris Philps
