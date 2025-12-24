'use client';

import { useEffect, useState } from 'react';
import { LineChart, Play, Loader2, Calendar, DollarSign, Clock } from 'lucide-react';
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
import { getAgents, runBacktest, type Agent, type Backtest } from '@/lib/api';
import { useRouter } from 'next/navigation';

export default function BacktestPage() {
    const router = useRouter();
    const [agents, setAgents] = useState<Agent[]>([]);
    const [loading, setLoading] = useState(true);
    const [running, setRunning] = useState(false);
    const [formData, setFormData] = useState({
        agent_id: '',
        start_date: new Date(Date.now() - 365 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
        end_date: new Date().toISOString().split('T')[0],
        initial_capital: 100000,
        holding_period_days: 30,
    });

    useEffect(() => {
        async function fetchAgents() {
            try {
                const data = await getAgents();
                setAgents(data.agents);
                if (data.agents.length > 0) {
                    setFormData(prev => ({ ...prev, agent_id: String(data.agents[0].id) }));
                }
            } catch (error) {
                console.error('Failed to fetch agents:', error);
            } finally {
                setLoading(false);
            }
        }
        fetchAgents();
    }, []);

    async function handleRunBacktest() {
        if (!formData.agent_id) return;

        setRunning(true);
        try {
            const result = await runBacktest({
                agent_id: parseInt(formData.agent_id),
                start_date: formData.start_date,
                end_date: formData.end_date,
                initial_capital: formData.initial_capital,
                holding_period_days: formData.holding_period_days,
            });

            // Navigate to results page
            router.push(`/results/${result.id}`);
        } catch (error) {
            console.error('Failed to run backtest:', error);
            alert('Backtest failed. Make sure you have insider trade data imported.');
        } finally {
            setRunning(false);
        }
    }

    const selectedAgent = agents.find(a => String(a.id) === formData.agent_id);

    // Preset date ranges
    const presets = [
        { label: '1 Year', days: 365 },
        { label: '2 Years', days: 730 },
        { label: '5 Years', days: 1825 },
    ];

    return (
        <div className="space-y-8 max-w-4xl mx-auto">
            {/* Header */}
            <div className="text-center">
                <h1 className="text-3xl font-bold">
                    <span className="gradient-text">Run Backtest</span>
                </h1>
                <p className="text-slate-400 mt-2">
                    Test your LLM agent against historical insider trading data
                </p>
            </div>

            {/* Main Form Card */}
            <Card className="border-emerald-500/20">
                <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                        <LineChart className="w-5 h-5 text-emerald-400" />
                        Backtest Configuration
                    </CardTitle>
                    <CardDescription>
                        Configure the backtest parameters and select an agent to evaluate
                    </CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                    {/* Agent Selection */}
                    <div className="space-y-2">
                        <Label className="flex items-center gap-2">
                            <span>Select Agent</span>
                            {loading && <Loader2 className="w-3 h-3 animate-spin" />}
                        </Label>
                        {agents.length > 0 ? (
                            <Select
                                value={formData.agent_id}
                                onValueChange={(value) => setFormData({ ...formData, agent_id: value })}
                            >
                                <SelectTrigger className="h-12">
                                    <SelectValue placeholder="Choose an agent..." />
                                </SelectTrigger>
                                <SelectContent>
                                    {agents.map((agent) => (
                                        <SelectItem key={agent.id} value={String(agent.id)}>
                                            <div className="flex items-center gap-2">
                                                <span className="font-medium">{agent.name}</span>
                                                <span className="text-slate-500 text-xs">
                                                    ({agent.provider}/{agent.model})
                                                </span>
                                            </div>
                                        </SelectItem>
                                    ))}
                                </SelectContent>
                            </Select>
                        ) : (
                            <div className="p-4 rounded-lg bg-slate-800/50 border border-slate-700 text-center">
                                <p className="text-slate-400 text-sm mb-2">No agents configured yet</p>
                                <Button variant="outline" size="sm" onClick={() => router.push('/agents')}>
                                    Create an Agent
                                </Button>
                            </div>
                        )}
                    </div>

                    {/* Selected Agent Summary */}
                    {selectedAgent && (
                        <div className="grid grid-cols-4 gap-4 p-4 rounded-lg bg-slate-800/30 border border-slate-700">
                            <div>
                                <p className="text-slate-500 text-xs">Provider</p>
                                <p className="text-white font-medium">{selectedAgent.provider}</p>
                            </div>
                            <div>
                                <p className="text-slate-500 text-xs">Model</p>
                                <p className="text-white font-medium">{selectedAgent.model}</p>
                            </div>
                            <div>
                                <p className="text-slate-500 text-xs">Risk</p>
                                <p className="text-white font-medium capitalize">{selectedAgent.risk_tolerance}</p>
                            </div>
                            <div>
                                <p className="text-slate-500 text-xs">Max Position</p>
                                <p className="text-white font-medium">{(selectedAgent.max_position_size * 100).toFixed(0)}%</p>
                            </div>
                        </div>
                    )}

                    {/* Date Range */}
                    <div className="space-y-3">
                        <Label className="flex items-center gap-2">
                            <Calendar className="w-4 h-4" />
                            Date Range
                        </Label>
                        <div className="flex gap-2 mb-3">
                            {presets.map((preset) => (
                                <Button
                                    key={preset.label}
                                    variant="outline"
                                    size="sm"
                                    onClick={() => {
                                        const end = new Date();
                                        const start = new Date(Date.now() - preset.days * 24 * 60 * 60 * 1000);
                                        setFormData({
                                            ...formData,
                                            start_date: start.toISOString().split('T')[0],
                                            end_date: end.toISOString().split('T')[0],
                                        });
                                    }}
                                >
                                    {preset.label}
                                </Button>
                            ))}
                        </div>
                        <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <Label htmlFor="startDate" className="text-slate-400">Start Date</Label>
                                <Input
                                    id="startDate"
                                    type="date"
                                    value={formData.start_date}
                                    onChange={(e) => setFormData({ ...formData, start_date: e.target.value })}
                                />
                            </div>
                            <div className="space-y-2">
                                <Label htmlFor="endDate" className="text-slate-400">End Date</Label>
                                <Input
                                    id="endDate"
                                    type="date"
                                    value={formData.end_date}
                                    onChange={(e) => setFormData({ ...formData, end_date: e.target.value })}
                                />
                            </div>
                        </div>
                    </div>

                    {/* Capital */}
                    <div className="space-y-2">
                        <Label htmlFor="capital" className="flex items-center gap-2">
                            <DollarSign className="w-4 h-4" />
                            Initial Capital
                        </Label>
                        <Input
                            id="capital"
                            type="number"
                            min="1000"
                            step="1000"
                            value={formData.initial_capital}
                            onChange={(e) => setFormData({ ...formData, initial_capital: parseInt(e.target.value) })}
                        />
                        <p className="text-xs text-slate-500">Starting portfolio value for the simulation</p>
                    </div>

                    {/* Holding Period */}
                    <div className="space-y-2">
                        <Label htmlFor="holdingPeriod" className="flex items-center gap-2">
                            <Clock className="w-4 h-4" />
                            Default Holding Period (days)
                        </Label>
                        <Input
                            id="holdingPeriod"
                            type="number"
                            min="1"
                            max="365"
                            value={formData.holding_period_days}
                            onChange={(e) => setFormData({ ...formData, holding_period_days: parseInt(e.target.value) })}
                        />
                        <p className="text-xs text-slate-500">How long to hold positions before re-evaluating</p>
                    </div>

                    {/* Run Button */}
                    <Button
                        onClick={handleRunBacktest}
                        disabled={!formData.agent_id || running}
                        className="w-full h-12 text-lg"
                    >
                        {running ? (
                            <>
                                <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                                Running Backtest...
                            </>
                        ) : (
                            <>
                                <Play className="w-5 h-5 mr-2" />
                                Start Backtest
                            </>
                        )}
                    </Button>

                    {/* Info */}
                    <div className="p-4 rounded-lg bg-slate-800/30 border border-slate-700">
                        <p className="text-xs text-slate-400">
                            <strong className="text-slate-300">Note:</strong> The backtest will simulate trading decisions based on
                            insider trading signals during the specified period. Each signal will be analyzed by the selected LLM agent,
                            which will decide whether to buy, sell, or hold. Performance metrics will be calculated and compared against
                            the S&P 500 benchmark.
                        </p>
                    </div>
                </CardContent>
            </Card>
        </div>
    );
}
