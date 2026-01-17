import React from 'react';
import { Target, Shield, Percent, Info } from 'lucide-react';
import './styles.css';

const InvestmentAdvice = ({ data }) => {
  if (!data) return null;

  const { rating, rating_score, target_price, stop_loss, position, reasoning } = data;

  const getRatingClass = (r) => {
    if (r && r.includes('买')) return 'rating-buy';
    if (r && r.includes('卖')) return 'rating-sell';
    return 'rating-hold';
  };

  return (
    <div className="ai-card">
      <div className="ai-card-header">
        <Target size={20} className="text-primary" />
        <h3 className="ai-title">投资建议</h3>
        <span className={`rating-badge ${getRatingClass(rating)} ml-auto`}>
          {rating || '中性'}
        </span>
      </div>

      <div className="investment-grid">
        <div className="advice-box">
          <div className="advice-label">目标价</div>
          <div className="advice-value text-success">¥{target_price}</div>
        </div>
        <div className="advice-box">
          <div className="advice-label">止损价</div>
          <div className="advice-value text-danger">¥{stop_loss}</div>
        </div>
        <div className="advice-box">
          <div className="advice-label">建议仓位</div>
          <div className="advice-value">{position}</div>
        </div>
        <div className="advice-box">
          <div className="advice-label">推荐指数</div>
          <div className="advice-value">{rating_score}/10</div>
        </div>
      </div>

      <div className="bg-tertiary p-4 rounded text-sm text-secondary leading-relaxed">
        <strong>逻辑支撑：</strong>
        {reasoning}
      </div>
    </div>
  );
};

export default InvestmentAdvice;
