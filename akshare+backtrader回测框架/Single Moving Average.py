import akshare as ak # 历史数据 
import pandas as pd # 格式转换 
import backtrader as bt # 回测框架 

df = ak.stock_zh_a_hist(symbol="000001", period="daily", start_date="20250101", end_date='20260105', adjust="hfq") 
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
        ma=30
       # stop_loss=0.01, 
        # take_profit=0.05 
    )  

    def __init__(self): 
         sma = bt.ind.SMA(period=self.p.ma) 
         self.crossover = bt.ind.CrossOver(self.data.close, sma) 

    def next(self): 
        if not self.position: 
            if self.crossover > 0:
                self.buy() 
        elif self.crossover < 0: 
                self.close()  
                
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