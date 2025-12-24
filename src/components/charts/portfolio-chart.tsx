'use client';

import {
    LineChart,
    Line,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    Area,
    AreaChart,
    Legend,
} from 'recharts';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

interface PortfolioChartProps {
    data: { date: string; value: number; benchmark?: number }[];
    title?: string;
    showBenchmark?: boolean;
}

export function PortfolioChart({
    data,
    title = "Portfolio Performance",
    showBenchmark = true
}: PortfolioChartProps) {
    const formatCurrency = (value: number) => {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD',
            minimumFractionDigits: 0,
            maximumFractionDigits: 0,
        }).format(value);
    };

    const formatDate = (dateStr: string) => {
        const date = new Date(dateStr);
        return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    };

    const CustomTooltip = ({ active, payload, label }: any) => {
        if (active && payload && payload.length) {
            return (
                <div className="bg-slate-800 border border-slate-700 rounded-lg p-3 shadow-xl">
                    <p className="text-slate-400 text-xs mb-2">{formatDate(label)}</p>
                    {payload.map((entry: any, index: number) => (
                        <p key={index} className="text-sm font-medium" style={{ color: entry.color }}>
                            {entry.name}: {formatCurrency(entry.value)}
                        </p>
                    ))}
                </div>
            );
        }
        return null;
    };

    return (
        <Card className="col-span-full">
            <CardHeader>
                <CardTitle className="flex items-center justify-between">
                    <span>{title}</span>
                    <div className="flex items-center gap-4 text-sm font-normal">
                        <div className="flex items-center gap-2">
                            <div className="w-3 h-3 rounded-full bg-emerald-500" />
                            <span className="text-slate-400">Portfolio</span>
                        </div>
                        {showBenchmark && (
                            <div className="flex items-center gap-2">
                                <div className="w-3 h-3 rounded-full bg-slate-500" />
                                <span className="text-slate-400">S&P 500</span>
                            </div>
                        )}
                    </div>
                </CardTitle>
            </CardHeader>
            <CardContent>
                <div className="h-[400px] w-full">
                    <ResponsiveContainer width="100%" height="100%">
                        <AreaChart
                            data={data}
                            margin={{ top: 10, right: 10, left: 0, bottom: 0 }}
                        >
                            <defs>
                                <linearGradient id="portfolioGradient" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="5%" stopColor="#10b981" stopOpacity={0.3} />
                                    <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
                                </linearGradient>
                                <linearGradient id="benchmarkGradient" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="5%" stopColor="#64748b" stopOpacity={0.2} />
                                    <stop offset="95%" stopColor="#64748b" stopOpacity={0} />
                                </linearGradient>
                            </defs>
                            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                            <XAxis
                                dataKey="date"
                                tickFormatter={formatDate}
                                stroke="#64748b"
                                fontSize={12}
                            />
                            <YAxis
                                tickFormatter={formatCurrency}
                                stroke="#64748b"
                                fontSize={12}
                            />
                            <Tooltip content={<CustomTooltip />} />
                            {showBenchmark && data[0]?.benchmark !== undefined && (
                                <Area
                                    type="monotone"
                                    dataKey="benchmark"
                                    name="S&P 500"
                                    stroke="#64748b"
                                    fillOpacity={1}
                                    fill="url(#benchmarkGradient)"
                                    strokeWidth={2}
                                />
                            )}
                            <Area
                                type="monotone"
                                dataKey="value"
                                name="Portfolio"
                                stroke="#10b981"
                                fillOpacity={1}
                                fill="url(#portfolioGradient)"
                                strokeWidth={2}
                            />
                        </AreaChart>
                    </ResponsiveContainer>
                </div>
            </CardContent>
        </Card>
    );
}

interface StockPriceChartProps {
    data: { date: string; close: number; volume: number }[];
    ticker: string;
}

export function StockPriceChart({ data, ticker }: StockPriceChartProps) {
    return (
        <Card>
            <CardHeader>
                <CardTitle>{ticker} Price History</CardTitle>
            </CardHeader>
            <CardContent>
                <div className="h-[300px] w-full">
                    <ResponsiveContainer width="100%" height="100%">
                        <LineChart data={data}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                            <XAxis
                                dataKey="date"
                                stroke="#64748b"
                                fontSize={12}
                            />
                            <YAxis stroke="#64748b" fontSize={12} />
                            <Tooltip
                                contentStyle={{
                                    backgroundColor: '#1e293b',
                                    border: '1px solid #334155',
                                    borderRadius: '8px'
                                }}
                            />
                            <Line
                                type="monotone"
                                dataKey="close"
                                stroke="#10b981"
                                strokeWidth={2}
                                dot={false}
                            />
                        </LineChart>
                    </ResponsiveContainer>
                </div>
            </CardContent>
        </Card>
    );
}
