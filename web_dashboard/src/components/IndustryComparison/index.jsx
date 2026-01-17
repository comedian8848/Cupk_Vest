import React from 'react';
import ComparisonTable from './ComparisonTable';
import ComparisonRadar from './ComparisonRadar';
import './styles.css';

const IndustryComparison = ({ stockData, industryData, stockName, baseline, baselineOptions = [], onBaselineChange }) => {
  if (!stockData || !industryData) {
    return (
      <div className="p-4 text-center text-muted">
        暂无行业对比数据
      </div>
    );
  }

  const metrics = [
    { key: 'roe', label: 'ROE', unit: '%' },
    { key: 'gross_margin', label: '毛利率', unit: '%' },
    { key: 'net_margin', label: '净利率', unit: '%' },
    { key: 'debt_ratio', label: '负债率', unit: '%' },
    { key: 'pe_ttm', label: 'PE(TTM)', unit: '' },
    { key: 'dividend_yield', label: '股息率', unit: '%' }
  ]

  const formatVal = (val, unit) => (val != null ? `${Number(val).toFixed(2)}${unit}` : '-')

  const exportCSV = () => {
    const rows = metrics.map(m => {
      const s = stockData[m.key]
      const i = industryData[m.key]
      const diff = (s != null && i != null) ? (s - i) : null
      return [
        m.label,
        formatVal(s, m.unit),
        formatVal(i, m.unit),
        diff != null ? diff.toFixed(2) : '-'
      ]
    })

    const header = ['指标', stockName || '当前股票', '行业平均', '差异']
    const csv = [header, ...rows].map(r => r.join(',')).join('\n')
    const blob = new Blob([`\ufeff${csv}`], { type: 'text/csv;charset=utf-8;' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${stockName || 'stock'}_industry_comparison.csv`
    a.click()
    URL.revokeObjectURL(url)
  }

  const exportJSON = () => {
    const payload = {
      stock: stockName || '当前股票',
      baseline: baseline || 'mean',
      data: metrics.map(m => ({
        metric: m.label,
        stock_value: stockData[m.key] ?? null,
        industry_value: industryData[m.key] ?? null
      }))
    }
    const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json;charset=utf-8;' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${stockName || 'stock'}_industry_comparison.json`
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="industry-comparison-container">
       <div className="comparison-header">
         <div className="comparison-title">行业对比基准</div>
         <div className="comparison-actions">
           {baselineOptions.length > 0 && (
             <select
               className="comparison-select"
               value={baseline || baselineOptions[0].id}
               onChange={(e) => onBaselineChange?.(e.target.value)}
             >
               {baselineOptions.map(opt => (
                 <option key={opt.id} value={opt.id}>{opt.label}</option>
               ))}
             </select>
           )}
           <button className="comparison-button" onClick={exportCSV}>导出CSV</button>
           <button className="comparison-button" onClick={exportJSON}>导出JSON</button>
         </div>
       </div>
       <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <ComparisonTable stockData={stockData} industryData={industryData} stockName={stockName} />
          <ComparisonRadar stockData={stockData} industryData={industryData} stockName={stockName} />
       </div>
    </div>
  );
};

export default IndustryComparison;
