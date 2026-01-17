import React from 'react';
import { ResponsiveContainer, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar, Legend, Tooltip } from 'recharts';
import './styles.css';

const ComparisonRadar = ({ stockData, industryData, stockName }) => {
  if (!stockData || !industryData) return null;

  // Normalize data for radar chart (0-100 scale ideally, or relative)
  // For simplicity, we'll map a few key metrics. 
  // Note: This requires careful normalization logic in a real app. 
  // Here we just display raw values which might be off-scale if units differ vastly.
  // Better approach: Calculate percentile or ratio.
  
  const metrics = [
    { key: 'roe', label: 'ROE', fullMark: 30 },
    { key: 'gross_margin', label: '毛利', fullMark: 80 },
    { key: 'net_margin', label: '净利', fullMark: 40 },
    { key: 'growth_rate', label: '增长', fullMark: 50 },
    { key: 'safety', label: '安全', fullMark: 100 }, // Inverse of debt ratio maybe?
  ];

  const data = metrics.map(m => {
    let sVal = stockData[m.key] || 0;
    let iVal = industryData[m.key] || 0;
    
    // Simple cap
    if (sVal > m.fullMark) sVal = m.fullMark;
    if (iVal > m.fullMark) iVal = m.fullMark;

    return {
      subject: m.label,
      stock: sVal,
      industry: iVal,
      fullMark: m.fullMark
    };
  });

  return (
    <div className="comparison-card">
      <h3 className="text-base font-bold text-primary mb-4">综合能力对比</h3>
      <div className="radar-container">
        <ResponsiveContainer width="100%" height="100%">
          <RadarChart cx="50%" cy="50%" outerRadius="80%" data={data}>
            <PolarGrid stroke="var(--border-color)" />
            <PolarAngleAxis dataKey="subject" tick={{ fill: 'var(--text-secondary)', fontSize: 12 }} />
            <PolarRadiusAxis angle={30} domain={[0, 'auto']} tick={false} axisLine={false} />
            <Radar
              name={stockName || "当前股票"}
              dataKey="stock"
              stroke="var(--accent-primary)"
              fill="var(--accent-primary)"
              fillOpacity={0.4}
            />
            <Radar
              name="行业平均"
              dataKey="industry"
              stroke="var(--text-secondary)"
              fill="var(--text-secondary)"
              fillOpacity={0.2}
            />
            <Legend wrapperStyle={{ fontSize: '12px' }} />
            <Tooltip 
               contentStyle={{
                  background: 'var(--bg-secondary)',
                  border: '1px solid var(--border-color)',
                  borderRadius: 'var(--radius-md)',
                  color: 'var(--text-primary)'
                }}
            />
          </RadarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export default ComparisonRadar;
