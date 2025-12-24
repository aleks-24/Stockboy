const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000/api';

export interface InsiderTrade {
    id: number;
    filing_date: string;
    trade_date: string;
    ticker: string;
    company_name: string;
    insider_name: string;
    insider_title: string;
    trade_type: string;
    price: number;
    quantity: number;
    value: number;
    delta_owned: number;
    industry: string;
}

export interface Agent {
    id: number;
    name: string;
    provider: string;
    model: string;
    temperature: number;
    risk_tolerance: string;
    max_position_size: number;
    stop_loss_pct: number;
    take_profit_pct: number;
    system_prompt?: string;
    created_at: string;
}

export interface Backtest {
    id: number;
    agent_id: number;
    agent_name: string;
    start_date: string;
    end_date: string;
    initial_capital: number;
    final_value: number;
    total_return: number;
    annualized_return: number;
    sharpe_ratio: number;
    max_drawdown: number;
    win_rate: number;
    total_trades: number;
    benchmark_return: number;
    alpha: number;
    status: string;
    portfolio_history: { date: string; value: number }[];
    created_at: string;
}

export interface Trade {
    id: number;
    ticker: string;
    trade_type: string;
    entry_date: string;
    entry_price: number;
    exit_date?: string;
    exit_price?: number;
    quantity: number;
    pnl?: number;
    pnl_pct?: number;
    reason?: string;
}

export interface Stats {
    total_insider_trades: number;
    total_agents: number;
    total_backtests: number;
    completed_backtests: number;
    recent_insider_buys: number;
    recent_insider_sales: number;
    best_backtest: Backtest | null;
}

async function fetchApi<T>(endpoint: string, options?: RequestInit): Promise<T> {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        ...options,
        headers: {
            'Content-Type': 'application/json',
            ...options?.headers,
        },
    });

    if (!response.ok) {
        throw new Error(`API Error: ${response.statusText}`);
    }

    return response.json();
}

// Stats
export async function getStats(): Promise<Stats> {
    return fetchApi<Stats>('/stats');
}

// Insider Trades
export async function getInsiderTrades(params?: {
    ticker?: string;
    trade_type?: string;
    start_date?: string;
    end_date?: string;
    limit?: number;
    offset?: number;
}): Promise<{ trades: InsiderTrade[]; total: number }> {
    const searchParams = new URLSearchParams();
    if (params) {
        Object.entries(params).forEach(([key, value]) => {
            if (value !== undefined) searchParams.set(key, String(value));
        });
    }
    return fetchApi(`/insider-trades?${searchParams}`);
}

export async function scrapeInsiderTrades(data: {
    start_date?: string;
    end_date?: string;
    max_pages?: number;
}): Promise<{ status: string; scraped: number; saved: number }> {
    return fetchApi('/insider-trades/scrape', {
        method: 'POST',
        body: JSON.stringify(data),
    });
}

export async function getClusterBuys(params?: {
    days?: number;
    min_insiders?: number;
}): Promise<{ clusters: any[] }> {
    const searchParams = new URLSearchParams();
    if (params) {
        Object.entries(params).forEach(([key, value]) => {
            if (value !== undefined) searchParams.set(key, String(value));
        });
    }
    return fetchApi(`/insider-trades/clusters?${searchParams}`);
}

// Stock Data
export async function getStockData(ticker: string, params?: {
    start_date?: string;
    end_date?: string;
}): Promise<any> {
    const searchParams = new URLSearchParams();
    if (params) {
        Object.entries(params).forEach(([key, value]) => {
            if (value !== undefined) searchParams.set(key, String(value));
        });
    }
    return fetchApi(`/stock/${ticker}?${searchParams}`);
}

// Agents
export async function getAgents(): Promise<{ agents: Agent[] }> {
    return fetchApi('/agents');
}

export async function getAgent(id: number): Promise<Agent> {
    return fetchApi(`/agents/${id}`);
}

export async function createAgent(data: Omit<Agent, 'id' | 'created_at'>): Promise<Agent> {
    return fetchApi('/agents', {
        method: 'POST',
        body: JSON.stringify(data),
    });
}

export async function updateAgent(id: number, data: Partial<Agent>): Promise<Agent> {
    return fetchApi(`/agents/${id}`, {
        method: 'PUT',
        body: JSON.stringify(data),
    });
}

export async function deleteAgent(id: number): Promise<void> {
    return fetchApi(`/agents/${id}`, { method: 'DELETE' });
}

// Backtests
export async function getBacktests(params?: {
    agent_id?: number;
    status?: string;
    limit?: number;
}): Promise<{ backtests: Backtest[] }> {
    const searchParams = new URLSearchParams();
    if (params) {
        Object.entries(params).forEach(([key, value]) => {
            if (value !== undefined) searchParams.set(key, String(value));
        });
    }
    return fetchApi(`/backtests?${searchParams}`);
}

export async function getBacktest(id: number): Promise<Backtest & { trades: Trade[] }> {
    return fetchApi(`/backtests/${id}`);
}

export async function runBacktest(data: {
    agent_id: number;
    start_date: string;
    end_date: string;
    initial_capital?: number;
    holding_period_days?: number;
}): Promise<Backtest> {
    return fetchApi('/backtests', {
        method: 'POST',
        body: JSON.stringify(data),
    });
}
