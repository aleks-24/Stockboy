'use client';

import { useEffect, useState } from 'react';
import { Bot, Plus, Trash2, Edit2, Save, X } from 'lucide-react';
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
import { getAgents, createAgent, deleteAgent, type Agent } from '@/lib/api';

const PROVIDERS = [
    { value: 'openai', label: 'OpenAI', models: ['gpt-4', 'gpt-4-turbo', 'gpt-3.5-turbo'] },
    { value: 'anthropic', label: 'Anthropic', models: ['claude-3-opus-20240229', 'claude-3-sonnet-20240229', 'claude-3-haiku-20240307'] },
    { value: 'google', label: 'Google', models: ['gemini-pro', 'gemini-pro-vision'] },
    { value: 'mock', label: 'Mock (Testing)', models: ['mock'] },
];

const RISK_TOLERANCES = ['conservative', 'moderate', 'aggressive'];

export default function AgentsPage() {
    const [agents, setAgents] = useState<Agent[]>([]);
    const [loading, setLoading] = useState(true);
    const [showForm, setShowForm] = useState(false);
    const [formData, setFormData] = useState({
        name: '',
        provider: 'openai',
        model: 'gpt-4',
        temperature: 0.7,
        risk_tolerance: 'moderate',
        max_position_size: 0.1,
        stop_loss_pct: 0.1,
        take_profit_pct: 0.2,
        system_prompt: '',
    });

    useEffect(() => {
        fetchAgents();
    }, []);

    async function fetchAgents() {
        try {
            const data = await getAgents();
            setAgents(data.agents);
        } catch (error) {
            console.error('Failed to fetch agents:', error);
        } finally {
            setLoading(false);
        }
    }

    async function handleCreateAgent() {
        try {
            await createAgent(formData);
            setShowForm(false);
            setFormData({
                name: '',
                provider: 'openai',
                model: 'gpt-4',
                temperature: 0.7,
                risk_tolerance: 'moderate',
                max_position_size: 0.1,
                stop_loss_pct: 0.1,
                take_profit_pct: 0.2,
                system_prompt: '',
            });
            fetchAgents();
        } catch (error) {
            console.error('Failed to create agent:', error);
        }
    }

    async function handleDeleteAgent(id: number) {
        if (!confirm('Are you sure you want to delete this agent?')) return;
        try {
            await deleteAgent(id);
            fetchAgents();
        } catch (error) {
            console.error('Failed to delete agent:', error);
        }
    }

    const selectedProvider = PROVIDERS.find(p => p.value === formData.provider);

    return (
        <div className="space-y-8">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold">
                        <span className="gradient-text">LLM Agents</span>
                    </h1>
                    <p className="text-slate-400 mt-1">
                        Configure and manage trading agents for backtesting
                    </p>
                </div>
                <Button onClick={() => setShowForm(true)}>
                    <Plus className="w-4 h-4 mr-2" />
                    New Agent
                </Button>
            </div>

            {/* Create Form */}
            {showForm && (
                <Card className="border-emerald-500/30 bg-gradient-to-br from-emerald-500/5 to-teal-500/5">
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                            <Bot className="w-5 h-5 text-emerald-400" />
                            Create New Agent
                        </CardTitle>
                        <CardDescription>
                            Configure a new LLM trading agent with your preferred settings
                        </CardDescription>
                    </CardHeader>
                    <CardContent>
                        <div className="grid gap-6 md:grid-cols-2">
                            {/* Name */}
                            <div className="space-y-2">
                                <Label htmlFor="name">Agent Name</Label>
                                <Input
                                    id="name"
                                    placeholder="My Trading Agent"
                                    value={formData.name}
                                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                                />
                            </div>

                            {/* Provider */}
                            <div className="space-y-2">
                                <Label>LLM Provider</Label>
                                <Select
                                    value={formData.provider}
                                    onValueChange={(value) => {
                                        const provider = PROVIDERS.find(p => p.value === value);
                                        setFormData({
                                            ...formData,
                                            provider: value,
                                            model: provider?.models[0] || ''
                                        });
                                    }}
                                >
                                    <SelectTrigger>
                                        <SelectValue />
                                    </SelectTrigger>
                                    <SelectContent>
                                        {PROVIDERS.map((provider) => (
                                            <SelectItem key={provider.value} value={provider.value}>
                                                {provider.label}
                                            </SelectItem>
                                        ))}
                                    </SelectContent>
                                </Select>
                            </div>

                            {/* Model */}
                            <div className="space-y-2">
                                <Label>Model</Label>
                                <Select
                                    value={formData.model}
                                    onValueChange={(value) => setFormData({ ...formData, model: value })}
                                >
                                    <SelectTrigger>
                                        <SelectValue />
                                    </SelectTrigger>
                                    <SelectContent>
                                        {selectedProvider?.models.map((model) => (
                                            <SelectItem key={model} value={model}>
                                                {model}
                                            </SelectItem>
                                        ))}
                                    </SelectContent>
                                </Select>
                            </div>

                            {/* Temperature */}
                            <div className="space-y-2">
                                <Label htmlFor="temperature">Temperature ({formData.temperature})</Label>
                                <Input
                                    id="temperature"
                                    type="range"
                                    min="0"
                                    max="1"
                                    step="0.1"
                                    value={formData.temperature}
                                    onChange={(e) => setFormData({ ...formData, temperature: parseFloat(e.target.value) })}
                                    className="accent-emerald-500"
                                />
                            </div>

                            {/* Risk Tolerance */}
                            <div className="space-y-2">
                                <Label>Risk Tolerance</Label>
                                <Select
                                    value={formData.risk_tolerance}
                                    onValueChange={(value) => setFormData({ ...formData, risk_tolerance: value })}
                                >
                                    <SelectTrigger>
                                        <SelectValue />
                                    </SelectTrigger>
                                    <SelectContent>
                                        {RISK_TOLERANCES.map((risk) => (
                                            <SelectItem key={risk} value={risk}>
                                                {risk.charAt(0).toUpperCase() + risk.slice(1)}
                                            </SelectItem>
                                        ))}
                                    </SelectContent>
                                </Select>
                            </div>

                            {/* Max Position Size */}
                            <div className="space-y-2">
                                <Label htmlFor="position">Max Position Size ({(formData.max_position_size * 100).toFixed(0)}%)</Label>
                                <Input
                                    id="position"
                                    type="range"
                                    min="0.01"
                                    max="0.5"
                                    step="0.01"
                                    value={formData.max_position_size}
                                    onChange={(e) => setFormData({ ...formData, max_position_size: parseFloat(e.target.value) })}
                                    className="accent-emerald-500"
                                />
                            </div>

                            {/* Stop Loss */}
                            <div className="space-y-2">
                                <Label htmlFor="stopLoss">Stop Loss ({(formData.stop_loss_pct * 100).toFixed(0)}%)</Label>
                                <Input
                                    id="stopLoss"
                                    type="range"
                                    min="0.01"
                                    max="0.3"
                                    step="0.01"
                                    value={formData.stop_loss_pct}
                                    onChange={(e) => setFormData({ ...formData, stop_loss_pct: parseFloat(e.target.value) })}
                                    className="accent-red-500"
                                />
                            </div>

                            {/* Take Profit */}
                            <div className="space-y-2">
                                <Label htmlFor="takeProfit">Take Profit ({(formData.take_profit_pct * 100).toFixed(0)}%)</Label>
                                <Input
                                    id="takeProfit"
                                    type="range"
                                    min="0.05"
                                    max="0.5"
                                    step="0.01"
                                    value={formData.take_profit_pct}
                                    onChange={(e) => setFormData({ ...formData, take_profit_pct: parseFloat(e.target.value) })}
                                    className="accent-emerald-500"
                                />
                            </div>

                            {/* System Prompt */}
                            <div className="space-y-2 md:col-span-2">
                                <Label htmlFor="prompt">Custom System Prompt (optional)</Label>
                                <textarea
                                    id="prompt"
                                    className="flex min-h-[100px] w-full rounded-lg border border-slate-700 bg-slate-800/50 px-3 py-2 text-sm text-slate-100 placeholder:text-slate-500 focus:border-emerald-500 focus:outline-none focus:ring-2 focus:ring-emerald-500/20"
                                    placeholder="Custom instructions for the LLM agent... (leave empty for default)"
                                    value={formData.system_prompt}
                                    onChange={(e) => setFormData({ ...formData, system_prompt: e.target.value })}
                                />
                            </div>
                        </div>

                        {/* Actions */}
                        <div className="flex justify-end gap-3 mt-6">
                            <Button variant="outline" onClick={() => setShowForm(false)}>
                                <X className="w-4 h-4 mr-2" />
                                Cancel
                            </Button>
                            <Button onClick={handleCreateAgent} disabled={!formData.name}>
                                <Save className="w-4 h-4 mr-2" />
                                Create Agent
                            </Button>
                        </div>
                    </CardContent>
                </Card>
            )}

            {/* Agents Grid */}
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                {loading ? (
                    [1, 2, 3].map((i) => (
                        <div key={i} className="h-48 skeleton rounded-xl" />
                    ))
                ) : agents.length > 0 ? (
                    agents.map((agent) => (
                        <Card key={agent.id} className="card-hover">
                            <CardHeader className="pb-3">
                                <div className="flex items-start justify-between">
                                    <div className="flex items-center gap-3">
                                        <div className="p-2 rounded-lg bg-emerald-500/20 text-emerald-400">
                                            <Bot className="w-5 h-5" />
                                        </div>
                                        <div>
                                            <CardTitle className="text-lg">{agent.name}</CardTitle>
                                            <CardDescription>{agent.provider} / {agent.model}</CardDescription>
                                        </div>
                                    </div>
                                    <Button
                                        variant="ghost"
                                        size="icon"
                                        className="text-slate-500 hover:text-red-400"
                                        onClick={() => handleDeleteAgent(agent.id)}
                                    >
                                        <Trash2 className="w-4 h-4" />
                                    </Button>
                                </div>
                            </CardHeader>
                            <CardContent>
                                <div className="grid grid-cols-2 gap-4 text-sm">
                                    <div>
                                        <p className="text-slate-500">Risk</p>
                                        <p className="text-white capitalize">{agent.risk_tolerance}</p>
                                    </div>
                                    <div>
                                        <p className="text-slate-500">Temperature</p>
                                        <p className="text-white">{agent.temperature}</p>
                                    </div>
                                    <div>
                                        <p className="text-slate-500">Max Position</p>
                                        <p className="text-white">{(agent.max_position_size * 100).toFixed(0)}%</p>
                                    </div>
                                    <div>
                                        <p className="text-slate-500">Stop Loss</p>
                                        <p className="text-red-400">{(agent.stop_loss_pct * 100).toFixed(0)}%</p>
                                    </div>
                                </div>
                            </CardContent>
                        </Card>
                    ))
                ) : (
                    <Card className="md:col-span-2 lg:col-span-3">
                        <CardContent className="flex flex-col items-center justify-center py-12">
                            <Bot className="w-12 h-12 text-slate-600 mb-4" />
                            <h3 className="text-lg font-medium text-white mb-2">No Agents Yet</h3>
                            <p className="text-slate-400 text-sm mb-4">Create your first LLM trading agent to get started</p>
                            <Button onClick={() => setShowForm(true)}>
                                <Plus className="w-4 h-4 mr-2" />
                                Create Agent
                            </Button>
                        </CardContent>
                    </Card>
                )}
            </div>
        </div>
    );
}
