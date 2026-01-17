/**
 * 图表联动事件总线
 * 实现跨图表数据联动和高亮
 */

import { createContext, useContext, useCallback, useEffect } from 'react'

const ChartEventContext = createContext(null)

// 事件类型定义
export const ChartEventTypes = {
  DATE_CLICK: 'date:click',        // 日期点击
  DATE_RANGE_SELECT: 'date:range', // 日期范围选择
  DATA_HIGHLIGHT: 'data:highlight', // 数据高亮
  DATA_RESET: 'data:reset'         // 重置高亮
}

export class ChartEventBus {
  constructor() {
    this.listeners = new Map()
  }

  // 订阅事件
  on(eventType, callback) {
    if (!this.listeners.has(eventType)) {
      this.listeners.set(eventType, new Set())
    }
    this.listeners.get(eventType).add(callback)

    // 返回取消订阅函数
    return () => this.off(eventType, callback)
  }

  // 取消订阅
  off(eventType, callback) {
    if (this.listeners.has(eventType)) {
      this.listeners.get(eventType).delete(callback)
    }
  }

  // 发布事件
  emit(eventType, payload) {
    if (this.listeners.has(eventType)) {
      this.listeners.get(eventType).forEach(callback => {
        try {
          callback(payload)
        } catch (error) {
          console.error('ChartEventBus callback error:', error)
        }
      })
    }
  }

  // 清空所有监听
  clear() {
    this.listeners.clear()
  }
}

// React Hook: 在组件中使用事件总线
export const useChartEvents = () => {
  const eventBus = useContext(ChartEventContext)

  if (!eventBus) {
    throw new Error('useChartEvents must be used within ChartEventProvider')
  }

  // 订阅事件
  const subscribe = useCallback((eventType, callback) => {
    return eventBus.on(eventType, callback)
  }, [eventBus])

  // 发布事件
  const publish = useCallback((eventType, payload) => {
    eventBus.emit(eventType, payload)
  }, [eventBus])

  return { subscribe, publish, eventBus }
}

// React Provider: 提供事件总线上下文
export const ChartEventProvider = ({ children }) => {
  const eventBus = new ChartEventBus()

  return (
    <ChartEventContext.Provider value={eventBus}>
      {children}
    </ChartEventContext.Provider>
  )
}

// 高阶组件：为图表组件添加联动能力
export const withChartLinkage = (WrappedComponent, { events = [] }) => {
  return function LinkedChart(props) {
    const { subscribe, publish } = useChartEvents()

    useEffect(() => {
      // 订阅指定事件
      const unsubscribers = events.map(eventConfig => {
        if (typeof eventConfig === 'string') {
          // 简单事件类型字符串
          return subscribe(eventConfig, (payload) => {
            // 默认行为：高亮对应数据
            if (props.onExternalHighlight) {
              props.onExternalHighlight(payload)
            }
          })
        } else {
          // 复杂配置：{ type: 'date:click', handler: (payload) => {} }
          return subscribe(eventConfig.type, eventConfig.handler)
        }
      })

      // 清理订阅
      return () => {
        unsubscribers.forEach(unsubscribe => unsubscribe())
      }
    }, [subscribe, props.onExternalHighlight])

    // 包装原始组件的props，注入publish方法
    const enhancedProps = {
      ...props,
      publishChartEvent: publish
    }

    return <WrappedComponent {...enhancedProps} />
  }
}

// 使用示例：
// TimeSeriesChart.jsx 中：
// onClick={(event) => {
//   if (event.points) {
//     publishChartEvent(ChartEventTypes.DATE_CLICK, {
//       date: event.points[0].x,
//       source: 'timeSeries'
//     })
//   }
// }}

// FinancialChart.jsx 中：
// useEffect(() => {
//   const unsub = subscribe(ChartEventTypes.DATE_CLICK, ({ date }) => {
//     // 高亮对应日期的财务数据
//     highlightDataByDate(date)
//   })
//   return unsub
// }, [])
