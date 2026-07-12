import json
from ib_insync import *
import pandas as pd
import redis
import ibapi
import asyncio, time, random
import config
from alpaca.data.historical import CryptoHistoricalDataClient
from alpaca.data.requests import CryptoBarsRequest
from alpaca.data.timeframe import TimeFrame
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce

from ibapi.client import EClient
# Alpaca Trading Client
trading_client = TradingClient(
    config.APCA_API_KEY_ID, config.APCA_API_SECRET_KEY, paper=True)


# from fundamentals import *

# connect to Interactive Brokers 
ib = IB()
ib.connect('127.0.0.1', 7497, clientId=0)

# connect to Redis and subscribe to tradingview message
r = redis.Redis(host='localhost', port=6379, db=0)
p = r.pubsub()
p.subscribe('tradingview')

async def check_messages():
    print(f"{time.time()} - checking for tradingview webhook messages")
    message = p.get_message()
    if message is not None and message['type'] == 'message':
        print(message)

        message_data = json.loads(message['data'])

        order = MarketOrder(message_data['strategy']['order_action'], message_data['strategy']['order_contracts']) 

        if message_data['ticker'] == 'BTCUSD':

            crypto = Crypto('BTC.USD', 'PAXOS', 'USD')
            trade2 = ib.placeOrder(crypto, order)
            print("BTC Trade Info: ", trade2)

            # from alpaca.trading.requests import MarketOrderRequest
            # from alpaca.trading.enums import OrderSide, TimeInForce
            # if message_data['strategy']['order_action'] == 'buy':
            #     # Setting parameters for our buy order
            #     market_order_data = MarketOrderRequest(
            #                         symbol="BTC/USD",
            #                         qty=1,
            #                         side=OrderSide.BUY,
            #                         time_in_force=TimeInForce.GTC
            #                     )
            #                     # Submitting the order and then printing the returned object
            #     market_order = trading_client.submit_order(market_order_data)
            #     for property_name, value in market_order:
            #         print(f"\"{property_name}\": {value}")

            # elif message_data['strategy']['order_action'] == 'sell':
            #     # Setting parameters for our buy order
            #     market_order_data = MarketOrderRequest(
            #                         symbol="BTC/USD",
            #                         qty=1,
            #                         side=OrderSide.SELL,
            #                         time_in_force=TimeInForce.GTC
            #                     )
            #                     # Submitting the order and then printing the returned object
            #     market_order = trading_client.submit_order(market_order_data)
            #     for property_name, value in market_order:
            #         print(f"\"{property_name}\": {value}")

        if message_data['ticker'] == 'XAUUSD':

            gold = CFD(message_data['ticker'],'SMART','USD')
            trade1 = ib.placeOrder(gold, order)
            print("Gold Trade Info: ", trade1)

        if message_data['ticker'] == 'Z':

            stock = Stock(message_data['ticker'], 'SMART', 'USD')
            trade = ib.placeOrder(stock, order)
            print("Stock Trade Info: ", trade)
        
 
async def run_periodically(interval, periodic_fucntion):
    while True:
        await asyncio.gather(asyncio.sleep(interval), periodic_fucntion())

asyncio.run(run_periodically(1, check_messages))
ib.run()











# contract = Forex('EURUSD')
# bars = ib.reqHistoricalData(
#     contract, endDateTime='', durationStr='30 D',
#     barSizeSetting='1 hour', whatToShow='MIDPOINT', useRTH=True)

# # convert to pandas dataframe:
# df = util.df(bars)
# # print(df)
# market_data = ib.reqMktData(contract, '', False, False)


# print(market_data)

# def onPendingTickers(tickers):
#     print("pending ticker event received")
#     print(tickers)
#     return 

# ib.pendingTickersEvent += onPendingTickers
# ib.run()

 
