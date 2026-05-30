"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { 
  Activity, 
  LineChart, 
  Globe, 
  Zap, 
  Cpu,
  ChevronLeft
} from "lucide-react";

interface SidebarProps {
  onToggle: () => void;
}

export default function Sidebar({ onToggle }: SidebarProps) {
  const pathname = usePathname();

  const menuItems = [
    { name: "Market Overview", path: "/", icon: Activity },
    { name: "Asset Analytics", path: "/analysis", icon: LineChart },
    { name: "Geopolitical News", path: "/events", icon: Globe },
    { name: "Scraper Playground", path: "/playground", icon: Zap },
  ];

  return (
    <aside className="w-full h-screen border-r border-[#ebdcb9] bg-[#fdfaf2] flex flex-col justify-between select-none">
      <div>
        {/* Brand header with collapse button */}
        <div className="p-6 border-b border-[#ebdcb9] flex items-center justify-between gap-2">
          <div className="flex items-center gap-3 overflow-hidden">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-amber-600 via-amber-500 to-yellow-400 flex items-center justify-center shadow-md shadow-amber-600/10 shrink-0">
              <Cpu className="w-5 h-5 text-white" />
            </div>
            <div className="truncate">
              <h1 className="font-extrabold text-lg leading-tight tracking-wide text-zinc-900">
                V-TRADER
              </h1>
              <div className="flex items-center gap-1.5 mt-0.5">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
                <span className="text-[10px] text-zinc-500 uppercase tracking-widest font-bold">
                  Swarm Active
                </span>
              </div>
            </div>
          </div>
          
          {/* Collapse Trigger Button */}
          <button 
            onClick={onToggle}
            className="p-1.5 rounded-lg hover:bg-amber-500/10 text-zinc-500 hover:text-zinc-800 transition-all cursor-pointer"
            title="Collapse Sidebar"
          >
            <ChevronLeft className="w-5 h-5" />
          </button>
        </div>

        {/* Menu items */}
        <nav className="p-4 space-y-1">
          {menuItems.map((item) => {
            const Icon = item.icon;
            const isActive = pathname === item.path;
            return (
              <Link
                key={item.path}
                href={item.path}
                className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-semibold transition-all duration-200 border ${
                  isActive 
                    ? "bg-amber-600/10 text-amber-800 border-amber-500/20" 
                    : "text-zinc-600 hover:text-zinc-900 hover:bg-amber-500/5 border-transparent"
                }`}
              >
                <Icon className="w-4.5 h-4.5" />
                {item.name}
              </Link>
            );
          })}
        </nav>
      </div>

      {/* User profile / session status */}
      <div className="p-4 border-t border-[#ebdcb9] bg-[#fdfaf2]">
        <div className="flex items-center gap-3 p-2 bg-[#f9f5e8] border border-[#ebdcb9]/60 rounded-xl overflow-hidden">
          <div className="w-8 h-8 rounded-lg bg-zinc-800 flex items-center justify-center font-bold text-sm text-zinc-100 shrink-0">
            U
          </div>
          <div className="truncate">
            <p className="text-xs font-bold text-zinc-800 truncate">Invest-User</p>
            <p className="text-[10px] text-zinc-500 truncate">Expert Swarm Active</p>
          </div>
        </div>
      </div>
    </aside>
  );
}
