import React, { useState, useEffect } from 'react';
import { Bot, RefreshCw, AlertCircle, FileText } from 'lucide-react';
import InvestmentAdvice from './InvestmentAdvice';
import PriceForecast from './PriceForecast';
import './styles.css';
import { aiAnalyze } from '../../api';

const AIReport = ({ reportId, currentPrice }) => {
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  // Load from local storage or fetch
  const cacheKey = `ai_report_${reportId}`;

  useEffect(() => {
    const cached = localStorage.getItem(cacheKey);
    if (cached) {
      try {
        setData(JSON.parse(cached));
      } catch (e) {
        localStorage.removeItem(cacheKey);
      }
    }
  }, [reportId]);

  const getAiConfig = () => {
    try {
      const raw = localStorage.getItem('ai_settings')
      return raw ? JSON.parse(raw) : null
    } catch (e) {
      return null
    }
  }

  const generateReport = async (force = false) => {
    setLoading(true);
    setError(null);
    try {
      const aiConfig = getAiConfig()
      const res = await aiAnalyze(reportId, { force, aiConfig });
      if (res.data) {
        setData(res.data);
        localStorage.setItem(cacheKey, JSON.stringify(res.data));
      }
    } catch (err) {
      console.error(err);
      setError(err.response?.data?.error || "AI 分析请求失败");
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
       <div className="ai-report-container p-8 text-center">
         <div className="animate-spin inline-block mb-4 text-accent">
           <RefreshCw size={32} />
         </div>
         <p className="text-secondary">AI 正在深入解读财报，请稍候...</p>
         <p className="text-xs text-muted mt-2">预计耗时 15-30 秒</p>
       </div>
    );
  }

  if (error) {
     return (
       <div className="ai-report-container">
         <div className="alert alert-error">
           <AlertCircle size={18} />
           <span>{error}</span>
           <button className="ml-auto underline" onClick={() => generateReport(true)}>重试</button>
         </div>
       </div>
     );
  }

  if (!data) {
    return (
      <div className="ai-report-container">
         <div className="empty-state">
           <Bot size={48} className="text-accent mb-4" />
           <h3 className="text-lg font-bold text-primary mb-2">AI 深度财报解读</h3>
           <p className="text-secondary mb-6 max-w-md text-center">
             利用大模型能力，深度分析财务数据、行业对比、估值模型，生成专业的投资建议和走势预测。
           </p>
           <button onClick={() => generateReport(false)} className="geek-btn bg-accent text-white px-6 py-2">
             <Bot size={18} />
             <span>生成 AI 报告</span>
           </button>
         </div>
      </div>
    );
  }

  return (
    <div className="ai-report-container">
      <div className="flex justify-between items-center mb-2">
         <h2 className="text-xl font-bold text-primary flex items-center gap-2">
           <Bot size={24} className="text-accent" />
           AI 深度分析报告
         </h2>
         <button onClick={() => generateReport(true)} className="text-xs text-muted flex items-center gap-1 hover:text-accent">
           <RefreshCw size={12} /> 重新生成
         </button>
      </div>

      {/* 1. Interpretation Summary */}
      <div className="ai-card">
        <div className="ai-card-header">
           <FileText size={20} className="text-primary" />
           <h3 className="ai-title">执行摘要</h3>
        </div>
        <p className="ai-summary-text">{data.interpretation?.summary}</p>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-4">
           <div>
             <h4 className="text-sm font-bold text-success mb-2">亮点</h4>
             <ul className="ai-highlights-list">
               {data.interpretation?.highlights?.map((h, i) => (
                 <li key={i} className="ai-highlight-item">
                   <span className="text-success">•</span> {h}
                 </li>
               ))}
             </ul>
           </div>
           <div>
             <h4 className="text-sm font-bold text-danger mb-2">风险</h4>
             <ul className="ai-highlights-list">
               {data.interpretation?.risks?.map((r, i) => (
                 <li key={i} className="ai-highlight-item">
                   <span className="text-danger">•</span> {r}
                 </li>
               ))}
             </ul>
           </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <InvestmentAdvice data={data.investment_advice} />
        <PriceForecast data={data.forecast} currentPrice={currentPrice} />
      </div>
    </div>
  );
};

export default AIReport;
