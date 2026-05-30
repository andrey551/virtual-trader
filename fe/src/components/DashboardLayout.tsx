"use client";

import React, { useState } from "react";
import Sidebar from "./Sidebar";
import { Menu } from "lucide-react";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const [isCollapsed, setIsCollapsed] = useState(false);

  return (
    <div className="min-h-full flex bg-[#fbf8ee] text-[#2b2d31] font-sans w-full relative">
      {/* Sidebar container with collapsible sliding animation */}
      <div 
        className={`transition-all duration-300 ease-in-out border-r border-[#ebdcb9] ${
          isCollapsed ? "w-0 opacity-0 overflow-hidden border-r-0" : "w-64 opacity-100"
        } shrink-0`}
      >
        <Sidebar onToggle={() => setIsCollapsed(true)} />
      </div>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 bg-[#fbf8ee] h-screen overflow-y-auto relative">
        {/* Floating Toggle Expand Button when sidebar is collapsed */}
        {isCollapsed && (
          <button
            onClick={() => setIsCollapsed(false)}
            className="absolute left-6 top-6 z-50 p-2 rounded-xl bg-white border border-[#ebdcb9] hover:bg-amber-500/5 text-zinc-700 shadow-sm transition-all cursor-pointer animate-fadeIn"
            title="Expand Sidebar"
          >
            <Menu className="w-5 h-5" />
          </button>
        )}
        
        {/* Render children inside main pane */}
        <div className={`transition-all duration-300 ${isCollapsed ? "pl-2" : "pl-0"}`}>
          {children}
        </div>
      </div>
    </div>
  );
}
