# Stockboy - LLM Trading Bot Benchmark Platform

A full-stack platform for benchmarking different LLM agents' ability to make trading decisions based on insider trading signals from OpenInsider.com.

![Dashboard Preview](docs/dashboard.png)

## 🚀 Features

- **Insider Trading Data**: Scrape and analyze SEC Form 4 filings from OpenInsider.com
- **LLM Agent Framework**: Test multiple LLM providers (OpenAI GPT-4, Anthropic Claude, Google Gemini)
- **Backtesting Engine**: Simulate trading strategies on historical data with performance metrics
- **Rich Visualizations**: Portfolio charts, trade tables, and key performance indicators
- **Cluster Detection**: Identify when multiple insiders are buying the same stock

## 📊 Architecture

```
Stockboy/
├── backend/               # Python Flask API
│   ├── app.py            # Main Flask application
│   ├── models.py         # SQLAlchemy database models
│   ├── services/         # Core services
│   │   ├── scraper.py    # OpenInsider.com scraper
│   │   ├── stock_data.py # Stock data + indicators
│   │   ├── llm_agents.py # LLM agent framework
│   │   └── backtester.py # Backtesting engine
│   └── tests/            # Pytest test suite
└── frontend/              # Next.js 14 + TypeScript
    └── src/
        ├── app/          # Next.js App Router pages
        ├── components/   # React components
        └── lib/          # Utilities + API client
```

## 🛠️ Quick Start

### Prerequisites

- Python 3.9+
- Node.js 18+
- npm or yarn

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file and add your API keys
cp .env.example .env

# Seed sample data (optional)
python seed_data.py

# Run the server
python app.py
```

The API will be available at http://localhost:5000

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

The UI will be available at http://localhost:3000

### 🐳 Docker Usage

To run the entire platform with Docker Compose:

1. Ensure your `.env` file is configured in `backend/` linked or variables passed.
2. Run:

```bash
docker-compose up --build
```

This starts both the frontend (optimized build) and backend services.


## 🔑 Configuration

Create a `.env` file in the `backend/` directory:

```env
# LLM API Keys (add the ones you want to use)
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key
GOOGLE_API_KEY=your_google_key

# Database
DATABASE_URL=sqlite:///stockboy.db

# Flask
FLASK_ENV=development
SECRET_KEY=your-secret-key
```

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Health check |
| GET | `/api/stats` | Platform statistics |
| GET | `/api/insider-trades` | List insider trades |
| POST | `/api/insider-trades/scrape` | Scrape new trades |
| GET | `/api/insider-trades/clusters` | Get cluster buys |
| GET | `/api/stock/:ticker` | Get stock data + indicators |
| GET/POST | `/api/agents` | CRUD for agents |
| GET/POST | `/api/backtests` | Run and view backtests |

## 🧪 Testing

### Backend Tests

```bash
cd backend
python -m pytest tests/ -v
```

### Run with Mock Agent

For testing without LLM API calls, create an agent with provider="mock".

## 📈 Metrics Calculated

- **Total Return**: Overall portfolio performance
- **Sharpe Ratio**: Risk-adjusted returns
- **Max Drawdown**: Largest peak-to-trough decline
- **Win Rate**: Percentage of profitable trades
- **Alpha**: Excess return vs S&P 500 benchmark

## ⚠️ Disclaimer

This platform is for **research and benchmarking purposes only**. It is not intended to provide financial advice. Past performance does not guarantee future results. Always do your own research before making investment decisions.

## 📝 License

MIT License - See LICENSE file for details.
