import { useState, useRef, useEffect, useCallback } from 'react'
import { Maximize2, X, Settings } from 'lucide-react'

/**
 * 图表容器组件
 * 功能：拖拽调整大小、全屏查看、折叠/展开
 */
const ChartContainer = ({
  title,
  children,
  defaultHeight = 400,
  defaultWidth = '100%',
  showToolbar = true,
  onLayoutChange,
  className = '',
  chartId
}) => {
  const [isFullscreen, setIsFullscreen] = useState(false)
  const [isCollapsed, setIsCollapsed] = useState(false)
  const [dimensions, setDimensions] = useState({
    width: defaultWidth,
    height: defaultHeight
  })

  const containerRef = useRef(null)
  const resizeRef = useRef({
    isResizing: false,
    startX: 0,
    startY: 0,
    startWidth: 0,
    startHeight: 0
  })

  // 全屏切换
  const toggleFullscreen = useCallback(() => {
    const newState = !isFullscreen
    setIsFullscreen(newState)

    if (onLayoutChange) {
      onLayoutChange(chartId, {
        isFullscreen: newState,
        timestamp: Date.now()
      })
    }
  }, [isFullscreen, chartId, onLayoutChange])

  // 折叠切换
  const toggleCollapse = useCallback(() => {
    const newState = !isCollapsed
    setIsCollapsed(newState)
    if (onLayoutChange) {
      onLayoutChange(chartId, { isCollapsed: newState })
    }
  }, [isCollapsed, chartId, onLayoutChange])

  // 拖拽调整大小
  const startResize = useCallback((e) => {
    e.preventDefault()
    const rect = containerRef.current?.getBoundingClientRect()
    if (!rect) return

    resizeRef.current = {
      isResizing: true,
      startX: e.clientX,
      startY: e.clientY,
      startWidth: rect.width,
      startHeight: rect.height
    }

    document.addEventListener('mousemove', handleResize)
    document.addEventListener('mouseup', stopResize)
    document.body.style.cursor = 'nwse-resize'
  }, [])

  const handleResize = useCallback((e) => {
    if (!resizeRef.current.isResizing) return

    const deltaX = e.clientX - resizeRef.current.startX
    const deltaY = e.clientY - resizeRef.current.startY

    const newWidth = Math.max(300, resizeRef.current.startWidth + deltaX)
    const newHeight = Math.max(200, resizeRef.current.startHeight + deltaY)

    setDimensions({
      width: newWidth,
      height: newHeight
    })
  }, [])

  const stopResize = useCallback(() => {
    resizeRef.current.isResizing = false
    document.removeEventListener('mousemove', handleResize)
    document.removeEventListener('mouseup', stopResize)
    document.body.style.cursor = 'default'

    if (onLayoutChange) {
      onLayoutChange(chartId, {
        dimensions: dimensions,
        timestamp: Date.now()
      })
    }
  }, [dimensions, onLayoutChange, chartId, handleResize])

  // 清理事件监听
  useEffect(() => {
    return () => {
      document.removeEventListener('mousemove', handleResize)
      document.removeEventListener('mouseup', stopResize)
    }
  }, [handleResize])

  // 全屏样式
  const fullscreenStyles = isFullscreen ? {
    position: 'fixed',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    zIndex: 9999,
    backgroundColor: '#ffffff',
    padding: '20px'
  } : {}

  return (
    <div
      ref={containerRef}
      className={`chart-container ${className} ${isFullscreen ? 'fullscreen' : ''}`}
      style={{
        ...dimensions,
        ...fullscreenStyles,
        border: '1px solid #e5e7eb',
        borderRadius: '8px',
        overflow: 'hidden',
        display: 'flex',
        flexDirection: 'column',
        transition: isFullscreen ? 'none' : 'all 0.3s ease',
        resize: 'both'
      }}
    >
      {/* 工具栏 */}
      {showToolbar && (
        <div className="chart-toolbar" style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          padding: '8px 12px',
          backgroundColor: '#f9fafb',
          borderBottom: '1px solid #e5e7eb'
        }}>
          <div className="chart-title" style={{
            fontWeight: 600,
            fontSize: '14px',
            color: '#374151'
          }}>
            {title}
          </div>

          <div className="chart-controls" style={{
            display: 'flex',
            gap: '4px'
          }}>
            {/* 设置按钮（预留） */}
            <button
              className="control-btn"
              onClick={() => {}}
              title="设置"
              style={{
                padding: '4px',
                background: 'none',
                border: 'none',
                cursor: 'pointer',
                color: '#6b7280'
              }}
            >
              <Settings size={16} />
            </button>

            {/* 全屏/退出全屏 */}
            <button
              className="control-btn"
              onClick={toggleFullscreen}
              title={isFullscreen ? '退出全屏' : '全屏'}
              style={{
                padding: '4px',
                background: 'none',
                border: 'none',
                cursor: 'pointer',
                color: '#6b7280'
              }}
            >
              <Maximize2 size={16} />
            </button>
          </div>
        </div>
      )}

      {/* 内容区域 */}
      <div
        className="chart-content"
        style={{
          flex: 1,
          height: isCollapsed ? 0 : 'auto',
          overflow: 'hidden',
          display: isCollapsed ? 'none' : 'block'
        }}
      >
        {children}
      </div>

      {/* 调整大小手柄（右下角） */}
      {!isFullscreen && (
        <div
          className="resize-handle"
          onMouseDown={startResize}
          style={{
            position: 'absolute',
            bottom: 0,
            right: 0,
            width: '20px',
            height: '20px',
            cursor: 'nwse-resize',
            background: 'linear-gradient(135deg, transparent 50%, #d1d5db 50%)'
          }}
        />
      )}
    </div>
  )
}

export default ChartContainer
