'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { BarChart3, TrendingUp, TrendingDown, ArrowRight } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { getBacktests, type Backtest } from '@/lib/api';

export default function ResultsPage() {
    const [backtests, setBacktests] = useState<Backtest[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        async function fetchBacktests() {
            try {
                const data = await getBacktests({ limit: 50 });
                setBacktests(data.backtests);
            } catch (error) {
                console.error('Failed to fetch backtests:', error);
            } finally {
                setLoading(false);
            }
        }
        fetchBacktests();
    }, []);

    return (
        <div className="space-y-8">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold">
                        <span className="gradient-text">Backtest Results</span>
                    </h1>
                    <p className="text-slate-400 mt-1">
                        Compare and analyze LLM agent performance
                    </p>
                </div>
                <Link href="/backtest">
                    <Button>
                        Run New Backtest
                        <ArrowRight className="w-4 h-4 ml-2" />
                    </Button>
                </Link>
            </div>

            {/* Results Table */}
            <Card>
                <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                        <BarChart3 className="w-5 h-5 text-emerald-400" />
                        All Backtests
                    </CardTitle>
                    <CardDescription>
                        Complete history of all benchmark runs
                    </CardDescription>
                </CardHeader>
                <CardContent>
                    {loading ? (
                        <div className="space-y-3">
                            {[1, 2, 3, 4, 5].map((i) => (
                                <div key={i} className="h-16 skeleton rounded-lg" />
                            ))}
                        </div>
                    ) : backtests.length > 0 ? (
                        <div className="overflow-x-auto">
                            <table className="w-full">
                                <thead>
                                    <tr className="border-b border-slate-800">
                                        <th className="text-left py-3 px-4 text-slate-400 font-medium">Agent</th>
                                        <th className="text-left py-3 px-4 text-slate-400 font-medium">Period</th>
                                        <th className="text-right py-3 px-4 text-slate-400 font-medium">Initial</th>
                                        <th className="text-right py-3 px-4 text-slate-400 font-medium">Final</th>
                                        <th className="text-right py-3 px-4 text-slate-400 font-medium">Return</th>
                                        <th className="text-right py-3 px-4 text-slate-400 font-medium">Sharpe</th>
                                        <th className="text-right py-3 px-4 text-slate-400 font-medium">Max DD</th>
                                        <th className="text-right py-3 px-4 text-slate-400 font-medium">Win Rate</th>
                                        <th className="text-right py-3 px-4 text-slate-400 font-medium">Trades</th>
                                        <th className="text-right py-3 px-4 text-slate-400 font-medium">Alpha</th>
                                        <th className="text-center py-3 px-4 text-slate-400 font-medium">Status</th>
                                        <th className="py-3 px-4"></th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {backtests.map((backtest) => (
                                        <tr
                                            key={backtest.id}
                                            className="border-b border-slate-800/50 hover:bg-slate-800/30 transition-colors"
                                        >
                                            <td className="py-4 px-4">
                                                <div className="flex items-center gap-2">
                                                    <div className={`p-1.5 rounded-lg ${(backtest.total_return || 0) >= 0
                                                            ? 'bg-emerald-500/20 text-emerald-400'
                                                            : 'bg-red-500/20 text-red-400'
                                                        }`}>
                                                        {(backtest.total_return || 0) >= 0 ? (
                                                            <TrendingUp className="w-4 h-4" />
                                                        ) : (
                                                            <TrendingDown className="w-4 h-4" />
                                                        )}
                                                    </div>
                                                    <span className="font-medium text-white">{backtest.agent_name}</span>
                                                </div>
                                            </td>
                                            <td className="py-4 px-4 text-slate-400 text-sm">
                                                {new Date(backtest.start_date).toLocaleDateString()} –<br />
                                                {new Date(backtest.end_date).toLocaleDateString()}
                                            </td>
                                            <td className="py-4 px-4 text-right text-slate-300">
                                                ${backtest.initial_capital?.toLocaleString()}
                                            </td>
                                            <td className="py-4 px-4 text-right text-white font-medium">
                                                ${backtest.final_value?.toLocaleString()}
                                            </td>
                                            <td className={`py-4 px-4 text-right font-bold ${(backtest.total_return || 0) >= 0 ? 'text-emerald-400' : 'text-red-400'
                                                }`}>
                                                {(backtest.total_return || 0) >= 0 ? '+' : ''}{backtest.total_return?.toFixed(1)}%
                                            </td>
                                            <td className="py-4 px-4 text-right text-white">
                                                {backtest.sharpe_ratio?.toFixed(2)}
                                            </td>
                                            <td className="py-4 px-4 text-right text-red-400">
                                                -{backtest.max_drawdown?.toFixed(1)}%
                                            </td>
                                            <td className="py-4 px-4 text-right text-white">
                                                {backtest.win_rate?.toFixed(0)}%
                                            </td>
                                            <td className="py-4 px-4 text-right text-slate-300">
                                                {backtest.total_trades}
                                            </td>
                                            <td className={`py-4 px-4 text-right font-medium ${(backtest.alpha || 0) >= 0 ? 'text-emerald-400' : 'text-red-400'
                                                }`}>
                                                {(backtest.alpha || 0) >= 0 ? '+' : ''}{backtest.alpha?.toFixed(1)}%
                                            </td>
                                            <td className="py-4 px-4 text-center">
                                                <span className={`px-2 py-1 rounded-full text-xs font-medium ${backtest.status === 'completed'
                                                        ? 'bg-emerald-500/20 text-emerald-400'
                                                        : backtest.status === 'running'
                                                            ? 'bg-yellow-500/20 text-yellow-400'
                                                            : 'bg-red-500/20 text-red-400'
                                                    }`}>
                                                    {backtest.status}
                                                </span>
                                            </td>
                                            <td className="py-4 px-4">
                                                <Link href={`/results/${backtest.id}`}>
                                                    <Button variant="ghost" size="sm">
                                                        View
                                                        <ArrowRight className="w-3 h-3 ml-1" />
                                                    </Button>
                                                </Link>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    ) : (
                        <div className="flex flex-col items-center justify-center py-12">
                            <BarChart3 className="w-12 h-12 text-slate-600 mb-4" />
                            <h3 className="text-lg font-medium text-white mb-2">No Backtests Yet</h3>
                            <p className="text-slate-400 text-sm mb-4">Run your first backtest to see results here</p>
                            <Link href="/backtest">
                                <Button>
                                    Run Backtest
                                    <ArrowRight className="w-4 h-4 ml-2" />
                                </Button>
                            </Link>
                        </div>
                    )}
                </CardContent>
            </Card>

            {/* Legend */}
            {backtests.length > 0 && (
                <Card className="bg-slate-800/30">
                    <CardContent className="p-4">
                        <div className="flex flex-wrap gap-6 text-sm">
                            <div>
                                <span className="text-slate-500">Return:</span>{' '}
                                <span className="text-slate-300">Total portfolio return %</span>
                            </div>
                            <div>
                                <span className="text-slate-500">Sharpe:</span>{' '}
                                <span className="text-slate-300">Risk-adjusted return (higher is better)</span>
                            </div>
                            <div>
                                <span className="text-slate-500">Max DD:</span>{' '}
                                <span className="text-slate-300">Maximum drawdown from peak</span>
                            </div>
                            <div>
                                <span className="text-slate-500">Alpha:</span>{' '}
                                <span className="text-slate-300">Excess return vs S&P 500</span>
                            </div>
                        </div>
                    </CardContent>
                </Card>
            )}
        </div>
    );
}
