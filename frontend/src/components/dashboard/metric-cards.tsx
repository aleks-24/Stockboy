'use client';

import { TrendingUp, TrendingDown, DollarSign, Activity, Bot, BarChart3 } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { cn } from '@/lib/utils';

interface MetricCardProps {
    title: string;
    value: string | number;
    change?: number;
    icon: React.ReactNode;
    description?: string;
    variant?: 'default' | 'success' | 'danger';
}

export function MetricCard({
    title,
    value,
    change,
    icon,
    description,
    variant = 'default'
}: MetricCardProps) {
    const variantStyles = {
        default: 'from-slate-500/10 to-slate-600/10 border-slate-700',
        success: 'from-emerald-500/10 to-teal-500/10 border-emerald-500/30',
        danger: 'from-red-500/10 to-rose-500/10 border-red-500/30',
    };

    return (
        <Card className={cn(
            "bg-gradient-to-br transition-all duration-300 hover:scale-[1.02] hover:shadow-xl",
            variantStyles[variant]
        )}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium text-slate-400">{title}</CardTitle>
                <div className={cn(
                    "p-2 rounded-lg",
                    variant === 'success' && "bg-emerald-500/20 text-emerald-400",
                    variant === 'danger' && "bg-red-500/20 text-red-400",
                    variant === 'default' && "bg-slate-700/50 text-slate-400"
                )}>
                    {icon}
                </div>
            </CardHeader>
            <CardContent>
                <div className="text-2xl font-bold text-white">{value}</div>
                {(change !== undefined || description) && (
                    <div className="flex items-center gap-2 mt-1">
                        {change !== undefined && (
                            <span className={cn(
                                "flex items-center text-xs font-medium",
                                change >= 0 ? "text-emerald-400" : "text-red-400"
                            )}>
                                {change >= 0 ? (
                                    <TrendingUp className="w-3 h-3 mr-1" />
                                ) : (
                                    <TrendingDown className="w-3 h-3 mr-1" />
                                )}
                                {change >= 0 ? '+' : ''}{change.toFixed(1)}%
                            </span>
                        )}
                        {description && (
                            <span className="text-xs text-slate-500">{description}</span>
                        )}
                    </div>
                )}
            </CardContent>
        </Card>
    );
}

// Pre-configured metric cards for common use cases
export function InsiderBuysCard({ count, change }: { count: number; change?: number }) {
    return (
        <MetricCard
            title="Insider Buys (30d)"
            value={count.toLocaleString()}
            change={change}
            icon={<TrendingUp className="w-4 h-4" />}
            variant="success"
        />
    );
}

export function InsiderSalesCard({ count, change }: { count: number; change?: number }) {
    return (
        <MetricCard
            title="Insider Sales (30d)"
            value={count.toLocaleString()}
            change={change}
            icon={<TrendingDown className="w-4 h-4" />}
            variant="danger"
        />
    );
}

export function TotalTradesCard({ count }: { count: number }) {
    return (
        <MetricCard
            title="Total Insider Trades"
            value={count.toLocaleString()}
            icon={<Activity className="w-4 h-4" />}
        />
    );
}

export function ActiveAgentsCard({ count }: { count: number }) {
    return (
        <MetricCard
            title="Active Agents"
            value={count}
            icon={<Bot className="w-4 h-4" />}
        />
    );
}

export function BacktestsCard({ count }: { count: number }) {
    return (
        <MetricCard
            title="Completed Backtests"
            value={count}
            icon={<BarChart3 className="w-4 h-4" />}
        />
    );
}

export function BestReturnCard({ returnPct }: { returnPct: number | null }) {
    return (
        <MetricCard
            title="Best Backtest Return"
            value={returnPct !== null ? `${returnPct.toFixed(1)}%` : 'N/A'}
            icon={<DollarSign className="w-4 h-4" />}
            variant={returnPct && returnPct > 0 ? 'success' : returnPct && returnPct < 0 ? 'danger' : 'default'}
        />
    );
}
