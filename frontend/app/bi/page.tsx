// app/bi/page.tsx
'use client';
import { useState, useEffect } from 'react';
import { analyzeBI, getBIReport, getIndustries, getRegions, checkHealth, type BIReport } from '@/lib/api';
import { Upload, BarChart3, TrendingUp, Building2, Globe, FileText, AlertCircle, CheckCircle, Loader2, Sparkles, Target, Download } from 'lucide-react';
//import { Download } from "lucide-react";

function cleanMarkdown(text: string): string {
  if (!text || typeof text !== 'string') return text || '';
  let cleaned = text
    .replace(/```[\s\S]*?```/g, '')
    .replace(/`([^`]+)`/g, '$1')
    .replace(/\*\*([^*]+)\*\*/g, '$1')
    .replace(/__([^_]+)__/g, '$1')
    .replace(/\*([^*]+)\*/g, '$1')
    .replace(/_([^_]+)_/g, '$1')
    .replace(/^#{1,6}\s*/gm, '')
    .replace(/^>\s*/gm, '')
    .replace(/^[-*_]{3,}$/gm, '')
    .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1')
    .replace(/!\[([^\]]*)\]\([^)]+\)/g, '')
    .replace(/\n{3,}/g, '\n\n')
    .trim();
  return cleaned;
}

function safeParse(value: any): any {
  if (value === null || value === undefined) return value;
  if (typeof value !== 'string') return value;
  try {
    const cleaned = value.replace(/```json|```/g, '').trim();
    return JSON.parse(cleaned);
  } catch {
    return cleanMarkdown(value);
  }
}

function renderValue(value: any): string {
  if (value === null || value === undefined) return '';
  if (typeof value === 'string') return cleanMarkdown(value);
  if (Array.isArray(value)) return value.map(renderValue).filter(Boolean).join('\n');
  if (typeof value === 'object') {
    const text = Object.values(value).filter(v => typeof v === 'string').join(' ');
    return cleanMarkdown(text);
  }
  return String(value);
}

// ==================== DECORATIVE COMPONENTS ====================

// 1. Enhanced Section Heading
const SectionHeading = ({ icon: Icon, title, subtitle }: { icon: any, title: string, subtitle?: string }) => (
  <div className="mb-6">
    <div className="flex items-center gap-3 mb-2">
      <div className="p-2 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg shadow-lg">
        <Icon size={20} className="text-white" />
      </div>
      <h2 className="text-2xl font-bold bg-gradient-to-r from-gray-900 to-gray-600 bg-clip-text text-transparent">
        {title}
      </h2>
    </div>
    {subtitle && <p className="text-gray-600 ml-14">{subtitle}</p>}
    <div className="h-1 w-full bg-gradient-to-r from-blue-500 via-purple-500 to-pink-500 rounded-full mt-3" />
  </div>
);

// 2. Enhanced KPI Table
const KPITable = ({ data }: { data: any[] }) => (
  <div className="bg-white rounded-2xl shadow-lg border border-gray-200 overflow-hidden mb-6">
    <div className="bg-gradient-to-r from-blue-600 to-purple-600 px-6 py-4">
      <h3 className="text-lg font-semibold text-white flex items-center gap-2">
        <TrendingUp size={20} />
        Key Performance Indicators
      </h3>
    </div>
    <div className="overflow-x-auto">
      <table className="w-full">
        <thead className="bg-gray-50 border-b border-gray-200">
          <tr>
            <th className="px-6 py-4 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">KPI</th>
            <th className="px-6 py-4 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">Current Value</th>
            <th className="px-6 py-4 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">Target Value</th>
            <th className="px-6 py-4 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">Growth Rate</th>
            <th className="px-6 py-4 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">Progress</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-200">
          {data.map((row, idx) => {
            const current = parseFloat(String(row.current).replace(/[^0-9.]/g, ''));
            const target = parseFloat(String(row.target).replace(/[^0-9.]/g, ''));
            const progress = target > 0 ? Math.min((current / target) * 100, 100) : 0;
            const progressColor = progress >= 80 ? 'bg-emerald-500' : progress >= 50 ? 'bg-amber-500' : 'bg-rose-500';
            
            return (
              <tr key={idx} className="hover:bg-gray-50 transition">
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="flex items-center gap-2">
                    <div className={`w-2 h-2 rounded-full ${progressColor}`} />
                    <span className="font-medium text-gray-900">{row.kpi}</span>
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-semibold bg-blue-100 text-blue-800">
                    {row.current}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-semibold bg-purple-100 text-purple-800">
                    {row.target}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-semibold ${
                    parseFloat(String(row.growth).replace(/[^0-9.-]/g, '')) >= 0 
                      ? 'bg-emerald-100 text-emerald-800' 
                      : 'bg-rose-100 text-rose-800'
                  }`}>
                    {row.growth}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="w-full max-w-[120px]">
                    <div className="flex justify-between text-xs mb-1">
                      <span className="text-gray-600">{Math.round(progress)}%</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div className={`${progressColor} h-2 rounded-full transition-all duration-500`} style={{ width: `${progress}%` }} />
                    </div>
                  </div>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  </div>
);

// 3. Stats Grid Cards
const StatsGrid = ({ stats }: { stats: any[] }) => (
  <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
    {stats.map((stat, idx) => (
      <div key={idx} className="bg-gradient-to-br from-white to-gray-50 rounded-xl p-5 border border-gray-200 shadow-md hover:shadow-lg transition">
        <div className="flex items-center justify-between mb-3">
          <span className="text-sm font-medium text-gray-600">{stat.label}</span>
          <div className={`p-2 rounded-lg ${stat.iconBg || 'bg-blue-100'}`}>
            {stat.icon}
          </div>
        </div>
        <div className="text-2xl font-bold text-gray-900 mb-1">{stat.value}</div>
        {stat.change !== undefined && (
          <div className={`text-sm font-medium ${stat.change >= 0 ? 'text-emerald-600' : 'text-rose-600'}`}>
            {stat.change >= 0 ? '↑' : '↓'} {Math.abs(stat.change)}%
          </div>
        )}
      </div>
    ))}
  </div>
);

// 4. Comparison Section
const ComparisonSection = ({ title, marketData, internalData }: { title: string, marketData: any, internalData: any }) => (
  <div className="bg-white rounded-2xl shadow-lg border border-gray-200 p-6 mb-6">
    <h3 className="text-xl font-bold text-gray-900 mb-6 flex items-center gap-2">
      <div className="p-2 bg-gradient-to-br from-amber-400 to-orange-500 rounded-lg">
        <BarChart3 size={18} className="text-white" />
      </div>
      {title}
    </h3>
    <div className="grid md:grid-cols-2 gap-6">
      <div className="p-5 bg-gradient-to-br from-blue-50 to-indigo-50 rounded-xl border border-blue-200">
        <div className="flex items-center gap-2 mb-4">
          <Globe size={18} className="text-blue-600" />
          <h4 className="font-semibold text-blue-900">Market Average</h4>
        </div>
        <div className="space-y-3">
          {Object.entries(marketData).map(([key, value]: [string, any]) => (
            <div key={key} className="flex justify-between items-center">
              <span className="text-sm text-blue-700">{key}</span>
              <span className="font-semibold text-blue-900">{value}</span>
            </div>
          ))}
        </div>
      </div>
      <div className="p-5 bg-gradient-to-br from-emerald-50 to-teal-50 rounded-xl border border-emerald-200">
        <div className="flex items-center gap-2 mb-4">
          <Building2 size={18} className="text-emerald-600" />
          <h4 className="font-semibold text-emerald-900">Our Performance</h4>
        </div>
        <div className="space-y-3">
          {Object.entries(internalData).map(([key, value]: [string, any]) => (
            <div key={key} className="flex justify-between items-center">
              <span className="text-sm text-emerald-700">{key}</span>
              <span className="font-semibold text-emerald-900">{value}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  </div>
);

// 5. Insight Card
const InsightCard = ({ number, title, content, type = 'neutral' }: { number: number, title: string, content: string, type?: 'positive' | 'negative' | 'neutral' | 'warning' }) => {
  const styles = {
    positive: { bg: 'from-emerald-50 to-green-50', border: 'border-emerald-200', icon: '📈', numberBg: 'bg-emerald-500' },
    negative: { bg: 'from-rose-50 to-red-50', border: 'border-rose-200', icon: '📉', numberBg: 'bg-rose-500' },
    warning: { bg: 'from-amber-50 to-orange-50', border: 'border-amber-200', icon: '⚠️', numberBg: 'bg-amber-500' },
    neutral: { bg: 'from-blue-50 to-indigo-50', border: 'border-blue-200', icon: '💡', numberBg: 'bg-blue-500' },
  };
  const style = styles[type];
  
  return (
    <div className={`p-5 rounded-xl border ${style.border} bg-gradient-to-br ${style.bg} hover:shadow-md transition`}>
      <div className="flex items-start gap-4">
        <div className="flex-shrink-0">
          <div className={`${style.numberBg} text-white w-10 h-10 rounded-xl flex items-center justify-center font-bold text-lg shadow-lg`}>
            {number}
          </div>
        </div>
        <div className="flex-1">
          <h4 className="font-semibold text-gray-900 mb-2 flex items-center gap-2">
            <span>{style.icon}</span>
            {title}
          </h4>
          <p className="text-sm text-gray-700 leading-relaxed">{content}</p>
        </div>
      </div>
    </div>
  );
};

// 6. Parse KPI table from markdown text
function extractKPITable(content: string): any[] {
  const kpiPattern = /\|\s*KPI\s*\|\s*Current Value\s*\|\s*Target Value\s*\|\s*Growth Rate\s*\|([\s\S]*?)(?=\n\n|\n\|---)/i;
  const match = content.match(kpiPattern);
  if (!match) return [];
  
  const rows = match[1].trim().split('\n').filter(line => line.includes('|') && !line.includes('---'));
  return rows.map(row => {
    const cells = row.split('|').map(cell => cell.trim()).filter(cell => cell);
    if (cells.length >= 4) {
      return { kpi: cells[0], current: cells[1], target: cells[2], growth: cells[3] };
    }
    return null;
  }).filter(Boolean);
}

// 7. Parse numbered insights from content
function extractInsights(content: string): Array<{number: number, title: string, content: string}> {
  const insightPattern = /(\d+)\.\s*([A-Z][^:]+):\s*([^.\n]+(?:\.[^.\n]+)*)/g;
  const insights = [];
  let match;
  while ((match = insightPattern.exec(content)) !== null) {
    insights.push({ number: parseInt(match[1]), title: match[2], content: match[3] });
  }
  return insights;
}

// ==================== MAIN COMPONENT ====================

export default function BIPage() {
  const [industry, setIndustry] = useState('Electric Vehicles');
  const [region, setRegion] = useState('Europe');
  const [query, setQuery] = useState('Analyze market opportunities and competitive landscape');
  const [competitors, setCompetitors] = useState('');
  const [files, setFiles] = useState<File[]>([]);
  const [workflow, setWorkflow] = useState('sequential');
  
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [report, setReport] = useState<BIReport | null>(null);
  const [backendConnected, setBackendConnected] = useState(false);

  useEffect(() => {
    const init = async () => {
      try {
        const [indList, regList, healthy] = await Promise.all([
          getIndustries(),
          getRegions(),
          checkHealth()
        ]);
        if (indList.length > 0 && !indList.includes(industry)) setIndustry(indList[0]);
        if (regList.length > 0 && !regList.includes(region)) setRegion(regList[0]);
        setBackendConnected(healthy);
      } catch (err) {
        console.error('Init failed:', err);
        setBackendConnected(false);
      }
    };
    init();
  }, []);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) setFiles(Array.from(e.target.files));
  };

  const handleAnalyze = async () => {
    if (!industry || !region) { setError('Please select industry and region'); return; }
    setLoading(true);
    setError(null);
    setReport(null);
    try {
      const result = await analyzeBI({
        query, industry, region,
        competitors: competitors || undefined,
        workflow,
        files: files.length > 0 ? files : undefined
      });
      const fullReport = await getBIReport(result.report_id);
      setReport(fullReport);
    } catch (err: any) {
      setError(err.message || 'Analysis failed');
    } finally {
      setLoading(false);
    }
  };

  // ... (keep your existing renderSWOT, renderRecommendations, renderTrends, renderValidation functions)
  // I'll show you where to use the new components in the return statement below

  const renderSWOT = (rawSwot: any) => {
    const swot = safeParse(rawSwot);
    if (!swot || typeof swot !== 'object' || Array.isArray(swot)) {
      return (
        <div className="prose prose-sm max-w-none text-gray-700">
          <p className="whitespace-pre-wrap">{renderValue(rawSwot)}</p>
        </div>
      );
    }
    const quadrants = [
      { key: 'strengths', label: 'Strengths', icon: '💪', color: 'emerald', desc: 'Internal advantages' },
      { key: 'weaknesses', label: 'Weaknesses', icon: '⚠️', color: 'rose', desc: 'Areas to improve' },
      { key: 'opportunities', label: 'Opportunities', icon: '🚀', color: 'blue', desc: 'External possibilities' },
      { key: 'threats', label: 'Threats', icon: '🛡️', color: 'amber', desc: 'External challenges' },
    ];
    return (
      <div className="grid md:grid-cols-2 gap-4">
        {quadrants.map(({ key, label, icon, color, desc }) => {
          const items = Array.isArray(swot[key]) ? swot[key] : [swot[key]].filter(Boolean);
          const bgClass = `bg-${color}-50 border-${color}-200`;
          const textClass = `text-${color}-800`;
          const dotClass = `bg-${color}-500`;
          return (
            <div key={key} className={`p-4 rounded-xl border ${bgClass} transition hover:shadow-md`}>
              <div className="flex items-center gap-2 mb-3">
                <span className="text-xl">{icon}</span>
                <div>
                  <h4 className={`font-semibold ${textClass}`}>{label}</h4>
                  <p className={`text-xs text-${color}-600`}>{desc}</p>
                </div>
              </div>
              <ul className="space-y-2">
                {items.map((item: any, i: number) => (
                  <li key={i} className="flex gap-2 text-sm text-gray-700">
                    <span className={`mt-1.5 w-1.5 h-1.5 rounded-full ${dotClass} flex-shrink-0`} />
                    <span>{renderValue(item)}</span>
                  </li>
                ))}
                {items.length === 0 && <li className="text-sm text-gray-400 italic">No items listed</li>}
              </ul>
            </div>
          );
        })}
      </div>
    );
  };

  const renderRecommendations = (strategy: any) => {
    const recs = safeParse(strategy?.recommendations);
    if (!recs) return null;
    if (typeof recs === 'string') {
      return <p className="text-sm text-gray-700 whitespace-pre-wrap">{cleanMarkdown(recs)}</p>;
    }
    const list: any[] = Array.isArray(recs) ? recs : Object.values(recs).filter(v => v && typeof v === 'object');
    if (list.length === 0) return null;
    
    return (
      <div className="space-y-3">
        {list.map((rec: any, i: number) => {
          const impact = rec.expected_impact?.toLowerCase() || 'medium';
          const impactStyles: Record<string, string> = {
            high: 'bg-emerald-100 text-emerald-800 border-emerald-200',
            medium: 'bg-amber-100 text-amber-800 border-amber-200',
            low: 'bg-gray-100 text-gray-700 border-gray-200',
          };
          return (
            <div key={i} className="border-l-4 border-blue-500 pl-4 py-3 bg-gradient-to-r from-blue-50/50 to-white rounded-r-lg shadow-sm">
              <div className="flex flex-wrap justify-between items-start gap-2">
                <h4 className="font-semibold text-gray-900">{rec.title || `Recommendation ${i + 1}`}</h4>
                <span className={`text-xs px-2.5 py-1 rounded-full border font-medium ${impactStyles[impact] || impactStyles.medium}`}>
                  {impact.charAt(0).toUpperCase() + impact.slice(1)} Impact
                </span>
              </div>
              <p className="text-sm text-gray-600 mt-2 leading-relaxed">{cleanMarkdown(rec.description || '')}</p>
              <div className="flex flex-wrap gap-3 mt-3 text-xs text-gray-500">
                {rec.timeline && (
                  <span className="flex items-center gap-1">
                    <span className="w-1.5 h-1.5 rounded-full bg-blue-400" />
                    {rec.timeline}
                  </span>
                )}
                {rec.effort_required && (
                  <span className="flex items-center gap-1">
                    <span className="w-1.5 h-1.5 rounded-full bg-purple-400" />
                    {rec.effort_required} effort
                  </span>
                )}
              </div>
            </div>
          );
        })}
      </div>
    );
  };

  const renderTrends = (rawTrends: any) => {
    const trends = safeParse(rawTrends);
    if (!trends) return null;
    if (typeof trends === 'string') {
      return <p className="text-sm text-gray-700 whitespace-pre-wrap">{cleanMarkdown(trends)}</p>;
    }
    const list: any[] = Array.isArray(trends) ? trends : Object.values(trends).filter(v => v);
    if (list.length === 0) return null;
    
    return (
      <ul className="space-y-3">
        {list.map((trend: any, i: number) => {
          const name = trend.name || trend.trend_name || (typeof trend === 'string' ? trend : `Trend ${i + 1}`);
          const trajectory = trend.growth_trajectory?.toLowerCase() || 'stable';
          const trajStyles: Record<string, string> = {
            accelerating: 'bg-emerald-100 text-emerald-700 border-emerald-200',
            growing: 'bg-blue-100 text-blue-700 border-blue-200',
            stable: 'bg-gray-100 text-gray-600 border-gray-200',
            declining: 'bg-rose-100 text-rose-700 border-rose-200',
          };
          return (
            <li key={i} className="flex gap-3 p-3 rounded-lg bg-gray-50 hover:bg-gray-100 transition">
              <span className="text-blue-500 mt-1 flex-shrink-0">→</span>
              <div className="flex-1 min-w-0">
                <div className="flex flex-wrap items-center gap-2">
                  <strong className="text-gray-900">{cleanMarkdown(String(name))}</strong>
                  {trajectory && (
                    <span className={`text-xs px-2 py-0.5 rounded border font-medium ${trajStyles[trajectory] || trajStyles.stable}`}>
                      {trajectory.charAt(0).toUpperCase() + trajectory.slice(1)}
                    </span>
                  )}
                </div>
                {trend.evidence && <p className="text-sm text-gray-600 mt-1">{cleanMarkdown(String(trend.evidence))}</p>}
                {trend.description && <p className="text-sm text-gray-500 mt-1 italic">{cleanMarkdown(String(trend.description))}</p>}
              </div>
            </li>
          );
        })}
      </ul>
    );
  };

  const renderValidation = (validation: any) => {
    if (!validation?.validation_summary) return null;
    const confidence = validation.final_confidence || validation.overall_confidence || 0;
    const status = confidence > 0.8 ? 'good' : confidence > 0.6 ? 'caution' : 'warning';
    const statusStyles = {
      good: 'bg-emerald-50 border-emerald-200 text-emerald-800',
      caution: 'bg-amber-50 border-amber-200 text-amber-800',
      warning: 'bg-rose-50 border-rose-200 text-rose-800',
    };
    const icons = { good: '✅', caution: '⚠️', warning: '❗' };
    
    return (
      <div className={`rounded-xl border p-4 ${statusStyles[status]}`}>
        <div className="flex items-start gap-3">
          <span className="text-xl">{icons[status]}</span>
          <div>
            <h4 className="font-semibold mb-1">Validation Summary</h4>
            <p className="text-sm opacity-90 whitespace-pre-wrap">{cleanMarkdown(validation.validation_summary)}</p>
            {validation.key_concerns && (
              <details className="mt-2 text-sm">
                <summary className="cursor-pointer font-medium hover:underline">Key Concerns ({Array.isArray(validation.key_concerns) ? validation.key_concerns.length : 1})</summary>
                <ul className="mt-2 space-y-1 pl-4 list-disc">
                  {(Array.isArray(validation.key_concerns) ? validation.key_concerns : [validation.key_concerns]).map((c: any, i: number) => (
                    <li key={i} className="opacity-90">{cleanMarkdown(String(c))}</li>
                  ))}
                </ul>
              </details>
            )}
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-50 to-white">
      {/* Header */}
      <header className="bg-white/80 backdrop-blur-sm border-b sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-6 py-4 flex justify-between items-center">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-blue-600 rounded-xl">
              <BarChart3 className="text-white" size={24} />
            </div>
            <h1 className="text-2xl font-bold bg-gradient-to-r from-gray-900 to-gray-600 bg-clip-text text-transparent">
              Business Intelligence
            </h1>
          </div>
          <div className={`flex items-center gap-2 text-sm font-medium px-3 py-1.5 rounded-full border ${
            backendConnected 
              ? 'bg-emerald-50 border-emerald-200 text-emerald-700' 
              : 'bg-rose-50 border-rose-200 text-rose-700'
          }`}>
            {backendConnected ? <CheckCircle size={14} /> : <AlertCircle size={14} />}
            {backendConnected ? 'Backend Connected' : 'Backend Disconnected'}
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto p-6 space-y-6">
        {/* Input Form - Keep your existing form code */}
        <section className="bg-white rounded-2xl shadow-sm border p-6">
          <h2 className="text-lg font-semibold mb-5 flex items-center gap-2 text-gray-900">
            <Sparkles size={20} className="text-blue-600" />
            Market Analysis Setup
          </h2>
          
          <div className="grid md:grid-cols-2 gap-4 mb-5">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">Industry</label>
              <select 
                value={industry} 
                onChange={(e) => setIndustry(e.target.value)}
                className="w-full border border-gray-300 rounded-xl p-2.5 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition bg-white"
              >
                <option>Electric Vehicles</option>
                <option>Fintech</option>
                <option>SaaS</option>
                <option>Healthcare AI</option>
                <option>Renewable Energy</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">Region</label>
              <select 
                value={region} 
                onChange={(e) => setRegion(e.target.value)}
                className="w-full border border-gray-300 rounded-xl p-2.5 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition bg-white"
              >
                <option>Global</option>
                <option>North America</option>
                <option>Europe</option>
                <option>Asia Pacific</option>
                <option>United States</option>
              </select>
            </div>
          </div>

          <div className="mb-5">
            <label className="block text-sm font-medium text-gray-700 mb-1.5">Analysis Query</label>
            <textarea 
              value={query} 
              onChange={(e) => setQuery(e.target.value)} 
              rows={3}
              className="w-full border border-gray-300 rounded-xl p-3 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition resize-none"
              placeholder="What would you like to analyze?" 
            />
          </div>

          <div className="mb-5">
            <label className="block text-sm font-medium text-gray-700 mb-1.5">Competitors (optional)</label>
            <input 
              type="text" 
              value={competitors} 
              onChange={(e) => setCompetitors(e.target.value)}
              className="w-full border border-gray-300 rounded-xl p-2.5 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition"
              placeholder="e.g., Tesla, BYD, Stripe" 
            />
          </div>

          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-2">Upload Internal Data</label>
            <div className="border-2 border-dashed border-gray-300 rounded-xl p-6 text-center hover:border-blue-400 hover:bg-blue-50/30 transition cursor-pointer group">
              <input 
                type="file" 
                multiple 
                accept=".csv,.xlsx,.xls,.json,.pdf"
                onChange={handleFileChange} 
                className="hidden" 
                id="file-upload" 
              />
              <label htmlFor="file-upload" className="cursor-pointer flex flex-col items-center gap-3">
                <div className="p-3 bg-gray-100 rounded-xl group-hover:bg-blue-100 transition">
                  <Upload size={24} className="text-gray-500 group-hover:text-blue-600 transition" />
                </div>
                <div>
                  <span className="text-sm font-medium text-gray-700">
                    {files.length > 0 ? `${files.length} file(s) selected` : 'Click to upload CSV, Excel, or JSON'}
                  </span>
                  <p className="text-xs text-gray-500 mt-1">Max 10MB per file</p>
                </div>
                {files.length > 0 && (
                  <ul className="text-xs text-gray-600 mt-3 space-y-1">
                    {files.map((f, i) => (
                      <li key={i} className="flex items-center gap-2">
                        <FileText size={12} />
                        {f.name}
                      </li>
                    ))}
                  </ul>
                )}
              </label>
            </div>
          </div>

          {error && (
            <div className="mb-5 p-3 bg-rose-50 border border-rose-200 rounded-xl text-rose-700 text-sm flex items-start gap-2">
              <AlertCircle size={16} className="mt-0.5 flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <button 
            onClick={handleAnalyze} 
            disabled={loading || !backendConnected}
            className="w-full bg-gradient-to-r from-blue-600 to-blue-700 text-white py-3.5 rounded-xl font-medium hover:from-blue-700 hover:to-blue-800 disabled:from-gray-400 disabled:to-gray-500 disabled:cursor-not-allowed flex items-center justify-center gap-2 transition shadow-sm hover:shadow"
          >
            {loading
              ? <><Loader2 className="animate-spin" size={20} /> Analyzing market data...</>
              : <><TrendingUp size={20} /> Start Intelligence Analysis</>}
          </button>
        </section>

        {/* Loading State */}
        {loading && !report && (
          <div className="bg-white rounded-2xl shadow-sm border p-10 text-center">
            <div className="relative mx-auto mb-6">
              <Loader2 className="animate-spin text-blue-600" size={40} />
              <Sparkles className="absolute -top-1 -right-1 text-amber-400 animate-pulse" size={16} />
            </div>
            <p className="text-gray-700 font-medium">Running multi-agent analysis...</p>
            <div className="flex flex-wrap justify-center gap-2 mt-4 text-xs text-gray-500">
              {['Industry', 'Competitors', 'Trends', 'Synthesis', 'Strategy', 'Validation'].map((step, i) => (
                <span key={i} className="px-2.5 py-1 bg-gray-100 rounded-full animate-pulse" style={{ animationDelay: `${i * 100}ms` }}>
                  {step}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Report Display - HERE'S WHERE YOU USE THE NEW COMPONENTS */}
        {report && (
          <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
            {/* Executive Summary */}
            <section className="bg-white rounded-2xl shadow-sm border overflow-hidden">
              <div className="bg-gradient-to-r from-blue-600 to-indigo-600 px-6 py-4">
                <h2 className="text-lg font-semibold text-white flex items-center gap-2">
                  <FileText size={20} />
                  Executive Summary
                </h2>
              </div>
              <div className="p-6">
                <p className="text-gray-700 leading-relaxed whitespace-pre-wrap">
                  {cleanMarkdown(report.executive_summary || '')}
                </p>
                <div className="mt-5 flex flex-wrap gap-2">
                  <span className={`px-3 py-1.5 rounded-full text-sm font-medium border ${
                    (report.metadata?.overall_confidence || 0) > 0.8 
                      ? 'bg-emerald-50 border-emerald-200 text-emerald-700' 
                      : (report.metadata?.overall_confidence || 0) > 0.6 
                        ? 'bg-amber-50 border-amber-200 text-amber-700'
                        : 'bg-rose-50 border-rose-200 text-rose-700'
                  }`}>
                    Confidence: {Math.round((report.metadata?.overall_confidence || 0) * 100)}%
                  </span>
                  {report.metadata?.requires_human_review && (
                    <span className="px-3 py-1.5 rounded-full text-sm font-medium bg-amber-50 border border-amber-200 text-amber-700 flex items-center gap-1">
                      <AlertCircle size={12} /> Requires Review
                    </span>
                  )}
                  <span className="px-3 py-1.5 rounded-full text-sm text-gray-600 bg-gray-100 border">
                    {new Date(report.metadata?.generated_at || Date.now()).toLocaleString()}
                  </span>
                </div>
              </div>
            </section>

            {/* Market Overview - WITH NEW DECORATIVE COMPONENTS */}
            {report.market_overview?.content && cleanMarkdown(report.market_overview.content).trim() && (
              <section className="bg-white rounded-2xl shadow-sm border p-6">
                {/* ✅ USE SectionHeading HERE */}
                <SectionHeading 
                  icon={Globe} 
                  title="Market Overview" 
                  subtitle="Healthcare AI Market Analysis" 
                />
                
                {/* ✅ Extract and display KPI table if found in content */}
                {(() => {
                  const kpiData = extractKPITable(report.market_overview.content);
                  if (kpiData.length > 0) {
                    return <KPITable data={kpiData} />;
                  }
                  return null;
                })()}
                
                {/* ✅ Extract and display insights as cards */}
                {(() => {
                  const insights = extractInsights(report.market_overview.content);
                  if (insights.length > 0) {
                    return (
                      <div className="space-y-4">
                        {insights.map((insight, idx) => (
                          <InsightCard 
                            key={idx}
                            number={insight.number}
                            title={insight.title}
                            content={insight.content}
                            type={idx % 2 === 0 ? 'positive' : 'neutral'}
                          />
                        ))}
                      </div>
                    );
                  }
                  return null;
                })()}
                
                {/* ✅ Fallback to plain text if no structured data found */}
                <div className="prose prose-sm max-w-none text-gray-700 mt-6">
                  <p className="whitespace-pre-wrap leading-relaxed">
                    {cleanMarkdown(report.market_overview.content)}
                  </p>
                </div>
              </section>
            )}

            {/* Comparison Section - NEW */}
            {report.market_overview?.content && (
              <ComparisonSection 
                title="Comparison to Market Growth"
                marketData={{ 
                  'Growth Rate': '0%', 
                  'Market Size': '$0 (Est.)', 
                  'Trend': 'Stable' 
                }}
                internalData={{ 
                  'Growth Rate': '15%', 
                  'Revenue': '$10M', 
                  'Trend': 'Accelerating' 
                }}
              />
            )}

            {/* Competitive Landscape */}
            {report.competitive_landscape?.swot && (
              <section className="bg-white rounded-2xl shadow-sm border p-6">
                <SectionHeading 
                  icon={Building2} 
                  title="Competitive Landscape" 
                />
                {renderSWOT(report.competitive_landscape.swot)}
              </section>
            )}

            {/* Trend Analysis */}
            {report.trend_analysis?.emerging_trends && (
              <section className="bg-white rounded-2xl shadow-sm border p-6">
                <SectionHeading 
                  icon={TrendingUp} 
                  title="Emerging Trends" 
                />
                {renderTrends(report.trend_analysis.emerging_trends)}
              </section>
            )}

            {/* Strategic Recommendations */}
            {report.strategy?.recommendations && (
              <section className="bg-white rounded-2xl shadow-sm border p-6">
                <SectionHeading 
                  icon={Target} 
                  title="Strategic Recommendations" 
                />
                {renderRecommendations(report.strategy)}
              </section>
            )}

            {/* Validation */}
            {renderValidation(report.validation)}

            {/* Action Bar */}
            <div className="flex flex-wrap gap-3 pt-4">
              <button className="px-4 py-2.5 border border-gray-300 rounded-xl hover:bg-gray-50 text-sm font-medium transition flex items-center gap-2">
                <Download size={16} /> Export PDF
              </button>
              <button className="px-4 py-2.5 border border-gray-300 rounded-xl hover:bg-gray-50 text-sm font-medium transition flex items-center gap-2">
                <FileText size={16} /> Copy Summary
              </button>
              <button 
                onClick={() => setReport(null)} 
                className="px-4 py-2.5 bg-gray-900 text-white rounded-xl hover:bg-gray-800 text-sm font-medium transition flex items-center gap-2 ml-auto"
              >
                <Sparkles size={16} /> New Analysis
              </button>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}