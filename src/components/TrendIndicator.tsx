import React from 'react';
import { TrendingUp, TrendingDown, Zap, Sparkles, Activity } from 'lucide-react';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

interface TrendIndicatorProps {
  velocity: number;
  momentum: number;
  acceleration: number;
  className?: string;
}

export const TrendIndicator: React.FC<TrendIndicatorProps> = ({ velocity, momentum, acceleration, className }) => {
  if (momentum > 80 && acceleration > 0) {
    return (
      <div className={cn("flex items-center gap-1 text-red-500 font-semibold", className)}>
        <Sparkles size={16} /> <span title="Explosive Growth (High Momentum + Acceleration)">🔥 Explosive</span>
      </div>
    );
  }
  
  if (acceleration > 5) {
    return (
      <div className={cn("flex items-center gap-1 text-yellow-400 font-semibold", className)}>
        <Zap size={16} /> <span title="Strong Acceleration">⚡ Accelerating</span>
      </div>
    );
  }

  if (velocity > 10) {
    return (
      <div className={cn("flex items-center gap-1 text-green-400 font-semibold", className)}>
        <TrendingUp size={16} /> <span>🟢 Strong Growth</span>
      </div>
    );
  }

  if (velocity > 0) {
    return (
      <div className={cn("flex items-center gap-1 text-emerald-300", className)}>
        <Activity size={16} /> <span>🟡 Moderate Growth</span>
      </div>
    );
  }
  
  if (velocity < 0) {
    return (
      <div className={cn("flex items-center gap-1 text-red-400", className)}>
        <TrendingDown size={16} /> <span>🔴 Declining</span>
      </div>
    );
  }

  return <span className="text-slate-500">Stable</span>;
};
