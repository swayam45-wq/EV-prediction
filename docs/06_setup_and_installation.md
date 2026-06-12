# 06. Setup and Installation

Follow these steps to run the backend locally.

## Prerequisites

*   Python 3.10 or higher installed on your system.
*   `git` installed.

## Step-by-Step Guide

### 1. Clone the Repository

```bash
git clone https://github.com/swayam45-wq/EV-prediction.git
cd EV-predict
```

### 2. Set Up a Virtual Environment

It's highly recommended to use a virtual environment to manage dependencies.

**On Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**On macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

Install the required Python packages from `requirements.txt`.

```bash
pip install -r requirements.txt
```
*(Note: This includes `pulp[cbc]`, which ensures the CBC solver is installed locally).*

### 4. Configure Environment Variables

Create a `.env` file based on the provided template.

```bash
cp .env.example .env
```
For Phase 1, the default values in `.env.example` are perfectly fine. No API keys are required yet.

### 5. Run the Server

Navigate to the `backend` directory and start the FastAPI server using Uvicorn.

```bash
cd backend
python -m uvicorn main:app --reload --port 8000
```

You should see output indicating the server has started:
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

### 6. Verify Installation

Open your web browser and navigate to:
**http://localhost:8000/docs**

You should see the interactive Swagger UI where you can test the `POST /api/recommend` endpoint directly from your browser.
