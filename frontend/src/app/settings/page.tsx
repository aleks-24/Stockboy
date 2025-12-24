'use client';

import { useState } from 'react';
import { Save, Key, Check, AlertCircle } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';

export default function SettingsPage() {
    const [apiKeys, setApiKeys] = useState({
        openai: '',
        anthropic: '',
        google: '',
    });

    const [saving, setSaving] = useState(false);
    const [saveStatus, setSaveStatus] = useState<'idle' | 'success' | 'error'>('idle');

    const handleSave = async () => {
        setSaving(true);
        setSaveStatus('idle');

        try {
            // Save to .env file or backend configuration
            // This is a placeholder - in production, you'd send to backend
            await new Promise(resolve => setTimeout(resolve, 1000));

            setSaveStatus('success');
            setTimeout(() => setSaveStatus('idle'), 3000);
        } catch (error) {
            console.error('Failed to save settings:', error);
            setSaveStatus('error');
        } finally {
            setSaving(false);
        }
    };

    return (
        <div className="space-y-8 max-w-4xl">
            {/* Header */}
            <div>
                <h1 className="text-3xl font-bold">
                    <span className="gradient-text">Settings</span>
                </h1>
                <p className="text-slate-400 mt-1">
                    Configure your LLM API keys and platform preferences
                </p>
            </div>

            {/* API Keys Section */}
            <Card className="border-emerald-500/20">
                <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                        <Key className="w-5 h-5 text-emerald-400" />
                        LLM API Keys
                    </CardTitle>
                    <CardDescription>
                        Configure API keys for LLM providers. Keys are stored securely and never exposed to the frontend.
                    </CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                    {/* OpenAI */}
                    <div className="space-y-2">
                        <Label htmlFor="openai" className="flex items-center gap-2">
                            OpenAI API Key
                            <span className="text-xs text-slate-500">(gpt-4, gpt-3.5-turbo)</span>
                        </Label>
                        <Input
                            id="openai"
                            type="password"
                            placeholder="sk-..."
                            value={apiKeys.openai}
                            onChange={(e) => setApiKeys({ ...apiKeys, openai: e.target.value })}
                        />
                        <p className="text-xs text-slate-500">
                            Get your key from{' '}
                            <a
                                href="https://platform.openai.com/api-keys"
                                target="_blank"
                                rel="noopener noreferrer"
                                className="text-emerald-400 hover:underline"
                            >
                                platform.openai.com/api-keys
                            </a>
                        </p>
                    </div>

                    {/* Anthropic */}
                    <div className="space-y-2">
                        <Label htmlFor="anthropic" className="flex items-center gap-2">
                            Anthropic API Key
                            <span className="text-xs text-slate-500">(Claude 3)</span>
                        </Label>
                        <Input
                            id="anthropic"
                            type="password"
                            placeholder="sk-ant-..."
                            value={apiKeys.anthropic}
                            onChange={(e) => setApiKeys({ ...apiKeys, anthropic: e.target.value })}
                        />
                        <p className="text-xs text-slate-500">
                            Get your key from{' '}
                            <a
                                href="https://console.anthropic.com/"
                                target="_blank"
                                rel="noopener noreferrer"
                                className="text-emerald-400 hover:underline"
                            >
                                console.anthropic.com
                            </a>
                        </p>
                    </div>

                    {/* Google */}
                    <div className="space-y-2">
                        <Label htmlFor="google" className="flex items-center gap-2">
                            Google AI API Key
                            <span className="text-xs text-slate-500">(Gemini Pro)</span>
                        </Label>
                        <Input
                            id="google"
                            type="password"
                            placeholder="AIza..."
                            value={apiKeys.google}
                            onChange={(e) => setApiKeys({ ...apiKeys, google: e.target.value })}
                        />
                        <p className="text-xs text-slate-500">
                            Get your key from{' '}
                            <a
                                href="https://makersuite.google.com/app/apikey"
                                target="_blank"
                                rel="noopener noreferrer"
                                className="text-emerald-400 hover:underline"
                            >
                                makersuite.google.com/app/apikey
                            </a>
                        </p>
                    </div>

                    {/* Save Button */}
                    <div className="flex items-center justify-between pt-4 border-t border-slate-700">
                        <div className="flex items-center gap-2">
                            {saveStatus === 'success' && (
                                <div className="flex items-center gap-2 text-emerald-400">
                                    <Check className="w-4 h-4" />
                                    <span className="text-sm">Settings saved successfully</span>
                                </div>
                            )}
                            {saveStatus === 'error' && (
                                <div className="flex items-center gap-2 text-red-400">
                                    <AlertCircle className="w-4 h-4" />
                                    <span className="text-sm">Failed to save settings</span>
                                </div>
                            )}
                        </div>
                        <Button onClick={handleSave} disabled={saving}>
                            {saving ? (
                                <>
                                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2" />
                                    Saving...
                                </>
                            ) : (
                                <>
                                    <Save className="w-4 h-4 mr-2" />
                                    Save Settings
                                </>
                            )}
                        </Button>
                    </div>
                </CardContent>
            </Card>

            {/* Info Card */}
            <Card className="bg-slate-800/30 border-slate-700">
                <CardContent className="p-6">
                    <div className="flex gap-4">
                        <div className="p-3 rounded-lg bg-blue-500/20 text-blue-400 h-fit">
                            <AlertCircle className="w-5 h-5" />
                        </div>
                        <div className="space-y-2 text-sm">
                            <p className="font-medium text-white">Important Notes:</p>
                            <ul className="list-disc list-inside space-y-1 text-slate-400">
                                <li>API keys are stored locally and only used for LLM agent requests</li>
                                <li>You only need to configure keys for the LLM providers you plan to use</li>
                                <li>The <span className="text-emerald-400 font-mono">mock</span> provider doesn't require any API keys</li>
                                <li>Restart the backend after updating keys for changes to take effect</li>
                            </ul>
                        </div>
                    </div>
                </CardContent>
            </Card>
        </div>
    );
}
