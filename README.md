## Moving-Average-Trading
Trading bot using Alpaca-trade-api. 
Implemented Simple Moving Average Crossover strategy. 
A moving average, also called as rolling average or running average is a used to analyze the time-series data by calculating a series of averages of the different subsets of full dataset. Simple moving average is calculated by adding the the closing price of last n number of days and then diving by the number of days(time-period).
Also implemented email notifications, all trading activities are alerted to the user through email. And it has error logging mechanism, which helps if the bot encounters any unforeseen errors.
Bot is functionally built on python-3.10.4

# alpaca-trade-api-python
`alpaca-trade-api-python` is a python library for the [Alpaca Commission Free Trading API](https://alpaca.markets).
It allows rapid trading algo development easily, with support for
both REST and streaming data interfaces. For details of each API behavior,
please see the online [API document](https://alpaca.markets/docs/api-documentation/api-v2/market-data/alpaca-data-api-v2/).

# Installation 
```bash
$ pip install -r requirements.txt
```

# Execution
* First of all, create a paper trading account on the Alpaca.
* It will allow you the access of API Keys.
* Once the API keys are obtained, copy and paste them into the 'config.cfg' file.
* Then change the ticker symbol according to your choice.
* On completing the above steps run the 'trading_system.py'

## Disclaimer
This trading bot is for educational purposes only and does not constitute an offer to
sell, a solicitation to buy, or a recommendation for any security; nor does it
constitute an offer to provide investment advisory or other services by the
speakers. Nothing contained herein constitutes investment advice or offers any
opinion with respect to the suitability of any security and any views expressed
herein should not be taken as advice to buy, sell, or hold any security or as an
endorsement of any security or company. The owner is not responsible for the
losses incurred due to the buying and selling of securities.
