from alpaca.trading.client import TradingClient
from alpaca.trading.enums import OrderSide, TimeInForce
from alpaca.trading.requests import *
from alpaca.data.requests import *
import threading,time, requests
from datetime import datetime
import datetime
import alpaca_trade_api as tradeapi
from alpaca.data.historical import StockHistoricalDataClient
from alpaca_trade_api.rest import REST,TimeFrame, TimeFrameUnit
from alpaca.data.live import StockDataStream
from polygon import RESTClient
import ta 
import pandas as pd 
import json
import numpy as np
import statistics
KEY = 'your-key'
SECRET_KEY = 'your-secret-key'
api =REST(KEY, SECRET_KEY)
url = "https://data.alpaca.markets/v2/stocks/bars/latest?symbols=NVDA&feed=iex"
poly_key = 'your-key'
trading_client = TradingClient(KEY, SECRET_KEY)
client = StockHistoricalDataClient(KEY, SECRET_KEY)
poly_client= RESTClient(poly_key)
pd.set_option('display.max_rows', None)
account = trading_client.get_account()
data_bars = []
sell_buy = False
price = 0


def write_data():
    data= get_bar('NVDA', '5Min')
    filename= './{}.txt'.format('NVDA')
    with open(filename,'a') as f:
        f.write(str(data['bars']['NVDA'][-1]['c'])+"\n")
    read_data()    
    
def read_data():
    global data_bars
    filename= './NVDA.txt'
    with open(filename,'r') as f:
        close = float(f.readlines()[-1].strip())
        data_bars = np.append(data_bars, close)
        
        
def get_bar(ticker,timeframe):
    u = 'https://data.alpaca.markets/v2/stocks/bars'
    params = {
    'symbols': ticker,
    'timeframe': timeframe,
    }
    
    headers = {
    "accept": "application/json",
    "APCA-API-KEY-ID": f'{KEY}',
    "APCA-API-SECRET-KEY": f'{SECRET_KEY}'
    }
    response = requests.get(u, params=params, headers=headers)
    return response.json()


def order(ticker, shares, type, price):
    market_order_data =LimitOrderRequest(symbol=ticker,qty=shares,side=type,time_in_force=TimeInForce.DAY, limit_price=float(price))
    order = trading_client.submit_order(order_data=market_order_data)
    
def trade(ticker, shares, data):
    if len(data) < 14:
        return
    close = pd.Series(data)
    df = ta.momentum.rsi(close, window=14)
    # drop first 13 bars since we wont be using these prices stil rsi calc are done on 14th bar 
    rsi = df.iloc[13:]
    close.iloc[13:]
    prices = close
    global sell_buy
    rsi_change = rsi.iloc[0]
    global price
    barset = api.get_latest_quote(ticker, 'iex') 
    current_price = 0 # planned to update to current market price through an API call
    tot_rsi = 0
    avg_rsi = list()
    tilt = 1 # changes depending on rsi trend: down trend decreases tilt while upward momentum increases 
    for i in range(len(rsi)):
        
        if i !=0:
            avg_rsi.append(tot_rsi/i)
        if len(avg_rsi) > 1 and statistics.mean(avg_rsi) != 0:
            tilt+= (avg_rsi[i-1]-avg_rsi[i-2])/avg_rsi[i-1]
        tot_rsi+=rsi.iloc[i]
        
   
        #sell
    if sell_buy == True and prices.iloc[-1] <prices.iloc[i]  : # check for steep trend and only sell at a profit 
        if rsi.iloc[-1] >= rsi_change+(23*tilt) and rsi.iloc[-1]>75 :
                order(ticker, shares, OrderSide.SELL,prices.iloc[i])
                print("sold")
                rsi_change = rsi.iloc[-1]
                sell_buy = False
                price = prices.iloc[i]
        elif prices.iloc[i] <  price*.99:
                order(ticker, shares, OrderSide.SELL, prices.iloc[i])
                print("sold")
                rsi_change = rsi.iloc[-1]
                sell_buy = False
                price = prices.iloc[i]
          
        #buy
    if sell_buy == False and prices.iloc[-1] >prices.iloc[i]:
        if rsi.iloc[i] <= rsi_change-(23*tilt):
                order(ticker, shares, OrderSide.BUY, prices.iloc[i]) 
                print("bought")
                rsi_change = rsi.iloc[-1]
                sell_buy = True
                price = prices.iloc[i]
        elif sell_buy == False and  rsi.iloc[-1] < 35:
                order(ticker, shares, OrderSide.BUY, prices.iloc[i]) 
                print("bought")
                rsi_change = rsi.iloc[-1]
                sell_buy = True
                price = prices.iloc[i]
                       

    print(rsi_change, rsi.iloc[-1], tilt)
    return close

def main():
    
    
        while True:
            time.sleep(300)
            write_data()
            trade('NVDA',10 , data_bars)
    # Mag 7 tickers 
        tickers = ["TSLA", "AAPL", "NVDA"]

    
       
        
if __name__ == '__main__':
    with open("./NVDA.txt", 'w') as f:
        pass
    while True:
        current_time = datetime.datetime.now() 
        if current_time.hour == 15:
            order('NVDA', 10, OrderSide.SELL, 0)
        if current_time.second == 0 and current_time.minute%5==0:
            print("start")
         
            r  = get_bar('NVDA', '5min')
            data= r['bars']['NVDA'][-14:]
            for i in range(len(data)):
                data_bars.append(data[i]['c'])
            main()