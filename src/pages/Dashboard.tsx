import React from 'react';
import { useApi } from '../hooks/useApi';
import { RankingTable } from '../components/RankingTable';
import { TerminalSquare } from 'lucide-react';

export const Dashboard: React.FC = () => {
  const [timeframe, setTimeframe] = React.useState('24h');
  
  const { data: repos, loading } = useApi<any[]>(`/rankings/stars?tf=${timeframe}`, 10000, [timeframe]);
  const { data: status } = useApi<any>('/status', 5000);

  const timeframes = [
    { id: '24h', label: 'Daily' },
    { id: '7d', label: 'Weekly' },
    { id: '1m', label: '1 Month' },
    { id: '2m', label: '2 Months' },
    { id: '3m', label: '3 Months' },
    { id: '6m', label: '6 Months' },
    { id: '1y', label: '1 Year' },
    { id: '2y', label: '2 Years' },
    { id: '3y', label: '3 Years' },
    { id: '5y', label: '5 Years' },
    { id: 'all', label: 'All Time' },
  ];

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-8 gap-4">
        <div className="flex items-center gap-4">
          <TerminalSquare size={40} className="text-primary" />
          <div>
            <h1 className="text-4xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-primary to-secondary">
              GitHub LiveRank
            </h1>
            <p className="text-textMuted mt-1">Real-Time GitHub Intelligence Terminal</p>
          </div>
        </div>
        
        {/* Status indicator */}
        <div className="glass-panel px-4 py-2 rounded-full flex items-center gap-3 text-sm">
          <div className="flex items-center gap-2">
            <span className={`w-2.5 h-2.5 rounded-full ${status?.status === 'healthy' ? 'bg-emerald-500 animate-pulse' : 'bg-red-500'}`}></span>
            <span className="font-medium">{status?.status === 'healthy' ? 'LIVE' : 'ERROR'}</span>
          </div>
          <div className="h-4 w-px bg-borderLight"></div>
          <span className="text-slate-400">Tracking: <strong className="text-slate-200">{status?.repositories_tracked || 0}</strong></span>
          <div className="h-4 w-px bg-borderLight"></div>
          <span className="text-slate-400">Last update: {status?.last_collection ? new Date(status.last_collection).toLocaleTimeString() : 'N/A'}</span>
        </div>
      </div>

      {/* Controls */}
      <div className="flex flex-col sm:flex-row justify-end items-center gap-4 mb-6 border-b border-borderLight/50 pb-2">
        <div className="flex items-center gap-2 self-end px-1 w-full sm:w-auto">
          <label htmlFor="timeframe" className="text-sm text-textMuted font-medium whitespace-nowrap">Timeframe:</label>
          <select 
            id="timeframe"
            value={timeframe}
            onChange={(e) => setTimeframe(e.target.value)}
            className="bg-slate-800 border border-borderLight text-textMain text-sm rounded-lg focus:ring-primary focus:border-primary block w-full p-2"
          >
            {timeframes.map(tf => (
              <option key={tf.id} value={tf.id}>{tf.label}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Main Content */}
      <div className="animate-in fade-in slide-in-from-bottom-4 duration-500">
        <RankingTable repos={repos || []} loading={loading} />
      </div>
    </div>
  );
};
