import React, { useEffect, useRef } from 'react';

const AnalysisRadar = ({ scores }) => {
  const containerRef = useRef(null);
  
  // scores: { growth, profitability, stability, safety, valuation }
  
  useEffect(() => {
    if (!scores || !containerRef.current || !window.Plotly) return;

    const data = [{
      type: 'scatterpolar',
      r: [
        scores.growth || 0,
        scores.profitability || 0,
        scores.stability || 0,
        scores.safety || 0,
        scores.valuation || 0,
        scores.growth || 0 // close loop
      ],
      theta: ['成长性', '盈利能力', '稳定性', '安全性', '估值', '成长性'],
      fill: 'toself',
      fillcolor: 'rgba(41, 98, 255, 0.2)',
      line: {
        color: '#2962ff'
      },
      name: '综合评分'
    }];

    const layout = {
      polar: {
        radialaxis: {
          visible: true,
          range: [0, 100],
          tickfont: { size: 10 }
        },
        angularaxis: {
          tickfont: { size: 12, color: '#333' }
        }
      },
      title: {
         text: '五维能力雷达图',
         font: { size: 16, color: '#333' }
      },
      margin: { t: 40, b: 40, l: 40, r: 40 },
      showlegend: false,
      autosize: true
    };

    const config = { displayModeBar: false, responsive: true };

    window.Plotly.newPlot(containerRef.current, data, layout, config);

    return () => {
      if (containerRef.current && window.Plotly) {
        window.Plotly.purge(containerRef.current);
      }
    };
  }, [scores]);

  if (!scores) return null;

  return (
    <div className="w-full h-full bg-white rounded-lg shadow-sm p-2">
      <div ref={containerRef} style={{ width: '100%', height: '100%' }} />
    </div>
  );
};

export default AnalysisRadar;