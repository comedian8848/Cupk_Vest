import akshare as ak # 历史数据 
import pandas as pd # 格式转换 
import backtrader as bt # 回测框架 
from datetime import datetime, timedelta

# 计算默认日期
today = datetime.now()
yesterday = today - timedelta(days=1)
one_year_ago = today - timedelta(days=365)

default_symbol = "000001"
default_start_date = one_year_ago.strftime("%Y%m%d")
default_end_date = yesterday.strftime("%Y%m%d")
default_cash = 100000.0
default_stake_percent = 20

# 获取用户输入
symbol = input(f"请输入股票代码 (默认: {default_symbol}): ").strip() or default_symbol
start_date = input(f"请输入开始日期 (默认: {default_start_date}): ").strip() or default_start_date
end_date = input(f"请输入结束日期 (默认: {default_end_date}): ").strip() or default_end_date
try:
    initial_cash = float(input(f"请输入起始资金 (默认: {default_cash}): ").strip() or default_cash)
    stake_percent = float(input(f"请输入每笔交易资金百分比 (默认: {default_stake_percent}): ").strip() or default_stake_percent)
except ValueError:
    print("资金或百分比输入无效，将使用默认值。")
    initial_cash = default_cash
    stake_percent = default_stake_percent

print(f"正在获取 {symbol} 从 {start_date} 到 {end_date} 的数据...")

try:
    df = ak.stock_zh_a_hist(symbol=symbol, period="daily", start_date=start_date, end_date=end_date, adjust="hfq")
    if df.empty:
        print("未获取到数据，请检查输入参数。")
        exit()
except Exception as e:
    print(f"获取数据出错: {e}")
    exit()

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
cerebro.broker.setcash(initial_cash)  
# Set commission 
cerebro.broker.setcommission(commission=0.005)  
# Add sizer 
cerebro.addsizer(bt.sizers.PercentSizer, percents=stake_percent)  
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