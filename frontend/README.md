# JalSense React Frontend

Production-grade decision-support web interface for the **JalSense** village water intelligence system.

## Technology Stack
- **Framework:** React 19 + TypeScript + Vite
- **Styling:** Tailwind CSS v4 (Custom High-Contrast Light Theme)
- **Data Visualizations:** Recharts (composed charts, linear projections, and SVG gauges)
- **Icons:** Lucide React
- **API Communication:** Centralized typed client (`src/services/api.ts`) connecting to FastAPI

## Local Development
```bash
# Install dependencies
npm install

# Run local development server (port 5173)
npm run dev

# Run TypeScript checks and production build
npm run build
```

## Production Deployment
Containerized via multi-stage Docker build with Nginx (`Dockerfile` & `nginx.conf`).
