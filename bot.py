import dontshare as d
from eth_account.signers.local import LocalAccount
import eth_account
import json
import time
from hyperliquid.info import Info
from hyperliquid.exchange import Exchange
from hyperliquid.utils import constants
import ccxt
import pandas as pd
import datetime
import schedule
import requests

symbol = 'WIF'
timeframe = '4h'
size = 10

def ask_bid(symbol):
    # This gets the ask and bid for any symbol passed in 

    url = 'http://api.hyperliquid.xyz/info'
    headers = {'Content-Type': 'application/json'}

    data = {
        'type': 'l2book',
        'coin': symbol
    }

    response = requests.post(url, headers=headers, data=json.dumps(data))

    if response.status_code != 200:
        print(f"Error: Received status code {response.status_code}")
        return None, None, None

    try:
        l2_data = response.json()
        l2_data = l2_data['levels']
    except json.JSONDecodeError as e:
        print(f"JSONDecodeError: {e}")
        return None, None, None

    # Get ask and bid 
    bid = float(l2_data[0][0]['px'])
    ask = float(l2_data[1][0]['px'])

    return ask, bid, l2_data

def get_sz_px_decimals(symbol):
    ''' This returns size decimals and price decimals '''

    url = 'http://api.hyperliquid.xyz/info'
    headers = {'Content-Type': 'application/json'}
    data = {'type': 'meta'}

    response = requests.post(url, headers=headers, data=json.dumps(data))

    if response.status_code == 200:
        data = response.json()
        symbols = data['universe']
        symbol_info = next((s for s in symbols if s['name'] == symbol), None)
        if symbol_info:
            sz_decimals = symbol_info['szDecimals']
        else:
            print('Symbol not found')
            return None, None
    else:
        print('Error', response.status_code)
        return None, None

    ask = ask_bid(symbol)[0]

    ask_str = str(ask)
    if '.' in ask_str:
        px_decimals = len(ask_str.split('.')[1])
    else:
        px_decimals = 0

    print(f'{symbol} this is the price {sz_decimals} decimals')

    return sz_decimals, px_decimals

# Make a Buy and a Sell Order
def limit_order(coin, is_buy, sz, limit_px, reduce_only, account):
    exchange = Exchange(account, constants.MAINNET_API_URL)
    rounding = get_sz_px_decimals(coin)[0]
    sz = round(sz, rounding)
    print(f'coin: {coin}, type: {type(coin)}')
    print(f'is_buy: {is_buy}, type: {type(is_buy)}')
    print(f'sz: {sz}, type: {type(sz)}')
    print(f'limit_px: {limit_px}, type: {type(limit_px)}')
    print(f'reduce_only: {reduce_only}, type: {type(reduce_only)}')

    print(f'placing limit order for {coin} {sz} @ {limit_px}')
    order_result = exchange.order(coin, is_buy, sz, limit_px, {"limit": {"tif": 'Gtc'}}, reduce_only=reduce_only)

    if is_buy:
        print(f"limit BUY order placed thanks moon dev, resting {order_result['response']['data']['statuses'][0]}")
    else:
        print(f"limit SELL order placed thanks moon dev, resting {order_result['response']['data']['statuses'][0]}")

    return order_result

coin = symbol
is_buy = True  # False = Sell
ask, bid, l2 = ask_bid(coin)
reduce_only = False
secret_key = d.private_key
account = eth_account.Account.from_key(secret_key)

# Buy order
if bid:
    limit_order(coin, is_buy, size, bid, reduce_only, account)

time.sleep(5)

is_buy = False
reduce_only = True
# Sell Order
if ask:
    limit_order(coin, is_buy, size, ask, reduce_only, account)