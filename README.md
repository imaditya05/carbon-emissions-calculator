# 🌍 Carbon Emission Calculator

A full-stack application that calculates carbon emissions for cargo transport between locations, identifies optimal routes (shortest and most efficient), and visualizes them on an interactive map.

![Carbon Emission Calculator](https://img.shields.io/badge/Status-Live-brightgreen)
![Python](https://img.shields.io/badge/Python-3.12-blue)
![React](https://img.shields.io/badge/React-18-61dafb)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688)

## 🚀 Live Demo

- **Frontend**: [https://carbon-frontend-1045695454259.us-central1.run.app](https://carbon-frontend-1045695454259.us-central1.run.app)
- **Backend API**: [https://carbon-backend-qkbbr3ntyq-uc.a.run.app](https://carbon-backend-qkbbr3ntyq-uc.a.run.app)
- **API Documentation**: [https://carbon-backend-qkbbr3ntyq-uc.a.run.app/docs](https://carbon-backend-qkbbr3ntyq-uc.a.run.app/docs)

---

## ✨ Features

### 1. Carbon Emission Calculation
- Calculate CO₂ emissions based on origin, destination, cargo weight, and transport mode
- Support for **Land**, **Sea**, and **Air** transport
- Uses industry-standard emission factors

### 2. Multi-Modal Route Computation
- **Shortest Route**: Distance-optimized path
- **Eco-Efficient Route**: CO₂-optimized path
- **Multi-Modal Support**: Road → Airport → Air → Airport → Road routes
- Automatic detection of nearby airports and seaports
- Viability checks for different transport modes

### 3. Interactive Map Visualization
- Mapbox GL JS integration
- Distinct colors for different transport modes:
  - 🟠 **Orange** - Road/Land
  - 🟣 **Purple** - Air (dashed line)
  - 🔵 **Cyan** - Sea (dashed line)
- Markers for origin, destination, airports, and ports
- Toggle between shortest and eco-efficient routes

### 4. User Authentication
- JWT-based authentication with OAuth2
- Secure password hashing with Argon2
- Token refresh and session management

### 5. Search History
- Save and retrieve past searches
- Filter by transport mode, location, date
- Pagination support
- Delete individual or all searches

---

## 📊 CO₂ Emission Factors

The application uses the following emission factors (kg CO₂ per tonne-km):

| Transport Mode | Emission Factor | Source |
|----------------|-----------------|--------|
| **Road (Truck)** | 0.062 kg CO₂/t-km | DEFRA 2023 - HGV average |
| **Sea (Container Ship)** | 0.016 kg CO₂/t-km | IMO 2023 - Container ship average |
| **Air (Cargo Plane)** | 0.602 kg CO₂/t-km | ICAO 2023 - Freight aircraft |

### Emission Calculation Formula

```
CO₂ Emissions (kg) = Distance (km) × Weight (tonnes) × Emission Factor
```

**Example**: Shipping 1000 kg cargo over 500 km by truck:
```
CO₂ = 500 km × 1.0 tonnes × 0.062 = 31 kg CO₂
```

### Multi-Modal Calculation

For multi-modal routes (e.g., Road → Air → Road), emissions are calculated separately for each segment and summed:

```
Total CO₂ = Σ (Segment Distance × Weight × Mode Emission Factor)
```

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend (React)                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐ │
│  │ Calculator  │  │   History   │  │      Map (Mapbox)       │ │
│  │    Form     │  │    Page     │  │   Route Visualization   │ │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘ │
└────────────────────────────┬────────────────────────────────────┘
                             │ REST API
┌────────────────────────────▼────────────────────────────────────┐
│                       Backend (FastAPI)                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐ │
│  │    Auth     │  │   Routes    │  │       Emissions         │ │
│  │   Service   │  │   Service   │  │        Service          │ │
│  └─────────────┘  └──────┬──────┘  └─────────────────────────┘ │
│                          │                                      │
│  ┌───────────────────────▼──────────────────────────────────┐  │
│  │                  Mapbox APIs                              │  │
│  │  • Directions API (road routes)                          │  │
│  │  • Geocoding API (airports/ports lookup)                 │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                     MongoDB Atlas                               │
│  ┌─────────────┐  ┌─────────────────────────────────────────┐  │
│  │    Users    │  │              Searches                    │  │
│  │ Collection  │  │             Collection                   │  │
│  └─────────────┘  └─────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🛠️ Tech Stack

### Backend
- **Python 3.12** - Programming language
- **FastAPI** - Web framework
- **MongoDB** - Database (with `pymongo` async driver)
- **PyJWT** - JWT authentication
- **pwdlib** - Password hashing (Argon2)
- **httpx** - HTTP client for external APIs
- **Pydantic** - Data validation

### Frontend
- **React 18** - UI library
- **TypeScript** - Type safety
- **Vite** - Build tool
- **Tailwind CSS** - Styling
- **Mapbox GL JS** - Map visualization
- **Zustand** - State management
- **Axios** - HTTP client

### Infrastructure
- **Google Cloud Run** - Serverless deployment
- **MongoDB Atlas** - Managed database
- **Docker** - Containerization

---

## 📁 Project Structure

```
carbon-emission-calculator/
├── backend/
│   ├── app/
│   │   ├── api/routes/          # API endpoints
│   │   │   ├── auth.py          # Authentication endpoints
│   │   │   ├── emissions.py     # Emission calculation endpoints
│   │   │   ├── routes.py        # Route computation endpoints
│   │   │   ├── searches.py      # Search history endpoints
│   │   │   └── health.py        # Health check endpoint
│   │   ├── core/                # Core configuration
│   │   │   ├── config.py        # Application settings
│   │   │   ├── security.py      # Password & JWT utilities
│   │   │   └── dependencies.py  # FastAPI dependencies
│   │   ├── db/                  # Database layer
│   │   │   ├── mongodb.py       # MongoDB client
│   │   │   └── init_db.py       # Database initialization
│   │   ├── models/              # Pydantic models
│   │   │   ├── user.py          # User models
│   │   │   ├── emission.py      # Emission models
│   │   │   ├── route.py         # Route models
│   │   │   └── search.py        # Search models
│   │   ├── services/            # Business logic
│   │   │   ├── auth_service.py      # Authentication logic
│   │   │   ├── emission_service.py  # Emission calculations
│   │   │   ├── route_service.py     # Route computation (937 lines)
│   │   │   └── search_service.py    # Search history management
│   │   └── main.py              # Application entry point
│   ├── Dockerfile               # Backend container
│   ├── requirements.txt         # Python dependencies
│   └── env.example.txt          # Environment variables template
│
├── frontend/
│   ├── src/
│   │   ├── components/          # React components
│   │   │   ├── calculator/      # Calculator form components
│   │   │   ├── layout/          # Layout components
│   │   │   ├── map/             # Map visualization
│   │   │   └── ui/              # Reusable UI components
│   │   ├── pages/               # Page components
│   │   ├── stores/              # Zustand stores
│   │   ├── lib/                 # Utilities (API, Mapbox)
│   │   └── types/               # TypeScript types
│   ├── Dockerfile               # Frontend container
│   ├── nginx.conf               # Nginx configuration
│   └── package.json             # Node dependencies
│
└── README.md                    # This file
```

---

## 🚀 Local Development Setup

### Prerequisites
- Python 3.12+
- Node.js 20+
- MongoDB Atlas account (or local MongoDB)
- Mapbox account (for access token)

### Backend Setup

```bash
# Navigate to backend
cd backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp env.example.txt .env
# Edit .env with your values

# Run the server
uvicorn app.main:app --reload --port 8000
```

### Frontend Setup

```bash
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Create .env file
cp env.example.txt .env
# Edit .env with your Mapbox token

# Run the development server
npm run dev
```

### Environment Variables

**Backend (.env)**:
```env
MONGODB_URL=mongodb+srv://user:pass@cluster.mongodb.net/
MONGODB_DATABASE=carbon_emission_db
JWT_SECRET_KEY=your-super-secret-key-change-in-production
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=10080
MAPBOX_ACCESS_TOKEN=pk.your_mapbox_token
ENVIRONMENT=development
```

**Frontend (.env)**:
```env
VITE_MAPBOX_ACCESS_TOKEN=pk.your_mapbox_token
VITE_API_URL=http://localhost:8000/api/v1
```

---

## ☁️ Cloud Run Deployment

### Deploy Backend

```bash
cd backend

gcloud run deploy carbon-backend \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --timeout=300 \
  --set-env-vars "MONGODB_URL=...,MONGODB_DATABASE=...,JWT_SECRET_KEY=...,MAPBOX_ACCESS_TOKEN=...,ENVIRONMENT=production"
```

### Deploy Frontend

```bash
cd frontend

gcloud run deploy carbon-frontend \
  --source . \
  --region us-central1 \
  --allow-unauthenticated
```

---

## 📡 API Endpoints

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/register` | Register new user |
| POST | `/api/v1/auth/token` | Login (OAuth2 password flow) |
| GET | `/api/v1/auth/me` | Get current user |

### Routes & Emissions
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/routes/compute` | Compute routes (no save) |
| POST | `/api/v1/searches/` | Compute routes and save |
| GET | `/api/v1/emissions/factors` | Get emission factors |
| POST | `/api/v1/emissions/calculate` | Calculate emissions |

### Search History
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/searches/` | List searches (with filters) |
| GET | `/api/v1/searches/{id}` | Get specific search |
| DELETE | `/api/v1/searches/{id}` | Delete search |
| DELETE | `/api/v1/searches/` | Delete all searches |

### Health
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/health` | Health check |
| GET | `/api/v1/health/detailed` | Detailed health check |

---

## 🔒 Security

- **Password Hashing**: Argon2 (via pwdlib)
- **Authentication**: JWT with OAuth2 Password flow
- **Token Expiry**: 7 days (configurable)
- **CORS**: Configured for specific origins
- **Input Validation**: Pydantic models with strict typing

---

## 📝 License

MIT License - feel free to use this project for learning or commercial purposes.

---

## 🙏 Acknowledgments

- [Mapbox](https://www.mapbox.com/) - Maps and routing APIs
- [FastAPI](https://fastapi.tiangolo.com/) - Modern Python web framework
- [DEFRA](https://www.gov.uk/government/organisations/department-for-environment-food-rural-affairs) - Emission factor data
- [IMO](https://www.imo.org/) - Maritime emission standards
- [ICAO](https://www.icao.int/) - Aviation emission standards
