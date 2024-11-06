
import alpaca_trade_api as tradeapi
from alpaca_trade_api.rest import REST,TimeFrame, TimeFrameUnit
import ta 
import pandas as pd 
socket = 'wss://stream.data.alpaca.markets/v2/iex'
KEY = 'PKNJNM9JXRUW0AW7CKBE'
SECRET_KEY = 'vXVj9GW0uXP8aiFFahTx6wcqaOJd7R9BwGBIyYhU'
api =REST(KEY, SECRET_KEY,'https://paper-api.alpaca.markets')
rsi = {}
pd.set_option('display.max_rows', None)
profits = 0
percents= 0


    
def trade(ticker, start, end, shares):
    profit = 0
    data = api.get_bars(ticker,TimeFrame(1, TimeFrameUnit.Minute), start,end).df
    close = data['close']
    df = ta.momentum.rsi(close, window=14)
    # drop first 13 bars since we wont be using these prices stil rsi calc are done on 14th bar 
    rsi = df.iloc[13:]
    data = data.iloc[13:]
    prices = data['close']
    val = prices.iloc[0]*shares
    rsi_change = rsi.iloc[0]
    j= True
    tot_rsi = 0
    avg_rsi = list()
    delta = 0
    tilt = 1 # changes depending on rsi trend: down trend decreases tilt while upward momentum increases 
    for i in range(len(rsi)):
        if i !=0:
            avg_rsi.append(tot_rsi/i)
        if len(avg_rsi) > 1:
            tilt+= (avg_rsi[i-1]-avg_rsi[i-2])/avg_rsi[i-1]
        
        tot_rsi+=rsi.iloc[i]
        
   
        #sell
        if val!=0 and prices.iloc[i-2] <prices.iloc[i]  : # check for steep trend and only sell at a profit 
            if rsi.iloc[i] >= rsi_change+(23*tilt) and rsi.iloc[i]>75 :
                rsi_change = rsi.iloc[i]
                old_val = val 
                val = prices.iloc[i]*shares
                profit += val-old_val
                val = 0
          
        #buy
        if val ==0 and prices.iloc[i-2] >prices.iloc[i] or (val ==0 and  rsi.iloc[i] < 30) :
            if rsi.iloc[i] <= rsi_change-(23*tilt):
              
                rsi_change = rsi.iloc[i]
                val = prices.iloc[i]*shares
        
    return profit, (profit/prices.iloc[0]/shares)*100


# Mag 7 tickers 
tickers = ["TSLA"]

# Calculate the profits for a given time frame on all tickers 
for i in tickers:
    profit, percent = trade(i, "2024-01-19","2024-01-22", 1000) 
    profits += profit
    percents +=percent
print(f"Profits {profits},  Percent {percents}%")
