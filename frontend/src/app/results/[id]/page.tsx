'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import {
    ArrowLeft,
    TrendingUp,
    TrendingDown,
    DollarSign,
    Target,
    Activity,
    BarChart3,
    Clock
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { PortfolioChart } from '@/components/charts/portfolio-chart';
import { LiveLogViewer } from '@/components/backtest/live-log-viewer';
import { getBacktest, type Backtest, type Trade } from '@/lib/api';

export default function ResultDetailPage() {
    const params = useParams();
    const [backtest, setBacktest] = useState<(Backtest & { trades: Trade[] }) | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        async function fetchBacktest() {
            try {
                const data = await getBacktest(parseInt(params.id as string));
                setBacktest(data);

                // If it's done, we don't need to poll anymore
                if (data.status === 'completed') {
                    setLoading(false);
                }
            } catch (error) {
                console.error('Failed to fetch backtest:', error);
            } finally {
                // If we have data, we show it (even if pending)
                if (backtest || loading) {
                    setLoading(false);
                }
            }
        }
        if (params.id) {
            fetchBacktest();
        }
        // Poll every few seconds if running to get status updates (for the badge)
        // The LiveLogViewer handles the logs, but we want the main status badge to update too
        const interval = setInterval(() => {
            if (backtest && backtest.status !== 'completed' && backtest.status !== 'failed') {
                fetchBacktest();
            }
        }, 5000);

        return () => clearInterval(interval);
    }, [params.id, backtest?.status]);

    if (loading) {
        return (
            <div className="space-y-8">
                <div className="h-8 w-64 skeleton rounded" />
                <div className="grid gap-4 md:grid-cols-4">
                    {[1, 2, 3, 4].map((i) => (
                        <div key={i} className="h-32 skeleton rounded-xl" />
                    ))}
                </div>
                <div className="h-[400px] skeleton rounded-xl" />
            </div>
        );
    }

    if (!backtest) {
        return (
            <div className="flex flex-col items-center justify-center py-24">
                <h2 className="text-xl font-medium text-white mb-4">Backtest not found</h2>
                <Link href="/results">
                    <Button>Back to Results</Button>
                </Link>
            </div>
        );
    }

    const metrics = [
        {
            label: 'Total Return',
            value: `${(backtest.total_return || 0) >= 0 ? '+' : ''}${backtest.total_return?.toFixed(1)}%`,
            icon: TrendingUp,
            color: (backtest.total_return || 0) >= 0 ? 'emerald' : 'red',
        },
        {
            label: 'Final Value',
            value: `$${backtest.final_value?.toLocaleString()}`,
            icon: DollarSign,
            color: 'slate',
        },
        {
            label: 'Sharpe Ratio',
            value: backtest.sharpe_ratio?.toFixed(2) || 'N/A',
            icon: Target,
            color: 'slate',
        },
        {
            label: 'Max Drawdown',
            value: `-${backtest.max_drawdown?.toFixed(1)}%`,
            icon: TrendingDown,
            color: 'red',
        },
        {
            label: 'Win Rate',
            value: `${backtest.win_rate?.toFixed(0)}%`,
            icon: Activity,
            color: 'slate',
        },
        {
            label: 'Total Trades',
            value: backtest.total_trades?.toString() || '0',
            icon: BarChart3,
            color: 'slate',
        },
        {
            label: 'Alpha',
            value: `${(backtest.alpha || 0) >= 0 ? '+' : ''}${backtest.alpha?.toFixed(1)}%`,
            icon: TrendingUp,
            color: (backtest.alpha || 0) >= 0 ? 'emerald' : 'red',
        },
        {
            label: 'Benchmark',
            value: `${(backtest.benchmark_return || 0) >= 0 ? '+' : ''}${backtest.benchmark_return?.toFixed(1)}%`,
            icon: Activity,
            color: 'slate',
        },
    ];

    return (
        <div className="space-y-8">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                    <Link href="/results">
                        <Button variant="ghost" size="icon">
                            <ArrowLeft className="w-5 h-5" />
                        </Button>
                    </Link>
                    <div>
                        <h1 className="text-3xl font-bold">
                            <span className="gradient-text">{backtest.agent_name}</span>
                        </h1>
                        <p className="text-slate-400 mt-1 flex items-center gap-2">
                            <Clock className="w-4 h-4" />
                            {new Date(backtest.start_date).toLocaleDateString()} – {new Date(backtest.end_date).toLocaleDateString()}
                        </p>
                    </div>
                </div>
                <span className={`px-3 py-1.5 rounded-full text-sm font-medium ${backtest.status === 'completed'
                    ? 'bg-emerald-500/20 text-emerald-400'
                    : backtest.status === 'running'
                        ? 'bg-yellow-500/20 text-yellow-400'
                        : 'bg-red-500/20 text-red-400'
                    }`}>
                    {backtest.status}
                </span>
            </div>

            {/* Live Logging Section */}
            {backtest.status !== 'completed' && backtest.status !== 'failed' && (
                <div className="mb-8">
                    <LiveLogViewer
                        backtestId={backtest.id}
                        initialStatus={backtest.status}
                        onComplete={() => {
                            // Refresh page or data when complete
                            // fetchBacktest() will handle it on next poll or via state update logic
                            window.location.reload();
                        }}
                    />
                </div>
            )}

            {/* Metrics Grid */}
            <div className="grid gap-4 md:grid-cols-4">
                {metrics.map((metric) => (
                    <Card key={metric.label} className={`bg-gradient-to-br ${metric.color === 'emerald' ? 'from-emerald-500/10 to-teal-500/10 border-emerald-500/30' :
                        metric.color === 'red' ? 'from-red-500/10 to-rose-500/10 border-red-500/30' :
                            'from-slate-500/10 to-slate-600/10 border-slate-700'
                        }`}>
                        <CardContent className="p-4">
                            <div className="flex items-center justify-between">
                                <div>
                                    <p className="text-slate-400 text-sm">{metric.label}</p>
                                    <p className={`text-2xl font-bold ${metric.color === 'emerald' ? 'text-emerald-400' :
                                        metric.color === 'red' ? 'text-red-400' :
                                            'text-white'
                                        }`}>
                                        {metric.value}
                                    </p>
                                </div>
                                <div className={`p-2 rounded-lg ${metric.color === 'emerald' ? 'bg-emerald-500/20 text-emerald-400' :
                                    metric.color === 'red' ? 'bg-red-500/20 text-red-400' :
                                        'bg-slate-700/50 text-slate-400'
                                    }`}>
                                    <metric.icon className="w-5 h-5" />
                                </div>
                            </div>
                        </CardContent>
                    </Card>
                ))}
            </div>

            {/* Portfolio Chart */}
            {backtest.portfolio_history && backtest.portfolio_history.length > 0 && (
                <PortfolioChart
                    data={backtest.portfolio_history}
                    title="Portfolio Value Over Time"
                />
            )}

            {/* Trades Table */}
            <Card>
                <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                        <Activity className="w-5 h-5 text-emerald-400" />
                        Trade History
                    </CardTitle>
                    <CardDescription>
                        All trades executed during this backtest
                    </CardDescription>
                </CardHeader>
                <CardContent>
                    {backtest.trades && backtest.trades.length > 0 ? (
                        <div className="overflow-x-auto">
                            <table className="w-full">
                                <thead>
                                    <tr className="border-b border-slate-800">
                                        <th className="text-left py-3 px-4 text-slate-400 font-medium">Ticker</th>
                                        <th className="text-left py-3 px-4 text-slate-400 font-medium">Type</th>
                                        <th className="text-left py-3 px-4 text-slate-400 font-medium">Entry Date</th>
                                        <th className="text-right py-3 px-4 text-slate-400 font-medium">Entry Price</th>
                                        <th className="text-left py-3 px-4 text-slate-400 font-medium">Exit Date</th>
                                        <th className="text-right py-3 px-4 text-slate-400 font-medium">Exit Price</th>
                                        <th className="text-right py-3 px-4 text-slate-400 font-medium">Quantity</th>
                                        <th className="text-right py-3 px-4 text-slate-400 font-medium">P/L</th>
                                        <th className="text-right py-3 px-4 text-slate-400 font-medium">P/L %</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {backtest.trades.map((trade) => (
                                        <tr key={trade.id} className="border-b border-slate-800/50 hover:bg-slate-800/30">
                                            <td className="py-3 px-4 font-medium text-white">{trade.ticker}</td>
                                            <td className="py-3 px-4">
                                                <span className={`px-2 py-0.5 rounded text-xs font-medium ${trade.trade_type === 'buy'
                                                    ? 'bg-emerald-500/20 text-emerald-400'
                                                    : 'bg-red-500/20 text-red-400'
                                                    }`}>
                                                    {trade.trade_type.toUpperCase()}
                                                </span>
                                            </td>
                                            <td className="py-3 px-4 text-slate-400">
                                                {new Date(trade.entry_date).toLocaleDateString()}
                                            </td>
                                            <td className="py-3 px-4 text-right text-white">
                                                ${trade.entry_price?.toFixed(2)}
                                            </td>
                                            <td className="py-3 px-4 text-slate-400">
                                                {trade.exit_date ? new Date(trade.exit_date).toLocaleDateString() : '-'}
                                            </td>
                                            <td className="py-3 px-4 text-right text-white">
                                                {trade.exit_price ? `$${trade.exit_price.toFixed(2)}` : '-'}
                                            </td>
                                            <td className="py-3 px-4 text-right text-slate-300">
                                                {trade.quantity}
                                            </td>
                                            <td className={`py-3 px-4 text-right font-medium ${(trade.pnl || 0) >= 0 ? 'text-emerald-400' : 'text-red-400'
                                                }`}>
                                                {trade.pnl ? `${trade.pnl >= 0 ? '+' : ''}$${trade.pnl.toFixed(0)}` : '-'}
                                            </td>
                                            <td className={`py-3 px-4 text-right font-medium ${(trade.pnl_pct || 0) >= 0 ? 'text-emerald-400' : 'text-red-400'
                                                }`}>
                                                {trade.pnl_pct ? `${trade.pnl_pct >= 0 ? '+' : ''}${trade.pnl_pct.toFixed(1)}%` : '-'}
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    ) : (
                        <div className="text-center py-8 text-slate-500">
                            No trades were executed during this backtest.
                        </div>
                    )}
                </CardContent>
            </Card>
        </div>
    );
}
