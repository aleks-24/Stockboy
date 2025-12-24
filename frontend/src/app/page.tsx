'use client';

import { useEffect, useState } from 'react';
import {
  TrendingUp,
  TrendingDown,
  Activity,
  Bot,
  BarChart3,
  ArrowRight,
  Zap
} from 'lucide-react';
import Link from 'next/link';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import {
  MetricCard,
  InsiderBuysCard,
  InsiderSalesCard
} from '@/components/dashboard/metric-cards';
import { PortfolioChart } from '@/components/charts/portfolio-chart';
import { getStats, getInsiderTrades, getBacktests, type Stats, type InsiderTrade, type Backtest } from '@/lib/api';

export default function Dashboard() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [recentTrades, setRecentTrades] = useState<InsiderTrade[]>([]);
  const [recentBacktests, setRecentBacktests] = useState<Backtest[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchData() {
      try {
        const [statsData, tradesData, backtestsData] = await Promise.all([
          getStats(),
          getInsiderTrades({ limit: 10 }),
          getBacktests({ limit: 5 }),
        ]);
        setStats(statsData);
        setRecentTrades(tradesData.trades);
        setRecentBacktests(backtestsData.backtests);
      } catch (error) {
        console.error('Failed to fetch dashboard data:', error);
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, []);



  if (loading) {
    return (
      <div className="space-y-8">
        <div className="flex items-center justify-between">
          <div>
            <div className="h-8 w-48 skeleton rounded" />
            <div className="h-4 w-64 skeleton rounded mt-2" />
          </div>
        </div>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-32 skeleton rounded-xl" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">
            <span className="gradient-text">Dashboard</span>
          </h1>
          <p className="text-slate-400 mt-1">
            Monitor insider trading signals and LLM agent performance
          </p>
        </div>
        <div className="flex gap-3">
          <Link href="/agents">
            <Button variant="outline">
              <Bot className="w-4 h-4 mr-2" />
              Configure Agents
            </Button>
          </Link>
          <Link href="/backtest">
            <Button>
              <Zap className="w-4 h-4 mr-2" />
              Run Backtest
            </Button>
          </Link>
        </div>
      </div>

      {/* Metrics Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <MetricCard
          title="Total Insider Trades"
          value={stats?.total_insider_trades?.toLocaleString() || '0'}
          icon={<Activity className="w-4 h-4" />}
          description="All time"
        />
        <InsiderBuysCard count={stats?.recent_insider_buys || 0} />
        <InsiderSalesCard count={stats?.recent_insider_sales || 0} />
        <MetricCard
          title="Active Agents"
          value={stats?.total_agents || 0}
          icon={<Bot className="w-4 h-4" />}
          description={`${stats?.completed_backtests || 0} backtests run`}
        />
      </div>

      {/* Best Performer Alert */}
      {stats?.best_backtest && (
        <Card className="bg-gradient-to-r from-emerald-500/10 to-teal-500/10 border-emerald-500/30">
          <CardContent className="flex items-center justify-between p-6">
            <div className="flex items-center gap-4">
              <div className="p-3 rounded-xl bg-emerald-500/20">
                <TrendingUp className="w-6 h-6 text-emerald-400" />
              </div>
              <div>
                <h3 className="font-semibold text-white">Best Performing Agent</h3>
                <p className="text-slate-400 text-sm">
                  {stats.best_backtest.agent_name} achieved{' '}
                  <span className="text-emerald-400 font-medium">
                    {stats.best_backtest.total_return?.toFixed(1)}%
                  </span>{' '}
                  return with a Sharpe ratio of {stats.best_backtest.sharpe_ratio?.toFixed(2)}
                </p>
              </div>
            </div>
            <Link href={`/results/${stats.best_backtest.id}`}>
              <Button variant="outline" size="sm">
                View Details
                <ArrowRight className="w-4 h-4 ml-2" />
              </Button>
            </Link>
          </CardContent>
        </Card>
      )}

      {/* Charts and Tables */}
      <div className="grid gap-6 lg:grid-cols-3">
        {/* Portfolio Chart */}
        <div className="lg:col-span-2">
          {stats?.best_backtest?.portfolio_history && stats.best_backtest.portfolio_history.length > 0 ? (
            <PortfolioChart
              data={stats.best_backtest.portfolio_history}
              title="Latest Backtest Performance"
            />
          ) : (
            <Card className="col-span-full">
              <CardContent className="flex flex-col items-center justify-center py-24">
                <BarChart3 className="w-16 h-16 text-slate-600 mb-4" />
                <h3 className="text-lg font-medium text-white mb-2">No Backtest Data</h3>
                <p className="text-slate-400 text-sm mb-4">Run your first backtest to see performance charts</p>
                <Link href="/backtest">
                  <Button>
                    <Zap className="w-4 h-4 mr-2" />
                    Run Backtest
                  </Button>
                </Link>
              </CardContent>
            </Card>
          )}
        </div>

        {/* Recent Activity */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Activity className="w-5 h-5 text-emerald-400" />
              Recent Insider Activity
            </CardTitle>
            <CardDescription>Latest insider trading signals</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {recentTrades.length > 0 ? (
              recentTrades.slice(0, 5).map((trade) => (
                <div key={trade.id} className="flex items-center justify-between p-3 rounded-lg bg-slate-800/50 hover:bg-slate-800 transition-colors">
                  <div className="flex items-center gap-3">
                    <div className={`p-2 rounded-lg ${trade.trade_type?.includes('P')
                      ? 'bg-emerald-500/20 text-emerald-400'
                      : 'bg-red-500/20 text-red-400'
                      }`}>
                      {trade.trade_type?.includes('P') ? (
                        <TrendingUp className="w-4 h-4" />
                      ) : (
                        <TrendingDown className="w-4 h-4" />
                      )}
                    </div>
                    <div>
                      <p className="font-medium text-white">{trade.ticker}</p>
                      <p className="text-xs text-slate-500">{trade.insider_name}</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="font-medium text-white">
                      ${(trade.value / 1000).toFixed(0)}K
                    </p>
                    <p className="text-xs text-slate-500">
                      {new Date(trade.trade_date).toLocaleDateString()}
                    </p>
                  </div>
                </div>
              ))
            ) : (
              <div className="text-center py-8 text-slate-500">
                <p>No recent trades found.</p>
                <Link href="/data" className="text-emerald-400 hover:underline text-sm">
                  Import data to get started
                </Link>
              </div>
            )}
            {recentTrades.length > 0 && (
              <Link href="/data">
                <Button variant="ghost" className="w-full">
                  View All Trades
                  <ArrowRight className="w-4 h-4 ml-2" />
                </Button>
              </Link>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Recent Backtests */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <BarChart3 className="w-5 h-5 text-emerald-400" />
                Recent Backtests
              </CardTitle>
              <CardDescription>Latest benchmark results from LLM agents</CardDescription>
            </div>
            <Link href="/results">
              <Button variant="outline" size="sm">
                View All
                <ArrowRight className="w-4 h-4 ml-2" />
              </Button>
            </Link>
          </div>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-slate-800">
                  <th className="text-left py-3 px-4 text-slate-400 font-medium">Agent</th>
                  <th className="text-left py-3 px-4 text-slate-400 font-medium">Period</th>
                  <th className="text-right py-3 px-4 text-slate-400 font-medium">Return</th>
                  <th className="text-right py-3 px-4 text-slate-400 font-medium">Sharpe</th>
                  <th className="text-right py-3 px-4 text-slate-400 font-medium">Max DD</th>
                  <th className="text-right py-3 px-4 text-slate-400 font-medium">Alpha</th>
                  <th className="text-center py-3 px-4 text-slate-400 font-medium">Status</th>
                </tr>
              </thead>
              <tbody>
                {recentBacktests.length > 0 ? (
                  recentBacktests.map((backtest) => (
                    <tr key={backtest.id} className="border-b border-slate-800/50 hover:bg-slate-800/30">
                      <td className="py-3 px-4">
                        <Link href={`/results/${backtest.id}`} className="font-medium text-white hover:text-emerald-400">
                          {backtest.agent_name}
                        </Link>
                      </td>
                      <td className="py-3 px-4 text-slate-400 text-sm">
                        {new Date(backtest.start_date).toLocaleDateString()} -{' '}
                        {new Date(backtest.end_date).toLocaleDateString()}
                      </td>
                      <td className={`py-3 px-4 text-right font-medium ${(backtest.total_return || 0) >= 0 ? 'text-emerald-400' : 'text-red-400'
                        }`}>
                        {backtest.total_return?.toFixed(1)}%
                      </td>
                      <td className="py-3 px-4 text-right text-white">
                        {backtest.sharpe_ratio?.toFixed(2)}
                      </td>
                      <td className="py-3 px-4 text-right text-red-400">
                        -{backtest.max_drawdown?.toFixed(1)}%
                      </td>
                      <td className={`py-3 px-4 text-right font-medium ${(backtest.alpha || 0) >= 0 ? 'text-emerald-400' : 'text-red-400'
                        }`}>
                        {backtest.alpha?.toFixed(1)}%
                      </td>
                      <td className="py-3 px-4 text-center">
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${backtest.status === 'completed'
                          ? 'bg-emerald-500/20 text-emerald-400'
                          : backtest.status === 'running'
                            ? 'bg-yellow-500/20 text-yellow-400'
                            : 'bg-red-500/20 text-red-400'
                          }`}>
                          {backtest.status}
                        </span>
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={7} className="py-8 text-center text-slate-500">
                      No backtests yet.{' '}
                      <Link href="/backtest" className="text-emerald-400 hover:underline">
                        Run your first backtest
                      </Link>
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
