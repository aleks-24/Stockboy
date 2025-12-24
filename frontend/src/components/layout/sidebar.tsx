"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
    LayoutDashboard,
    Bot,
    LineChart,
    TrendingUp,
    Settings,
    Database
} from "lucide-react";
import { cn } from "@/lib/utils";

const navigation = [
    { name: 'Dashboard', href: '/', icon: LayoutDashboard },
    { name: 'Agents', href: '/agents', icon: Bot },
    { name: 'Backtest', href: '/backtest', icon: LineChart },
    { name: 'Results', href: '/results', icon: TrendingUp },
    { name: 'Data', href: '/data', icon: Database },
    { name: 'Settings', href: '/settings', icon: Settings },
];

export function Sidebar() {
    const pathname = usePathname();

    return (
        <div className="flex h-screen w-64 flex-col fixed left-0 top-0 bg-slate-900/80 backdrop-blur-xl border-r border-slate-800">
            {/* Logo */}
            <div className="flex h-16 items-center px-6 border-b border-slate-800">
                <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-emerald-400 to-teal-500 flex items-center justify-center">
                        <TrendingUp className="w-6 h-6 text-white" />
                    </div>
                    <div>
                        <h1 className="text-lg font-bold text-white">Stockboy</h1>
                        <p className="text-xs text-slate-500">LLM Trading Benchmark</p>
                    </div>
                </div>
            </div>

            {/* Navigation */}
            <nav className="flex-1 px-3 py-4 space-y-1">
                {navigation.map((item) => {
                    const isActive = pathname === item.href ||
                        (item.href !== '/' && pathname.startsWith(item.href));

                    return (
                        <Link
                            key={item.name}
                            href={item.href}
                            className={cn(
                                "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-200",
                                isActive
                                    ? "bg-gradient-to-r from-emerald-500/20 to-teal-500/20 text-emerald-400 border border-emerald-500/30"
                                    : "text-slate-400 hover:text-white hover:bg-slate-800"
                            )}
                        >
                            <item.icon className={cn("w-5 h-5", isActive && "text-emerald-400")} />
                            {item.name}
                        </Link>
                    );
                })}
            </nav>

            {/* Footer */}
            <div className="p-4 border-t border-slate-800">
                <div className="flex items-center justify-between text-xs text-slate-500">
                    <span>v1.0.0</span>
                    <button className="hover:text-slate-300 transition-colors">
                        <Settings className="w-4 h-4" />
                    </button>
                </div>
            </div>
        </div>
    );
}
