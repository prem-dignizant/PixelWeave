# PixelWeave Backend 🧶

PixelWeave is a Django-based backend for an AI-powered fashion design application. It allows users to generate wardrobe items and studio mockups using Generative AI (Google Gemini), manage credits via Stripe payments, and receive real-time notifications via WebSockets.

## 🚀 Features

- **AI Image Generation**: Generate garment images and professional model mockups.
- **Credit System**: Pay-per-use model with Stripe integration.
- **Real-time Notifications**: WebSocket integration for instant updates on generation status.
- **User Management**: Simple JWT-based authentication.

## 🛠️ Prerequisites

- **Python 3.10+**
- **Redis** (Required for WebSockets/Channels)
- **PostgreSQL** (Recommended) or SQLite (Local default)

## 📦 Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository_url>
    cd PixelWeave
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    python -m venv venv
    # Windows
    venv\Scripts\activate
    # Mac/Linux
    source venv/bin/activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Environment Configuration:**
    Create a `.env` file in the root directory:
    ```ini
    DEBUG=True
    ENVIRONMENT=local
    DATABASE_URL=sqlite:///db.sqlite3
    
    # Security
    SECRET_KEY=your_secret_key_here
    
    # AI Service
    GEMINI_API_KEY=your_google_gemini_key
    
    # Payments (Stripe)
    STRIPE_PUBLISHABLE_KEY=pk_test_...
    STRIPE_SECRET_KEY=sk_test_...
    STRIPE_WEBHOOK_SECRET=whsec_...
    CREDIT_PER_DOLLAR=10
    
    # Celery/Redis
    CELERY_BROKER_URL=redis://localhost:6379/0
    CELERY_RESULT_BACKEND=redis://localhost:6379/0
    ```

5.  **Apply Migrations:**
    ```bash
    python manage.py makemigrations
    python manage.py migrate
    ```

## 🏃‍♂️ Running the Server

1.  **Start Redis Server** (Required for WebSockets):
    Ensure your local Redis instance is running.

2.  **Run Django Development Server:**
    ```bash
    python manage.py runserver
    ```

    The API will be available at `http://localhost:8000/`.

## 📡 WebSockets

Connect to the notification stream to receive real-time updates:

- **URL:** `ws://localhost:8000/ws/notifications/?token=<ACCESS_TOKEN>`

## 📚 API Documentation

For detailed endpoint usage, please refer to the `api_documentation.md` file located in the `artifacts` folder or the project documentation.

**Key Endpoints:**
- `POST /user/register/` - Sign up
- `POST /user/login/` - Get JWT tokens
- `POST /pixel/wardrobe/` - Generate wardrobe item
- `POST /pixel/mockup/` - Generate studio mockup
- `POST /user/payment/create-checkout/` - Buy credits
