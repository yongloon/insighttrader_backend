# InsightTrader AI (MVP) - Backend

This is the backend service for the InsightTrader AI (MVP) platform. It is built using Python and FastAPI, providing APIs for market data, technical analysis, trade ideas, and alert management for BTC/USD.

## Table of Contents

- [Features (Backend Focus)](#features-backend-focus)
- [Technology Stack](#technology-stack)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Setup and Installation](#setup-and-installation)
- [Running the Backend Server](#running-the-backend-server)
- [API Endpoints](#api-endpoints)
- [Key Modules](#key-modules)
- [Configuration](#configuration)
- [Contributing](#contributing)
- [License](#license)

## Features (Backend Focus)

*   **Market Data Provision:**
    *   Serves simulated or live BTC/USD price data (via Binance public API).
    *   Maintains a short-term history of price points.
    *   Provides simulated sentiment data (mock X posts).
*   **Technical Analysis Engine:**
    *   Calculates Simple Moving Averages (SMA), Relative Strength Index (RSI), and Moving Average Convergence Divergence (MACD).
    *   Determines basic trend direction (e.g., Uptrend, Downtrend, Crossovers).
*   **Trade Idea Generation:**
    *   Generates simple, rule-based trade suggestions (BUY, SELL, HOLD) based on TA and sentiment.
*   **Alert Management:**
    *   Allows creation and deletion of price alerts.
    *   Checks and reports triggered alerts.

## Technology Stack

*   Python 3.10+
*   FastAPI
*   Uvicorn (ASGI server)
*   Pandas
*   Pandas TA (Technical Analysis Indicators)
*   HTTPX (Asynchronous HTTP client for live data)
*   Pydantic (Data validation and settings management)

## Project Structure

insighttrader_backend/
├── app/
│ ├── core/ # Configuration, etc. (minimal for MVP)
│ ├── models/ # Pydantic models for data validation and serialization
│ ├── services/ # Business logic:
│ │ ├── market_simulator.py (or live_data_fetcher.py) # Handles price data (sim/live) & sentiment
│ │ └── analysis_engine.py # Calculates indicators, trend, trade ideas
│ └── main.py # FastAPI application instance, routes, startup events
├── venv/ # Python virtual environment (ignored by Git)
├── requirements.txt # Python dependencies
├── .gitignore
└── README.md # This file


## Prerequisites

*   Python 3.10 or higher
*   pip (Python package installer)
*   Git (for version control)

## Setup and Installation

1.  **Clone the repository (if you haven't already) and navigate to this directory:**
    ```bash
    # Assuming you are in the root project directory
    cd insighttrader_backend
    ```
2.  **Create and activate a Python virtual environment:**
    ```bash
    python -m venv venv
    # Windows
    .\venv\Scripts\activate
    # macOS/Linux
    source venv/bin/activate
    ```
3.  **Install Python dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

## Running the Backend Server

1.  Ensure your virtual environment (`venv`) is active.
2.  Start the Uvicorn server from the `insighttrader_backend` root directory:
    ```bash
    uvicorn app.main:app --reload --port 8000
    ```
    *   `--reload`: Enables auto-reloading on code changes (for development).
    *   `--port 8000`: Specifies the port to run on.

    The API will be available at `http://localhost:8000`.
    Interactive API documentation (Swagger UI) can be accessed at `http://localhost:8000/docs`.
    Alternative documentation (ReDoc) at `http://localhost:8000/redoc`.

## API Endpoints

The following main API endpoints are exposed (base URL: `http://localhost:8000`):

*   `GET /api/market-data`: Fetches current market data (price, history, indicators, sentiment).
*   `GET /api/trade-idea`: Generates a trade idea.
*   `POST /api/alerts`: Creates a new price alert.
    *   Request Body: `{"price_level": float, "direction": "above" | "below"}`
*   `GET /api/check-alerts`: Checks for and returns triggered alerts.
*   `DELETE /api/alerts/{alert_id}`: Deletes an active alert.

Refer to `http://localhost:8000/docs` for detailed request/response schemas.

## Key Modules

*   **`app/main.py`**: Defines the FastAPI application, routes, and startup/shutdown events (like the background data fetcher).
*   **`app/services/market_simulator.py` (or `live_data_fetcher.py`)**: Responsible for providing BTC/USD price data (either by simulation or fetching from an external API like Binance) and mock sentiment.
*   **`app/services/analysis_engine.py`**: Contains the logic for calculating technical indicators, determining trends, and generating rule-based trade ideas.
*   **`app/models/pydantic_models.py`**: Defines the data structures (schemas) used for API requests, responses, and internal data handling, ensuring data validation.

## Configuration

*   **Live Data Fetching (Binance API):**
    *   Symbol: `BTCUSDT` (defined in `app/services/market_simulator.py`)
    *   Price Fetch Interval: Configurable in `app/services/market_simulator.py` (e.g., `PRICE_FETCH_INTERVAL_SECONDS`).
*   **Simulation Parameters:**
    *   Initial Price, History Length: Defined in `app/services/market_simulator.py` if using the simulator.

## Contributing

Contributions to the backend are welcome. Please refer to the main project README for general contribution guidelines. Focus on backend-specific improvements, API enhancements, or new data service integrations.

## License

This project is licensed under the MIT License. See the `LICENSE.md` file in the root project directory.