import React from "react";
import { LucideIcon } from "lucide-react";

interface StatsCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: LucideIcon;
  trend?: string;
  color: "red" | "emerald" | "blue" | "amber" | "purple";
}

export const StatsCard: React.FC<StatsCardProps> = ({
  title,
  value,
  subtitle,
  icon: Icon,
  trend,
  color,
}) => {
  const colorMap = {
    red: {
      bg: "from-red-500/10 to-rose-500/5",
      border: "border-red-500/20",
      text: "text-red-400",
      iconBg: "bg-red-500/20 text-red-400",
      glow: "hover:border-red-500/40",
    },
    emerald: {
      bg: "from-emerald-500/10 to-teal-500/5",
      border: "border-emerald-500/20",
      text: "text-emerald-400",
      iconBg: "bg-emerald-500/20 text-emerald-400",
      glow: "hover:border-emerald-500/40",
    },
    blue: {
      bg: "from-blue-500/10 to-cyan-500/5",
      border: "border-blue-500/20",
      text: "text-blue-400",
      iconBg: "bg-blue-500/20 text-blue-400",
      glow: "hover:border-blue-500/40",
    },
    amber: {
      bg: "from-amber-500/10 to-yellow-500/5",
      border: "border-amber-500/20",
      text: "text-amber-400",
      iconBg: "bg-amber-500/20 text-amber-400",
      glow: "hover:border-amber-500/40",
    },
    purple: {
      bg: "from-purple-500/10 to-violet-500/5",
      border: "border-purple-500/20",
      text: "text-purple-400",
      iconBg: "bg-purple-500/20 text-purple-400",
      glow: "hover:border-purple-500/40",
    },
  };

  const c = colorMap[color];

  return (
    <div
      className={`relative overflow-hidden rounded-2xl p-5 border bg-gradient-to-br ${c.bg} ${c.border} ${c.glow} transition-all duration-300 shadow-sm`}
    >
      <div className="flex items-center justify-between">
        <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">{title}</span>
        <div className={`p-2.5 rounded-xl ${c.iconBg}`}>
          <Icon className="h-5 w-5" />
        </div>
      </div>

      <div className="mt-4 flex items-baseline justify-between">
        <span className="text-3xl font-bold text-white tracking-tight">{value}</span>
        {trend && <span className="text-xs font-medium text-slate-400">{trend}</span>}
      </div>

      {subtitle && <p className="mt-1 text-xs text-slate-400 truncate">{subtitle}</p>}
    </div>
  );
};
