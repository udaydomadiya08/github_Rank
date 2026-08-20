import React, { useState } from 'react';
import { TrendIndicator } from './TrendIndicator';
import { ArrowUpDown, ExternalLink } from 'lucide-react';

interface Repo {
  id: string;
  full_name: string;
  name: string;
  owner: string;
  description: string;
  html_url: string;
  language: string;
  stars: number;
  forks: number;
  velocity: number;
  acceleration: number;
  momentum: number;
  insufficient_data: boolean;
  is_estimate: boolean;
}

interface RankingTableProps {
  repos: Repo[];
  loading?: boolean;
}

export const RankingTable: React.FC<RankingTableProps> = ({ repos, loading }) => {
  const [sortField, setSortField] = useState<keyof Repo>('stars');
  const [sortDesc, setSortDesc] = useState(true);
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 50;

  const handleSort = (field: keyof Repo) => {
    if (sortField === field) {
      setSortDesc(!sortDesc);
    } else {
      setSortField(field);
      setSortDesc(true);
    }
    setCurrentPage(1); // Reset to first page on sort
  };

  const sortedRepos = [...repos].sort((a, b) => {
    let aVal = a[sortField];
    let bVal = b[sortField];
    
    if (typeof aVal === 'string' && typeof bVal === 'string') {
      return sortDesc ? bVal.localeCompare(aVal) : aVal.localeCompare(bVal);
    }
    
    if (typeof aVal === 'number' && typeof bVal === 'number') {
      return sortDesc ? bVal - aVal : aVal - bVal;
    }
    
    return 0;
  });

  const totalPages = Math.ceil(sortedRepos.length / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const paginatedRepos = sortedRepos.slice(startIndex, startIndex + itemsPerPage);

  if (loading) {
    return (
      <div className="w-full flex justify-center py-12">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
      </div>
    );
  }

  return (
    <div className="w-full flex flex-col gap-4">
      <div className="w-full overflow-x-auto card">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="bg-slate-800/50 text-textMuted text-sm border-b border-borderLight uppercase">
              <th className="p-4 font-medium">Rank</th>
              <th className="p-4 font-medium cursor-pointer hover:text-textMain" onClick={() => handleSort('name')}>
                <div className="flex items-center gap-1">Repository <ArrowUpDown size={14} /></div>
              </th>
              <th className="p-4 font-medium cursor-pointer hover:text-textMain" onClick={() => handleSort('stars')}>
                <div className="flex items-center gap-1">Stars <ArrowUpDown size={14} /></div>
              </th>
              <th className="p-4 font-medium cursor-pointer hover:text-textMain" onClick={() => handleSort('velocity')}>
                <div className="flex items-center gap-1">Growth <ArrowUpDown size={14} /></div>
              </th>
              <th className="p-4 font-medium cursor-pointer hover:text-textMain" onClick={() => handleSort('momentum')}>
                <div className="flex items-center gap-1">Momentum <ArrowUpDown size={14} /></div>
              </th>
              <th className="p-4 font-medium hidden md:table-cell">Trend</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-borderLight/50">
            {paginatedRepos.map((repo, idx) => (
              <tr key={repo.id} className="table-row-hover text-sm">
                <td className="p-4 font-semibold text-slate-400">#{startIndex + idx + 1}</td>
                <td className="p-4">
                  <div>
                    <a href={repo.html_url} target="_blank" rel="noreferrer" className="font-bold text-primary hover:underline inline-flex items-center gap-1">
                      {repo.owner}/{repo.name} <ExternalLink size={12} />
                    </a>
                    <p className="text-xs text-textMuted mt-1 line-clamp-1 max-w-[300px]" title={repo.description}>{repo.description}</p>
                    {repo.language && (
                      <span className="badge mt-2 inline-block bg-slate-700/50 text-slate-300">{repo.language}</span>
                    )}
                  </div>
                </td>
                <td className="p-4 font-medium text-slate-200">
                  {repo.stars.toLocaleString()}
                </td>
                <td className="p-4">
                  {repo.insufficient_data ? (
                    <span className="text-slate-500 text-xs italic">Not enough data</span>
                  ) : <div className="flex flex-col">
                        <span className={(repo.velocity || 0) > 0 ? "text-green-400 font-medium" : (repo.velocity || 0) < 0 ? "text-red-400 font-medium" : "text-slate-400"}>
                          {(repo.velocity || 0) > 0 ? '+' : ''}{(repo.velocity || 0).toFixed(1)}
                        </span>
                        {repo.is_estimate && <span className="text-[10px] text-slate-500 uppercase tracking-wide">Estimate</span>}
                      </div>
                  }
                </td>
                <td className="p-4">
                  {repo.insufficient_data ? (
                    <span className="text-slate-500 text-xs">-</span>
                  ) : (
                    <div className="flex items-center gap-2">
                      <span className="font-bold">{(repo.momentum || 0).toFixed(1)}</span>
                      <div className="w-16 h-1.5 bg-slate-700 rounded-full overflow-hidden hidden lg:block">
                        <div className="h-full bg-primary" style={{ width: `${repo.momentum || 0}%` }} />
                      </div>
                    </div>
                  )}
                </td>
                <td className="p-4 hidden md:table-cell">
                  {repo.insufficient_data ? null : (
                    <TrendIndicator velocity={repo.velocity || 0} momentum={repo.momentum || 0} acceleration={repo.acceleration || 0} />
                  )}
                </td>
              </tr>
            ))}
            {sortedRepos.length === 0 && (
              <tr>
                <td colSpan={6} className="p-8 text-center text-textMuted">No repositories found.</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
      
      {totalPages > 1 && (
        <div className="flex items-center justify-between px-4 py-3 sm:px-6 card bg-slate-800/30">
          <div className="hidden sm:flex-1 sm:flex sm:items-center sm:justify-between">
            <div>
              <p className="text-sm text-textMuted">
                Showing <span className="font-medium text-textMain">{startIndex + 1}</span> to <span className="font-medium text-textMain">{Math.min(startIndex + itemsPerPage, sortedRepos.length)}</span> of <span className="font-medium text-textMain">{sortedRepos.length}</span> results
              </p>
            </div>
            <div>
              <nav className="relative z-0 inline-flex rounded-md shadow-sm -space-x-px" aria-label="Pagination">
                <button
                  onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
                  disabled={currentPage === 1}
                  className="relative inline-flex items-center px-2 py-2 rounded-l-md border border-borderLight bg-slate-800 text-sm font-medium text-textMuted hover:bg-slate-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  <span className="sr-only">Previous</span>
                  Previous
                </button>
                <div className="flex items-center px-4 py-2 border-y border-borderLight bg-slate-800 text-sm font-medium text-textMain">
                  Page {currentPage} of {totalPages}
                </div>
                <button
                  onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
                  disabled={currentPage === totalPages}
                  className="relative inline-flex items-center px-2 py-2 rounded-r-md border border-borderLight bg-slate-800 text-sm font-medium text-textMuted hover:bg-slate-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  <span className="sr-only">Next</span>
                  Next
                </button>
              </nav>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
