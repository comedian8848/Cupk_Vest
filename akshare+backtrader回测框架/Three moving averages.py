import akshare as ak # 历史数据 
import pandas as pd # 格式转换 
import backtrader as bt # 回测框架 

df = ak.stock_zh_a_hist(symbol="000001", period="daily", start_date="20240101", end_date='20250101', adjust="hfq") 
print(df)  
# Convert and prepare data 
df['日期'] = pd.to_datetime(df['日期']) 
df = df.sort_values('日期') 
# Ensure data is in chronological order 
df = df.rename(columns={ 
    '日期': 'datetime', 
    '开盘': 'Open', 
    '最高': 'High', 
    '最低': 'Low', 
    '收盘': 'Close', 
    '成交额': 'Volume' }) 
df.set_index('datetime', inplace=True)  

class SimpleCross(bt.Strategy): 
    params = dict( 
        ma5=5, # 短期均线 
        ma10=10, # 中期均线 
        ma15=15, # 长期均线 
    )  

    def __init__(self): 

        # 计算三条移动平均线 
        self.sma5 = bt.ind.SMA(period=self.p.ma5) 
        self.sma10 = bt.ind.SMA(period=self.p.ma10) 
        self.sma15 = bt.ind.SMA(period=self.p.ma15) 

         # 创建交叉信号 
        self.cross_5_10 = bt.ind.CrossOver(self.sma5, self.sma10) # MA5上穿/下穿MA10 
        self.cross_5_15 = bt.ind.CrossOver(self.sma5, self.sma15) # MA5上穿/下穿MA15  

        #用于追踪均线排列状态
        self.ma_condion = None

    def next(self): 
        # 检查均线排列条件：MA5 < MA10 < MA15 
        ma_aligned = (self.sma5[-1] < self.sma10[-1] < self.sma15[-1]) 
            
         # 如果没有持仓 
        if not self.position: 
                # 买入条件：均线排列正确且MA5上穿MA10 
            if ma_aligned and self.cross_5_10 > 0: 
                self.buy() 
                print(f'{self.data.datetime.date()}: 买入 - 价格: {self.data.close[0]:.2f}')

             # 如果持有仓位 
        else:                 # 卖出条件：MA5下穿MA10 或 MA5下穿MA15 
            sell_condition = (self.cross_5_10 < 0) or (self.cross_5_15 < 0)  
            if sell_condition: 
                self.close() 
                print(f'{self.data.datetime.date()}: 卖出 - 价格: {self.data.close[0]:.2f}')
                
# Create Cerebro engine 
cerebro = bt.Cerebro() 
# Create data feed 
data = bt.feeds.PandasData(dataname=df)  
# Add data feed to Cerebro 
cerebro.adddata(data)  
# Add strategy 
cerebro.addstrategy(SimpleCross)  
# Set initial cash 
cerebro.broker.setcash(100000.0)  
# Set commission 
cerebro.broker.setcommission(commission=0.005)  
# Add sizer 
cerebro.addsizer(bt.sizers.PercentSizer, percents=20)  
# Add analyzer 
cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe') 
cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')  
print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())  
# Run backtest 
results = cerebro.run()  
print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())  
# Print analyzers 
strat = results[0] 
print('Sharpe Ratio:', strat.analyzers.sharpe.get_analysis()['sharperatio']) 
print('Return:', strat.analyzers.returns.get_analysis()['rnorm100'], '%')  
# Plot results 
cerebro.plot(style='candlestick')