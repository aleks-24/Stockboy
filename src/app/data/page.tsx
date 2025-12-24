'use client';

import { useEffect, useState } from 'react';
import { Database, Download, RefreshCw, Loader2, TrendingUp, TrendingDown, Search } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue
} from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { getInsiderTrades, scrapeInsiderTrades, getClusterBuys, type InsiderTrade } from '@/lib/api';

export default function DataPage() {
    const [trades, setTrades] = useState<InsiderTrade[]>([]);
    const [clusters, setClusters] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [scraping, setScraping] = useState(false);
    const [total, setTotal] = useState(0);
    const [filters, setFilters] = useState({
        ticker: '',
        trade_type: '',
        limit: 50,
        offset: 0,
    });

    useEffect(() => {
        fetchTrades();
        fetchClusters();
    }, []);

    async function fetchTrades() {
        setLoading(true);
        try {
            const data = await getInsiderTrades(filters);
            setTrades(data.trades);
            setTotal(data.total);
        } catch (error) {
            console.error('Failed to fetch trades:', error);
        } finally {
            setLoading(false);
        }
    }

    async function fetchClusters() {
        try {
            const data = await getClusterBuys({ days: 30 });
            setClusters(data.clusters);
        } catch (error) {
            console.error('Failed to fetch clusters:', error);
        }
    }

    async function handleScrape() {
        setScraping(true);
        try {
            const result = await scrapeInsiderTrades({ max_pages: 5 });
            alert(`Scraped ${result.scraped} trades, saved ${result.saved} new records`);
            fetchTrades();
        } catch (error) {
            console.error('Failed to scrape:', error);
            alert('Scraping failed. Check the backend console for errors.');
        } finally {
            setScraping(false);
        }
    }

    async function handleFilter() {
        setFilters({ ...filters, offset: 0 });
        fetchTrades();
    }

    return (
        <div className="space-y-8">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold">
                        <span className="gradient-text">Data Management</span>
                    </h1>
                    <p className="text-slate-400 mt-1">
                        Import and manage insider trading data from OpenInsider.com
                    </p>
                </div>
                <Button onClick={handleScrape} disabled={scraping}>
                    {scraping ? (
                        <>
                            <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                            Scraping...
                        </>
                    ) : (
                        <>
                            <Download className="w-4 h-4 mr-2" />
                            Import Data
                        </>
                    )}
                </Button>
            </div>

            {/* Stats */}
            <div className="grid gap-4 md:grid-cols-3">
                <Card>
                    <CardContent className="p-6">
                        <div className="flex items-center gap-4">
                            <div className="p-3 rounded-xl bg-emerald-500/20 text-emerald-400">
                                <Database className="w-6 h-6" />
                            </div>
                            <div>
                                <p className="text-slate-400 text-sm">Total Trades</p>
                                <p className="text-2xl font-bold text-white">{total.toLocaleString()}</p>
                            </div>
                        </div>
                    </CardContent>
                </Card>
                <Card>
                    <CardContent className="p-6">
                        <div className="flex items-center gap-4">
                            <div className="p-3 rounded-xl bg-teal-500/20 text-teal-400">
                                <TrendingUp className="w-6 h-6" />
                            </div>
                            <div>
                                <p className="text-slate-400 text-sm">Cluster Buys (30d)</p>
                                <p className="text-2xl font-bold text-white">{clusters.length}</p>
                            </div>
                        </div>
                    </CardContent>
                </Card>
                <Card>
                    <CardContent className="p-6">
                        <div className="flex items-center gap-4">
                            <div className="p-3 rounded-xl bg-cyan-500/20 text-cyan-400">
                                <RefreshCw className="w-6 h-6" />
                            </div>
                            <div>
                                <p className="text-slate-400 text-sm">Data Source</p>
                                <p className="text-lg font-medium text-white">openinsider.com</p>
                            </div>
                        </div>
                    </CardContent>
                </Card>
            </div>

            {/* Tabs */}
            <Tabs defaultValue="trades" className="space-y-6">
                <TabsList className="grid w-full max-w-md grid-cols-2">
                    <TabsTrigger value="trades">All Trades</TabsTrigger>
                    <TabsTrigger value="clusters">Cluster Buys</TabsTrigger>
                </TabsList>

                <TabsContent value="trades" className="space-y-4">
                    {/* Filters */}
                    <Card>
                        <CardContent className="p-4">
                            <div className="flex flex-wrap gap-4 items-end">
                                <div className="space-y-2">
                                    <Label>Ticker</Label>
                                    <Input
                                        placeholder="e.g. AAPL"
                                        value={filters.ticker}
                                        onChange={(e) => setFilters({ ...filters, ticker: e.target.value.toUpperCase() })}
                                        className="w-32"
                                    />
                                </div>
                                <div className="space-y-2">
                                    <Label>Type</Label>
                                    <Select
                                        value={filters.trade_type}
                                        onValueChange={(value) => setFilters({ ...filters, trade_type: value })}
                                    >
                                        <SelectTrigger className="w-32">
                                            <SelectValue placeholder="All" />
                                        </SelectTrigger>
                                        <SelectContent>
                                            <SelectItem value="">All</SelectItem>
                                            <SelectItem value="P">Purchases</SelectItem>
                                            <SelectItem value="S">Sales</SelectItem>
                                        </SelectContent>
                                    </Select>
                                </div>
                                <Button onClick={handleFilter} variant="outline">
                                    <Search className="w-4 h-4 mr-2" />
                                    Filter
                                </Button>
                            </div>
                        </CardContent>
                    </Card>

                    {/* Trades Table */}
                    <Card>
                        <CardHeader>
                            <CardTitle>Insider Trades</CardTitle>
                            <CardDescription>
                                Showing {trades.length} of {total.toLocaleString()} total trades
                            </CardDescription>
                        </CardHeader>
                        <CardContent>
                            {loading ? (
                                <div className="space-y-3">
                                    {[1, 2, 3, 4, 5].map((i) => (
                                        <div key={i} className="h-12 skeleton rounded" />
                                    ))}
                                </div>
                            ) : trades.length > 0 ? (
                                <div className="overflow-x-auto">
                                    <table className="w-full">
                                        <thead>
                                            <tr className="border-b border-slate-800">
                                                <th className="text-left py-3 px-4 text-slate-400 font-medium">Date</th>
                                                <th className="text-left py-3 px-4 text-slate-400 font-medium">Ticker</th>
                                                <th className="text-left py-3 px-4 text-slate-400 font-medium">Company</th>
                                                <th className="text-left py-3 px-4 text-slate-400 font-medium">Insider</th>
                                                <th className="text-center py-3 px-4 text-slate-400 font-medium">Type</th>
                                                <th className="text-right py-3 px-4 text-slate-400 font-medium">Price</th>
                                                <th className="text-right py-3 px-4 text-slate-400 font-medium">Value</th>
                                                <th className="text-right py-3 px-4 text-slate-400 font-medium">Δ Owned</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {trades.map((trade) => (
                                                <tr key={trade.id} className="border-b border-slate-800/50 hover:bg-slate-800/30">
                                                    <td className="py-3 px-4 text-slate-400 text-sm">
                                                        {new Date(trade.trade_date).toLocaleDateString()}
                                                    </td>
                                                    <td className="py-3 px-4 font-medium text-white">{trade.ticker}</td>
                                                    <td className="py-3 px-4 text-slate-300 text-sm max-w-[200px] truncate">
                                                        {trade.company_name}
                                                    </td>
                                                    <td className="py-3 px-4 text-slate-400 text-sm max-w-[150px] truncate">
                                                        {trade.insider_name}
                                                    </td>
                                                    <td className="py-3 px-4 text-center">
                                                        <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium ${trade.trade_type?.includes('P')
                                                                ? 'bg-emerald-500/20 text-emerald-400'
                                                                : 'bg-red-500/20 text-red-400'
                                                            }`}>
                                                            {trade.trade_type?.includes('P') ? (
                                                                <TrendingUp className="w-3 h-3" />
                                                            ) : (
                                                                <TrendingDown className="w-3 h-3" />
                                                            )}
                                                            {trade.trade_type?.includes('P') ? 'BUY' : 'SELL'}
                                                        </span>
                                                    </td>
                                                    <td className="py-3 px-4 text-right text-white">
                                                        ${trade.price?.toFixed(2)}
                                                    </td>
                                                    <td className="py-3 px-4 text-right text-white">
                                                        ${(trade.value / 1000).toFixed(0)}K
                                                    </td>
                                                    <td className="py-3 px-4 text-right text-slate-400">
                                                        {trade.delta_owned ? `${trade.delta_owned.toFixed(1)}%` : '-'}
                                                    </td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>
                            ) : (
                                <div className="text-center py-12 text-slate-500">
                                    <Database className="w-12 h-12 mx-auto mb-4" />
                                    <p className="mb-4">No insider trading data found</p>
                                    <Button onClick={handleScrape} disabled={scraping}>
                                        <Download className="w-4 h-4 mr-2" />
                                        Import Data
                                    </Button>
                                </div>
                            )}

                            {/* Pagination */}
                            {trades.length > 0 && (
                                <div className="flex items-center justify-between mt-4 pt-4 border-t border-slate-800">
                                    <p className="text-sm text-slate-500">
                                        Page {Math.floor(filters.offset / filters.limit) + 1} of {Math.ceil(total / filters.limit)}
                                    </p>
                                    <div className="flex gap-2">
                                        <Button
                                            variant="outline"
                                            size="sm"
                                            disabled={filters.offset === 0}
                                            onClick={() => {
                                                setFilters({ ...filters, offset: Math.max(0, filters.offset - filters.limit) });
                                                fetchTrades();
                                            }}
                                        >
                                            Previous
                                        </Button>
                                        <Button
                                            variant="outline"
                                            size="sm"
                                            disabled={filters.offset + filters.limit >= total}
                                            onClick={() => {
                                                setFilters({ ...filters, offset: filters.offset + filters.limit });
                                                fetchTrades();
                                            }}
                                        >
                                            Next
                                        </Button>
                                    </div>
                                </div>
                            )}
                        </CardContent>
                    </Card>
                </TabsContent>

                <TabsContent value="clusters">
                    <Card>
                        <CardHeader>
                            <CardTitle>Cluster Buys</CardTitle>
                            <CardDescription>
                                Multiple insiders buying the same stock within 30 days
                            </CardDescription>
                        </CardHeader>
                        <CardContent>
                            {clusters.length > 0 ? (
                                <div className="grid gap-4 md:grid-cols-2">
                                    {clusters.map((cluster) => (
                                        <Card key={cluster.ticker} className="bg-slate-800/30 border-emerald-500/20">
                                            <CardContent className="p-4">
                                                <div className="flex items-start justify-between mb-3">
                                                    <div>
                                                        <h3 className="font-bold text-lg text-white">{cluster.ticker}</h3>
                                                        <p className="text-sm text-slate-400">{cluster.company_name}</p>
                                                    </div>
                                                    <div className="text-right">
                                                        <p className="text-2xl font-bold text-emerald-400">
                                                            {cluster.num_insiders}
                                                        </p>
                                                        <p className="text-xs text-slate-500">insiders</p>
                                                    </div>
                                                </div>
                                                <div className="space-y-2 text-sm">
                                                    <div className="flex justify-between">
                                                        <span className="text-slate-500">Total Value</span>
                                                        <span className="text-white font-medium">
                                                            ${(cluster.total_value / 1000).toFixed(0)}K
                                                        </span>
                                                    </div>
                                                    <div className="flex justify-between">
                                                        <span className="text-slate-500">Insiders</span>
                                                        <span className="text-slate-300 text-xs">
                                                            {cluster.insiders.slice(0, 3).join(', ')}
                                                            {cluster.insiders.length > 3 && ` +${cluster.insiders.length - 3} more`}
                                                        </span>
                                                    </div>
                                                </div>
                                            </CardContent>
                                        </Card>
                                    ))}
                                </div>
                            ) : (
                                <div className="text-center py-12 text-slate-500">
                                    <TrendingUp className="w-12 h-12 mx-auto mb-4" />
                                    <p>No cluster buys detected in the last 30 days</p>
                                </div>
                            )}
                        </CardContent>
                    </Card>
                </TabsContent>
            </Tabs>
        </div>
    );
}
