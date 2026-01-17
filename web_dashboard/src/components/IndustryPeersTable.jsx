import React from 'react';

const IndustryPeersTable = ({ peers, currentCode }) => {
  // peers: [{code, name, price, change_pct, pe, pb, market_cap}, ...]
  
  if (!peers || peers.length === 0) {
    return <div className="text-muted text-sm p-4">暂无同行业对比数据</div>;
  }

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full divide-y divide-gray-200 text-sm">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-3 py-2 text-left font-medium text-gray-500">代码/名称</th>
            <th className="px-3 py-2 text-right font-medium text-gray-500">股价</th>
            <th className="px-3 py-2 text-right font-medium text-gray-500">涨跌幅</th>
            <th className="px-3 py-2 text-right font-medium text-gray-500">PE(动)</th>
            <th className="px-3 py-2 text-right font-medium text-gray-500">PB</th>
            <th className="px-3 py-2 text-right font-medium text-gray-500">市值(亿)</th>
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {peers.map((peer, idx) => {
            const isMe = peer.code === currentCode;
            return (
              <tr key={idx} className={isMe ? 'bg-blue-50' : ''}>
                <td className="px-3 py-2 whitespace-nowrap">
                  <div className="font-medium text-gray-900">{peer.name}</div>
                  <div className="text-xs text-gray-500">{peer.code}</div>
                </td>
                <td className="px-3 py-2 text-right whitespace-nowrap font-medium">
                  {peer.price ? peer.price.toFixed(2) : '-'}
                </td>
                <td className={`px-3 py-2 text-right whitespace-nowrap ${peer.change_pct > 0 ? 'text-red-500' : peer.change_pct < 0 ? 'text-green-500' : ''}`}>
                  {peer.change_pct ? `${peer.change_pct > 0 ? '+' : ''}${peer.change_pct}%` : '-'}
                </td>
                <td className="px-3 py-2 text-right whitespace-nowrap text-gray-600">
                  {peer.pe ? peer.pe.toFixed(1) : '-'}
                </td>
                <td className="px-3 py-2 text-right whitespace-nowrap text-gray-600">
                  {peer.pb ? peer.pb.toFixed(2) : '-'}
                </td>
                <td className="px-3 py-2 text-right whitespace-nowrap text-gray-600">
                  {peer.market_cap ? peer.market_cap.toFixed(0) : '-'}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
};

export default IndustryPeersTable;
