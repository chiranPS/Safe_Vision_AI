# AI-Powered Police-Compliant Analysis & Management System

This project is a comprehensive system designed for Police Complaint Management. It integrates modern web technologies and artificial intelligence to streamline and automate complaint processing.

The system consists of four main components:
1. **Frontend**: A React single-page application built with Vite.
2. **Backend**: A Next.js application providing the REST API and handling database operations via Prisma ORM.
3. **AI Service**: A Python-based FastAPI service responsible for OCR (Optical Character Recognition) and machine learning predictive pipelines.
4. **SafeVisionAI OCR**: An advanced standalone Dockerized OCR service with a Django backend, React frontend, Celery, and MongoDB.

---

## 🛠️ Prerequisites

Before you begin, ensure you have the following installed on your system:
- **Node.js** (v18 or higher) - Required for Frontend and Backend.
- **Python** (v3.10 or higher) - Required for the AI Service.
- **PostgreSQL** (or your preferred database) - Make sure the database service is running locally or accessible remotely.
- **Docker & Docker Compose** - Required for running the SafeVisionAI OCR service.

> [!WARNING]
> **Port Conflicts**: By default, there are port overlaps between the services:
> - **Port 3000** is used by both the Next.js **Backend** and the **SafeVisionAI OCR Frontend**.
> - **Port 8000** is used by both the **AI Service** and the **SafeVisionAI OCR Backend**.
> Make sure to adjust ports in your commands or `.env` files if you intend to run all services simultaneously.

---

## 🚀 How to Run the Project Locally

You will need multiple terminals to run all parts of the application simultaneously.

### 1. Backend (Next.js & Prisma)
The backend manages data persistence and provides APIs for the frontend.

1. Open a terminal and navigate to the `backend` directory:
   ```bash
   cd backend
   ```
2. Install the Node.js dependencies:
   ```bash
   npm install
   ```
3. Set up your Environment Variables:
   - Ensure a `.env` file exists in the `backend` directory.
   - It must contain your database connection string, for example: `DATABASE_URL="postgresql://user:password@localhost:5434/complaint_system"`
4. Initialize the Database:
   ```bash
   npx prisma generate
   npx prisma db push
   # Optional: seed the database if you have seed data configured
   # npm run prisma db seed
   ```
5. Start the backend server:
   ```bash
   npm run dev
   # To avoid port 3000 conflict, you can run: npm run dev -- -p 3001
   ```

---

### 2. Frontend (React & Vite)
The frontend provides the user interface for the main application.

1. Open a new terminal and ensure you are in the **project root directory** (`Police-Compliant MS`).
2. Install the Node.js dependencies:
   ```bash
   npm install
   ```
3. Start the frontend development server:
   ```bash
   npm run dev
   ```
   *The frontend application will be available at `http://localhost:5173`.*

---

### 3. AI Service (Python FastAPI)
The AI service handles document processing, predictive models, and simple OCR.

1. Open a new terminal and navigate to the `ai-service` directory:
   ```bash
   cd ai-service
   ```
2. Create and activate a Python virtual environment:
   ```bash
   # On Windows:
   python -m venv venv
   .\venv\Scripts\activate

   # On macOS/Linux:
   python3 -m venv venv
   source venv/bin/activate
   ```
3. Install the required Python packages:
   ```bash
   pip install -r requirements.txt
   ```
4. Start the FastAPI server:
   ```bash
   uvicorn app.main:app --reload --port 8000
   # To avoid port 8000 conflict, you can change the port: uvicorn app.main:app --reload --port 8001
   ```
   *The interactive API documentation will be available at `http://localhost:8000/docs`.*

---

### 4. SafeVisionAI OCR (Dockerized)
This is an advanced OCR module powered by Docker, comprising a Django backend, React frontend, and Redis/Celery queue.

1. Open a new terminal and navigate to the `SafeVisionAI_OCR` directory:
   ```bash
   cd SafeVisionAI_OCR
   ```
2. Start the services using Docker Compose:
   ```bash
   docker-compose up --build
   ```
   *This will spin up:*
   - *MongoDB and Redis*
   - *Django Backend (`http://localhost:8000`)*
   - *Celery Worker*
   - *React Frontend (`http://localhost:3000`)*

---

## 🏗️ Building for Production

If you need to build the project for a production deployment:

- **Frontend**: Run `npm run build` in the root directory. The compiled static assets will be output to the `dist` folder.
- **Backend**: Run `npm run build` in the `backend` directory, followed by `npm start` to run the production server.
- **AI Service**: Use a production-grade ASGI server like Gunicorn with Uvicorn workers.
- **SafeVisionAI OCR**: Deploy the Docker containers using `docker-compose -f docker-compose.prod.yml up -d` (if a production compose file is created) and configure proper proxying (e.g., NGINX).

---

## ❓ Troubleshooting Common Issues

- **Port Conflicts**: As mentioned above, make sure Next.js and SafeVisionAI frontend aren't fighting for port `3000`, and FastAPI and SafeVisionAI backend aren't fighting for port `8000`. Use `-p <port>` flags to reassign ports.
- **"Module not found" Errors**: Ensure you have successfully run `npm install` in the respective JavaScript directories, and `pip install -r requirements.txt` inside the activated virtual environment for the Python service.
- **Database Connection Errors**: Verify that your PostgreSQL database is actually running and that the credentials in `backend/.env` are perfectly matched to your database configuration.
- **Docker Issues**: Make sure Docker Desktop daemon is running if you are using Windows/Mac, before running `docker-compose`.
