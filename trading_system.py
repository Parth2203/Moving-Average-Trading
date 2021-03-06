"""
This script contains the main trading system.
"""

import os
import sys
import json
import logging
import time
import numpy as np
from datetime import datetime
import configparser as ConfigParser
from connection import Client
from strategy import Momentum
from email_notification import Notification

# Intializing parameters
configParser = ConfigParser.RawConfigParser()
configParser.read('config.cfg')

TIMEFRAME = '1Min'
MAX_BUDGET = float(configParser.get('system', 'max_budget'))
EXCHANGE = str(configParser.get('system', 'exchange'))
UNIVERSE = json.loads(configParser.get('system', 'universe'))
FAST_MA = int(configParser.get('strategy', 'fast_ma'))
SLOW_MA = int(configParser.get('strategy', 'slow_ma'))

# Split the budget equally among all the assets in the asset UNIVERSE
BUDGET = MAX_BUDGET//len(UNIVERSE)

# Logging init
logging.basicConfig(
    filename='error.log',
    level=logging.WARNING,
    format='%(asctime)s:%(levelname)s:%(message)s')


# Setup the connection with the API
client = Client()
websocket = client.streaming_api()
api = client.rest_api()

# Setup email notification
email = Notification('Momentum Trading Algo')


class System:
    def __init__(self, ticker:str):
        # Create an instance of the Trading System for Time-series momentum.
        
        self.ticker = ticker
        self.buy_price = None
        print(f"Intializing Momentum Strategy for : {ticker} .............")
        
        # Intialize the strategy
        self.strategy = Momentum(FAST_MA, SLOW_MA)
        self.get_history()

    def get_history(self):

        # A function to get the historical bars of pair

        try:
            self.price = api.get_crypto_bars(self.ticker, TIMEFRAME,
                                            datetime.now().date(),
                                            limit=SLOW_MA,
                                            exchanges=[EXCHANGE]).df.close.values
        except Exception as e:
            logging.exception(e)
            print(e)

    def close_position(self):

        # Close the current market position of the asset.

        try:
            # Close the position if exist
            order = api.close_position(self.ticker)
            # Check if filled
            status = api.get_order(order).status
            price = api.get_latest_crypto_trade(self.ticker,
                                                exchange=EXCHANGE).price
            message = f"SOLD ${BUDGET} worth of {self.ticker} HOLDING at ${price}.\n \
                        Realized PnL : {price - self.buy_price}"
            email.send_notification(message)
            return status
        except Exception as e:
            logging.exception(e)
            print(e)

    def check_market_open(self):

        # Check if the market is open. If not the sleep till the market opens.

        clock = api.get_clock()
        if clock.is_open:
            pass
        else:
            time_to_open = clock.next_open - clock.timestamp
            print(
                f"Market is closed now going to sleep for \
                {time_to_open.total_seconds()//60} minutes")
            time.sleep(time_to_open.total_seconds())

    def get_dollar_qty(self, symbol:str)->int:

        # Get the Quantity of stocks to trade based on the dollar value.

        current_asset_price = api.get_latest_crypto_trade(symbol,
                                                          exchange=EXCHANGE).price
        qty = BUDGET / current_asset_price
        return qty

    def OMS(self, side:str):

        # A simple Order Management System that sends out orders to the Broker on arrival of a trading signal.

        if side=='LONG':
            try:
                order_info = api.submit_order(
                                symbol=self.ticker,
                                #qty=self.get_dollar_qty(self.ticker),
                                notional=BUDGET,
                                side='buy',
                                type='market',
                                time_in_force='day')
                print(order_info)
                price = api.get_latest_crypto_trade(self.ticker,
                                                    exchange=EXCHANGE).price
                self.buy_price = price
                message = f"BOUGHT ${BUDGET} worth of {self.ticker} at ${price}"
                email.send_notification(message)

            except Exception as e:
                logging.exception(e)
                print(e)
        else:
            self.close_position()

    def update_price(self, price:float):
        # Update the prices in the queue everytime a new price is available.

        self.price[:-1] = self.price[1:]
        self.price[-1] = price


    def on_bar(self, bar):
        # This function will be called everytime a new bar is generated.
 
        self.update_price(bar.close)
        signal = self.strategy.check_for_trades(self.price)
        if signal is not None:
            print(f"Signal for {self.ticker} is {signal}")
            self.OMS(signal)

def get_instances():
    # Generates System instances for each pair.

    instances = dict()
    for ticker in UNIVERSE:
        instances[ticker] = System(ticker)
    return instances

def get_pnl():

    # Halts trading and stops the algo if account value drops more than 25%.

    # Get account info
    account = api.get_account()

    # Check our current balance vs. our balance at the last market close
    pnl = float(account.equity) - float(account.last_equity)
    ret = 1 - (float(account.equity)/float(account.last_equity))
    if ret > 0.25:
        message = "HALT TRADING ! Account value dropped more than 25%"
        email.send_notification(message)
        api.close_all_positions()
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
    return pnl


if __name__ == "__main__":
    try:
        print("Starting Momentum Algorithm ................")
        message = f"Starting the Momentum Algorithm on {UNIVERSE}"
        email.send_notification(message)
        # generate instances
        instances = get_instances()
        async def OnBar(bar):
             """
             This function will run once a minute on arrival of a minute bar.

             :params bar: (Bar object) the latest minute bar data
             """
             if bar.exchange == EXCHANGE:
                instances[bar.symbol].on_bar(bar)
                print(f"Account PnL : {get_pnl()}")

        # Unique ticker to subscribe
        print(f"Listening to feeds from : {UNIVERSE}")
        # Subscribe to live data
        websocket.subscribe_crypto_bars(OnBar, *UNIVERSE)
        # Start streaming data
        websocket.run()

    except (KeyboardInterrupt, RuntimeError):
        print('Interrupted')
        api.close_all_positions()
        message = f"ALERT ! Momentum Algorithm is INTERUPTED"
        email.send_notification(message)
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
