import { useState, useEffect } from 'react'
import axios from 'axios'
import { BarChart3, Activity, DollarSign, TrendingUp, FileText, Image as ImageIcon, ArrowLeft, RefreshCw, Cpu, Box, Layers, AlertTriangle, Play, Loader, CheckCircle, XCircle, LayoutGrid, Maximize2 } from 'lucide-react'

const API_BASE = 'http://localhost:5001/api'

function App() {
  const [reports, setReports] = useState([])
  const [selectedReport, setSelectedReport] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [showAnalyzer, setShowAnalyzer] = useState(false)

  useEffect(() => {
    fetchReports()
  }, [])

  const fetchReports = async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await axios.get(`${API_BASE}/reports`)
      setReports(res.data)
    } catch (err) {
      console.error(err)
      setError("无法连接到服务器，请确保 Python 后端正在运行。")
    } finally {
      setLoading(false)
    }
  }

  const loadReportDetails = async (report) => {
    setLoading(true)
    try {
      const [detailsRes, summaryRes] = await Promise.all([
        axios.get(`${API_BASE}/reports/${report.id}`),
        report.type === 'stock' ? axios.get(`${API_BASE}/reports/${report.id}/summary`).catch(() => ({data: null})) : Promise.resolve({data: null})
      ])
      
      setSelectedReport({
        ...report,
        ...detailsRes.data,
        summaryData: summaryRes.data
      })
      setShowAnalyzer(false)
    } catch (err) {
      console.error(err)
      alert("加载报告详情失败")
    } finally {
      setLoading(false)
    }
  }

  const handleAnalysisComplete = (code) => {
    fetchReports()
    setTimeout(() => {
      const newReport = reports.find(r => r.code === code)
      if (newReport) loadReportDetails(newReport)
    }, 1000)
  }

  return (
    <div className="geek-container">
      {/* Header */}
      <header className="geek-header">
        <div className="flex items-center gap-3">
          <div className="flex items-center justify-center" style={{width: 36, height: 36, background: 'linear-gradient(135deg, var(--accent-primary), var(--color-up))', borderRadius: 'var(--radius-md)'}}>
            <BarChart3 size={20} color="white" />
          </div>
          <div>
            <h1 className="text-lg font-bold text-primary">BlackOil</h1>
            <div className="text-xs text-muted">专业金融分析平台</div>
          </div>
        </div>
        <div className="flex gap-2">
          <button 
            onClick={() => {
              setShowAnalyzer(!showAnalyzer)
              setSelectedReport(null)
            }} 
            className="geek-btn"
            style={showAnalyzer ? {background: 'var(--color-success)'} : {}}
          >
            <Play size={14} />
            <span>新建分析</span>
          </button>
          <button onClick={fetchReports} className="geek-btn" disabled={loading} style={{background: 'var(--bg-tertiary)'}}>
            <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
            <span className="hidden-md">刷新</span>
          </button>
        </div>
      </header>

      {/* Error Alert */}
      {error && (
        <div className="alert alert-error mb-4">
          <AlertTriangle size={18} />
          <span>{error}</span>
        </div>
      )}

      {/* Main Content */}
      <main>
        {showAnalyzer ? (
          <StockAnalyzer onComplete={handleAnalysisComplete} onBack={() => setShowAnalyzer(false)} />
        ) : selectedReport ? (
          <ReportDetail report={selectedReport} onBack={() => setSelectedReport(null)} />
        ) : (
          <div className="animate-in">
            {/* Report Grid */}
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
              {reports.map((report) => (
                <div 
                  key={report.id} 
                  onClick={() => loadReportDetails(report)}
                  className="geek-card"
                >
                  <div className="flex items-center gap-2 mb-3">
                    <div 
                      className="flex items-center justify-center"
                      style={{
                        width: 32, 
                        height: 32, 
                        borderRadius: 'var(--radius-md)',
                        background: report.type === 'stock' ? 'rgba(41, 98, 255, 0.15)' : 'rgba(255, 152, 0, 0.15)'
                      }}
                    >
                      {report.type === 'stock' 
                        ? <Activity size={16} style={{color: 'var(--accent-primary)'}} /> 
                        : <Layers size={16} style={{color: 'var(--color-warning)'}} />
                      }
                    </div>
                    <span className="text-xs text-muted">
                      {report.type === 'stock' ? '股票' : '期货'}
                    </span>
                  </div>
                  
                  <h3 className="text-xl font-bold text-primary mb-1">{report.code}</h3>
                  {report.name && <div className="text-xs text-muted mb-1">{report.name}</div>}
                  <div className="text-sm text-secondary">{report.date}</div>
                </div>
              ))}
            </div>
            
            {/* Empty State */}
            {reports.length === 0 && !loading && !error && (
              <div className="empty-state">
                <Box size={48} />
                <div className="text-lg font-medium">暂无分析报告</div>
                <div className="text-sm">点击「新建分析」生成第一份报告</div>
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  )
}

function StockAnalyzer({ onComplete, onBack }) {
  const [code, setCode] = useState('')
  const [taskId, setTaskId] = useState(null)
  const [status, setStatus] = useState(null)
  const [error, setError] = useState(null)

  const startAnalysis = async () => {
    if (!code.trim()) {
      setError('请输入股票代码')
      return
    }

    setError(null)
    try {
      const res = await axios.post(`${API_BASE}/analyze`, { code: code.trim() })
      setTaskId(res.data.task_id)
      pollStatus(res.data.task_id)
    } catch (err) {
      setError(err.response?.data?.error || '启动分析失败')
    }
  }

  const pollStatus = async (id) => {
    const interval = setInterval(async () => {
      try {
        const res = await axios.get(`${API_BASE}/analyze/${id}`)
        setStatus(res.data)

        if (res.data.status === 'completed') {
          clearInterval(interval)
          setTimeout(() => {
            onComplete(res.data.code)
          }, 1500)
        } else if (res.data.status === 'error') {
          clearInterval(interval)
          setError(res.data.message)
        }
      } catch (err) {
        clearInterval(interval)
        setError('获取状态失败')
      }
    }, 2000)
  }

  return (
    <div className="animate-in" style={{maxWidth: 520, margin: '0 auto'}}>
      <button onClick={onBack} className="geek-btn mb-4" style={{background: 'var(--bg-tertiary)'}}>
        <ArrowLeft size={14} />
        <span>返回</span>
      </button>

      <div className="info-panel">
        <h2 className="text-xl font-bold text-primary mb-6 flex items-center gap-2">
          <Play size={20} style={{color: 'var(--accent-primary)'}} />
          新建股票分析
        </h2>
        
        {!taskId ? (
          <div className="flex flex-col gap-4">
            <div>
              <label className="text-sm text-secondary mb-2" style={{display: 'block'}}>股票/期货代码</label>
              <input
                type="text"
                value={code}
                onChange={(e) => setCode(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && startAnalysis()}
                placeholder="如：600519、RB、螺纹钢"
                style={{
                  width: '100%',
                  padding: '12px 16px',
                  background: 'var(--bg-tertiary)',
                  border: '1px solid var(--border-color)',
                  borderRadius: 'var(--radius-md)',
                  color: 'var(--text-primary)',
                  fontSize: '14px'
                }}
              />
            </div>

            {error && (
              <div className="alert alert-error">
                <XCircle size={16} />
                <span>{error}</span>
              </div>
            )}

            <button onClick={startAnalysis} className="geek-btn w-full" style={{padding: '12px', fontSize: '15px'}}>
              <Play size={16} />
              <span>开始分析</span>
            </button>

            <div className="text-sm text-muted" style={{borderTop: '1px solid var(--border-color)', paddingTop: '16px'}}>
              <p style={{marginBottom: '4px'}}>• 支持 A 股（6位代码）和期货品种</p>
              <p style={{marginBottom: '4px'}}>• 分析耗时约 1-3 分钟</p>
              <p>• 将生成 20+ 张专业图表</p>
            </div>
          </div>
        ) : (
          <div className="flex flex-col gap-4">
            <div className="flex items-center gap-3">
              {status?.status === 'running' && <Loader size={22} className="animate-spin" style={{color: 'var(--accent-primary)'}} />}
              {status?.status === 'completed' && <CheckCircle size={22} style={{color: 'var(--color-success)'}} />}
              {status?.status === 'error' && <XCircle size={22} style={{color: 'var(--color-down)'}} />}
              
              <div style={{flex: 1}}>
                <div className="text-xs text-muted mb-1">状态</div>
                <div className="text-base font-semibold text-primary">
                  {status?.message || '初始化中...'}
                </div>
              </div>
            </div>

            {status?.status === 'running' && (
              <div>
                <div className="progress-bar mb-2">
                  <div 
                    className="progress-bar-fill"
                    style={{ width: `${status.progress || 5}%` }}
                  />
                </div>
                <div className="text-xs text-muted" style={{textAlign: 'right'}}>
                  {status.progress || 0}%
                </div>
              </div>
            )}

            {error && (
              <div className="alert alert-error">
                <XCircle size={16} />
                <span>{error}</span>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

function ReportDetail({ report, onBack }) {
  const [activeTab, setActiveTab] = useState('all')
  
  const images = report.images || []
  const categories = {
    overview: images.filter(i => i.includes('Dashboard') || i.includes('增量分析') || i.includes('概览')),
    trend: images.filter(i => i.match(/\/(00|01|02|03|05|06|08)_/)),
    valuation: images.filter(i => i.match(/\/(04|11|12|13|21)_/)),
    financials: images.filter(i => i.includes('财务') || i.match(/\/(07|09|14|15|16|18|20)_/)),
    technicals: images.filter(i => i.includes('技术') || i.includes('回测') || i.includes('99_')),
    all: images
  }
  
  const currentImages = (report.type === 'stock' && categories[activeTab]?.length > 0) 
    ? categories[activeTab] 
    : (activeTab === 'all' ? images : [])

  const TABS = [
    { id: 'all', label: '全部', icon: <LayoutGrid size={14} /> },
    { id: 'overview', label: '概览', icon: <Activity size={14} /> },
    { id: 'trend', label: '趋势', icon: <TrendingUp size={14} /> },
    { id: 'valuation', label: '估值', icon: <DollarSign size={14} /> },
    { id: 'financials', label: '财务', icon: <FileText size={14} /> },
    { id: 'technicals', label: '技术', icon: <Cpu size={14} /> },
  ]

  const summary = report.summaryData || {}
  
  return (
    <div className="animate-in">
      {/* Back Button */}
      <button onClick={onBack} className="geek-btn mb-4" style={{background: 'var(--bg-tertiary)'}}>
        <ArrowLeft size={14} />
        <span>返回列表</span>
      </button>
      
      {/* Header Panel */}
      <div className="info-panel mb-6">
        <div className="flex flex-col gap-4" style={{position: 'relative', zIndex: 1}}>
          {/* Top Row: Code and Type */}
          <div className="flex items-center justify-between flex-wrap gap-4">
            <div>
              <div className="text-xs text-accent mb-1">
                {report.type === 'stock' ? '股票代码' : '期货品种'}
              </div>
              <div>
                <h1 className="text-3xl font-bold text-primary">{report.code}</h1>
                {summary.stock_name && <div className="text-sm text-secondary mt-1">{summary.stock_name}</div>}
              </div>
            </div>
            
            <div className="flex items-center gap-3">
              <span 
                className="text-xs px-3 py-1 rounded"
                style={{
                  background: report.type === 'stock' ? 'rgba(41, 98, 255, 0.15)' : 'rgba(255, 152, 0, 0.15)',
                  color: report.type === 'stock' ? 'var(--accent-primary)' : 'var(--color-warning)'
                }}
              >
                {report.type === 'stock' ? '股票' : '期货'}
              </span>
              <span className="text-sm text-secondary">{report.date}</span>
            </div>
          </div>

          {/* Metrics Row */}
          {summary.stock_name && (
            <div className="grid grid-cols-1 md:grid-cols-4 gap-3 mt-4">
              <MetricBox label="行业" value={summary.industry || '-'} />
              <MetricBox label="总股本" value={summary.total_shares ? (summary.total_shares / 1e8).toFixed(2) + '亿' : '-'} />
              <MetricBox label="市值" value={summary.market_cap ? (summary.market_cap / 1e8).toFixed(2) + '亿' : '-'} highlight />
              <MetricBox label="PE(TTM)" value={summary.pe_ttm ? summary.pe_ttm.toFixed(2) : '-'} />
            </div>
          )}
          
          {/* Key Insights */}
          {summary && Object.keys(summary).length > 0 && (
            <div className="border-t" style={{borderColor: 'var(--border-color)', paddingTop: '16px', marginTop: '16px'}}>
              <h3 className="text-sm font-semibold text-primary mb-3 flex items-center gap-2">
                <span style={{width: 4, height: 4, borderRadius: '50%', background: 'var(--accent-primary)'}}></span>
                关键指标
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {summary.roe && <KeyInsightItem label="ROE" value={summary.roe.toFixed(2) + '%'} />}
                {summary.gross_margin && <KeyInsightItem label="毛利率" value={summary.gross_margin.toFixed(2) + '%'} />}
                {summary.net_margin && <KeyInsightItem label="净利率" value={summary.net_margin.toFixed(2) + '%'} />}
                {summary.debt_ratio && <KeyInsightItem label="负债比" value={summary.debt_ratio.toFixed(2) + '%'} />}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Tabs */}
      {report.type === 'stock' && (
        <div className="tabs-container">
          {TABS.map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`tab-button ${activeTab === tab.id ? 'active' : ''}`}
            >
              {tab.icon}
              <span>{tab.label}</span>
            </button>
          ))}
        </div>
      )}

      {/* Analysis Text */}
      {summary.raw_text && activeTab === 'overview' && (
        <div className="info-panel mb-6">
          <div className="flex items-center gap-2 mb-3 text-accent">
            <FileText size={16} />
            <h3 className="font-semibold text-sm">分析报告</h3>
          </div>
          <pre className="report-text">{summary.raw_text}</pre>
        </div>
      )}

      {/* Chart Grid - 核心修复：使用独立的图表卡片网格 */}
      <div className="chart-grid">
        {report.type === 'futures' ? (
          report.images.map((img, idx) => (
            <ImageCard key={idx} src={img} fullWidth />
          ))
        ) : (
          currentImages.length > 0 ? (
            currentImages.map((img, idx) => (
              <ImageCard key={idx} src={img} />
            ))
          ) : (
            <div className="empty-state col-span-full">
              <ImageIcon size={40} />
              <div>该分类下暂无图表</div>
            </div>
          )
        )}
      </div>
    </div>
  )
}

function MetricBox({ label, value, highlight = false }) {
  return (
    <div className={`metric-box ${highlight ? 'highlight' : ''}`}>
      <div className="metric-label">{label}</div>
      <div className="metric-value truncate">{value || '-'}</div>
    </div>
  )
}

function KeyInsightItem({ label, value }) {
  return (
    <div className="flex items-center justify-between p-3 rounded" style={{background: 'var(--bg-tertiary)'}}>
      <span className="text-sm text-secondary">{label}</span>
      <span className="font-semibold text-primary">{value}</span>
    </div>
  )
}

function ImageCard({ src, fullWidth = false }) {
  const [isExpanded, setIsExpanded] = useState(false)
  const fileName = src.split('/').pop().replace(/\.(png|jpg|jpeg)$/i, '')
  
  return (
    <>
      <div className={`chart-card ${fullWidth ? 'full-width' : ''}`}>
        <div className="chart-card-header">
          <span title={fileName}>{fileName}</span>
          <div className="status-dot online"></div>
        </div>
        <div 
          className="chart-card-body cursor-pointer" 
          onClick={() => setIsExpanded(true)}
        >
          <img 
            src={`http://localhost:5001${src}`} 
            alt={fileName}
            loading="lazy"
          />
          <div 
            className="flex items-center justify-center gap-2"
            style={{
              position: 'absolute',
              inset: 0,
              background: 'rgba(41, 98, 255, 0.05)',
              opacity: 0,
              transition: 'opacity 0.2s'
            }}
            onMouseEnter={(e) => e.currentTarget.style.opacity = 1}
            onMouseLeave={(e) => e.currentTarget.style.opacity = 0}
          >
            <span 
              className="flex items-center gap-1 text-sm"
              style={{
                background: 'var(--bg-secondary)',
                padding: '6px 12px',
                borderRadius: 'var(--radius-md)',
                color: 'var(--text-primary)'
              }}
            >
              <Maximize2 size={14} />
              点击放大
            </span>
          </div>
        </div>
      </div>

      {/* Lightbox */}
      {isExpanded && (
        <div className="lightbox-overlay" onClick={() => setIsExpanded(false)}>
          <button className="lightbox-close" onClick={() => setIsExpanded(false)}>
            ✕
          </button>
          <img 
            src={`http://localhost:5001${src}`} 
            alt={fileName}
            className="lightbox-image"
            onClick={(e) => e.stopPropagation()}
          />
        </div>
      )}
    </>
  )
}

export default App
