"use client"

import { useEffect, useRef, useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Badge } from "@/components/ui/badge"
import { AlertCircle, CheckCircle2, Terminal } from "lucide-react"

interface LogMessage {
    message: string
    type: "info" | "error" | "warning" | "success" | "trade" | "progress" | "complete" | "analysis" | "analysis_details"
    timestamp?: string
}

interface LiveLogViewerProps {
    backtestId: number
    initialStatus?: string
    onComplete?: () => void
}

export function LiveLogViewer({ backtestId, initialStatus, onComplete }: LiveLogViewerProps) {
    const [logs, setLogs] = useState<LogMessage[]>([])
    const [status, setStatus] = useState<string>(initialStatus || "pending")
    const [connected, setConnected] = useState(false)
    const [error, setError] = useState<string | null>(null)
    const scrollRef = useRef<HTMLDivElement>(null)

    // Auto-scroll to bottom
    useEffect(() => {
        if (scrollRef.current) {
            const scrollContainer = scrollRef.current.querySelector('[data-radix-scroll-area-viewport]');
            if (scrollContainer) {
                scrollContainer.scrollTop = scrollContainer.scrollHeight;
            }
        }
    }, [logs])

    useEffect(() => {
        if (status === 'completed' && !connected) return;

        // Use environment variable for API URL or fallback
        const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:5000/api"
        const streamUrl = `${API_URL}/backtests/stream/${backtestId}`

        console.log(`Connecting to log stream: ${streamUrl}`)

        // Create EventSource
        const eventSource = new EventSource(streamUrl)

        eventSource.onopen = () => {
            setConnected(true)
            setError(null)
            addLog("Connected to live stream...", "info")
        }

        eventSource.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data)

                // Handle heartbeat (update last seen, maybe logic later)
                if (data.type === 'heartbeat') {
                    return
                }

                // Handle log message
                if (data.message) {
                    addLog(data.message, data.type)
                }

                // Handle completion
                if (data.type === 'complete') {
                    setStatus('completed')
                    eventSource.close()
                    setConnected(false)
                    if (onComplete) onComplete()
                }

                // Handle error from backend
                if (data.type === 'error') {
                    setError(data.message)
                    setStatus('failed')
                    eventSource.close()
                    setConnected(false)
                }

            } catch (e) {
                console.error("Error parsing SSE message:", e)
            }
        }

        eventSource.onerror = (e) => {
            console.error("SSE Error:", e)
            if (status !== 'completed') {
                // Only show error if we didn't expect to close
                // verify connection state... EventSource usually tries to reconnect
                // use readyState to check
                if (eventSource.readyState === EventSource.CLOSED) {
                    setConnected(false);
                }
            }
        }

        return () => {
            eventSource.close()
            setConnected(false)
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [backtestId])

    const addLog = (message: string, type: LogMessage['type'] = 'info') => {
        setLogs(prev => [...prev, { message, type, timestamp: new Date().toISOString() }])
    }

    const getLogColor = (type: string) => {
        switch (type) {
            case 'error': return 'text-red-500'
            case 'warning': return 'text-yellow-500'
            case 'success': return 'text-green-500 font-medium'
            case 'trade': return 'text-blue-400'
            case 'analysis': return 'text-purple-400 font-bold mt-2'
            case 'analysis_details': return 'text-zinc-400 pl-4 border-l-2 border-zinc-800'
            case 'progress': return 'text-muted-foreground'
            case 'complete': return 'text-green-400 font-bold'
            default: return 'text-foreground'
        }
    }

    return (
        <Card className="w-full bg-black/95 border-zinc-800">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium flex items-center gap-2">
                    <Terminal className="h-4 w-4" />
                    Live Logs
                </CardTitle>
                <div className="flex items-center gap-2">
                    {connected && <Badge variant="outline" className="bg-green-500/10 text-green-500 border-green-500/20 animate-pulse">Live</Badge>}
                    <Badge variant={status === 'completed' ? 'secondary' : 'outline'}>
                        {status}
                    </Badge>
                </div>
            </CardHeader>
            <CardContent>
                {error && (
                    <div className="mb-4 p-3 rounded bg-red-500/10 border border-red-500/20 text-red-500 flex items-center gap-2">
                        <AlertCircle className="h-4 w-4" />
                        {error}
                    </div>
                )}

                <ScrollArea className="h-[400px] w-full rounded border border-zinc-800 bg-zinc-950 p-4 font-mono text-xs" ref={scrollRef}>
                    <div className="space-y-1">
                        {logs.length === 0 && connected && (
                            <div className="text-zinc-500 italic">Waiting for logs...</div>
                        )}
                        {logs.map((log, i) => (
                            <div key={i} className={`flex gap-2 ${getLogColor(log.type)}`}>
                                <span className="text-zinc-600 shrink-0 select-none">
                                    {log.timestamp ? new Date(log.timestamp).toLocaleTimeString() : ''}
                                </span>
                                <span className="whitespace-pre-wrap font-mono">
                                    {log.type === 'trade' && '🛒 '}
                                    {log.type === 'success' && '✅ '}
                                    {log.type === 'analysis' && '🤖 '}
                                    {log.message}
                                </span>
                            </div>
                        ))}
                        {status === 'completed' && (
                            <div className="flex items-center gap-2 text-green-500 mt-4 pt-4 border-t border-zinc-800 font-bold">
                                <CheckCircle2 className="h-4 w-4" />
                                Backtest execution finished. Refreshing results...
                            </div>
                        )}
                    </div>
                </ScrollArea>
            </CardContent>
        </Card>
    )
}
