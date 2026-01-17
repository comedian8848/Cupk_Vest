import React from 'react';
import { ArrowUp, ArrowDown, Minus } from 'lucide-react';
import './styles.css';

const ComparisonTable = ({ stockData, industryData, stockName }) => {
  if (!stockData || !industryData) return null;

  const metrics = [
    { key: 'roe', label: 'ROE', unit: '%', isHigherBetter: true },
    { key: 'gross_margin', label: '毛利率', unit: '%', isHigherBetter: true },
    { key: 'net_margin', label: '净利率', unit: '%', isHigherBetter: true },
    { key: 'debt_ratio', label: '负债率', unit: '%', isHigherBetter: false },
    { key: 'pe_ttm', label: 'PE(TTM)', unit: '', isHigherBetter: false },
    { key: 'dividend_yield', label: '股息率', unit: '%', isHigherBetter: true },
  ];

  const renderDiff = (val1, val2, isHigherBetter) => {
    if (val1 == null || val2 == null) return <Minus size={14} className="text-muted" />;
    
    const diff = val1 - val2;
    const isBetter = isHigherBetter ? diff > 0 : diff < 0;
    const colorClass = isBetter ? 'diff-positive' : 'diff-negative';
    const Icon = isBetter ? ArrowUp : ArrowDown;

    return (
      <div className={`flex items-center gap-1 ${colorClass}`}>
        <Icon size={14} />
        <span>{Math.abs(diff).toFixed(2)}</span>
        <span className="text-xs ml-1">{isBetter ? '优于行业' : '弱于行业'}</span>
      </div>
    );
  };

  return (
    <div className="comparison-card">
      <h3 className="text-base font-bold text-primary mb-4">行业数据对比</h3>
      <table className="comparison-table">
        <thead>
          <tr>
            <th>指标</th>
            <th>{stockName || '当前股票'}</th>
            <th>行业平均</th>
            <th>差异分析</th>
          </tr>
        </thead>
        <tbody>
          {metrics.map((metric) => {
            const stockVal = stockData[metric.key];
            const industryVal = industryData[metric.key];

            return (
              <tr key={metric.key}>
                <td>{metric.label}</td>
                <td>{stockVal != null ? `${stockVal.toFixed(2)}${metric.unit}` : '-'}</td>
                <td>{industryVal != null ? `${industryVal.toFixed(2)}${metric.unit}` : '-'}</td>
                <td>{renderDiff(stockVal, industryVal, metric.isHigherBetter)}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
};

export default ComparisonTable;
