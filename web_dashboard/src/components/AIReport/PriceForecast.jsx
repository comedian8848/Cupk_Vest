import React from 'react';
import { TrendingUp, ArrowRight } from 'lucide-react';
import { ResponsiveContainer, ComposedChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Area, ReferenceLine, Scatter } from 'recharts';
import './styles.css';

const PriceForecast = ({ data, currentPrice }) => {
  if (!data || !data.one_year_price) return null;

  const { low, mid, high, confidence } = data.one_year_price;
  const drivers = data.key_drivers || [];

  // Construct chart data
  // Current -> Forecast (Low, Mid, High)
  const chartData = [
    { name: '当前', price: currentPrice, range: [currentPrice, currentPrice] },
    { name: '预测(1年)', price: mid, range: [low, high] }
  ];

  return (
    <div className="ai-card">
      <div className="ai-card-header">
        <TrendingUp size={20} className="text-primary" />
        <h3 className="ai-title">走势预测</h3>
        <span className="text-xs text-muted ml-auto">置信度: {confidence}</span>
      </div>

      <div className="forecast-chart-area">
        <ResponsiveContainer width="100%" height="100%">
           <ComposedChart data={chartData} margin={{ top: 20, right: 30, bottom: 0, left: 0 }}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--border-color)" />
              <XAxis dataKey="name" stroke="var(--text-muted)" />
              <YAxis domain={['auto', 'auto']} stroke="var(--text-muted)" />
              <Tooltip 
                contentStyle={{
                  background: 'var(--bg-secondary)',
                  border: '1px solid var(--border-color)',
                  color: 'var(--text-primary)'
                }}
              />
              <Line type="monotone" dataKey="price" stroke="var(--accent-primary)" strokeWidth={2} dot={{r: 4}} />
              <Area dataKey="range" fill="var(--accent-primary)" fillOpacity={0.1} stroke="none" />
              <Scatter dataKey="price" fill="var(--accent-primary)" />
           </ComposedChart>
        </ResponsiveContainer>
      </div>

      <div className="mt-4">
        <h4 className="text-sm font-bold text-secondary mb-2">核心驱动因素</h4>
        <div className="flex flex-wrap gap-2">
          {drivers.map((driver, idx) => (
             <span key={idx} className="text-xs bg-tertiary px-2 py-1 rounded text-secondary border border-border">
               {driver}
             </span>
          ))}
        </div>
      </div>
    </div>
  );
};

export default PriceForecast;
