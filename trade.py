#!/usr/bin/env python3
import warnings
warnings.filterwarnings("ignore")

import requests
import json
import time
import numpy as np
import os

# Retrieve the current price of the ticker from an API
def get_ticker_price():
    price = requests.get('https://www.mercadobitcoin.net/api/BTC/ticker/')
    price = json.loads(price.text)
    return float(price['ticker']['last'])

# Retrieve the trades within a specified time frame from an API
def get_trades(seconds):
    time_now = int(time.time())
    time_then = time_now - seconds
    trades = requests.get('https://www.mercadobitcoin.net/api/BTC/trades/{0}/{1}'.format(time_then, time_now))
    return trades.json()

# Extract a specific key from a list of trades
def extract(trades, a_key):
    extract = []
    for trade in trades:
        extract.append(trade[a_key])
    return extract
    
# Create an environment dictionary with variance and mean price information
def environment(timeframe):
    trades = get_trades(timeframe)
    prices = extract(trades, 'price')
    environment = {
        'variance': np.var(prices), 
        'mean_price': round(np.mean(prices), 2), 
    }
    return environment
    
# Calculate the alpha value based on the current price and mean price
def alpha(current, mean):
    alpha = current - mean
    alpha = alpha / mean
    return abs(alpha)

# Calculate the new order based on the previous order and a new order
def calc_order(new_order, order):
    tmp = {
        'quantity': new_order['quantity'] + order['quantity'],
        'volume': round(new_order['volume'] + order['volume'], 2),
        'timestamp': int(time.time()),
        'profit': round(new_order['profit'], 2),
    }
    if tmp['quantity'] > 0:
        tmp['price'] = round(tmp['volume'] / tmp['quantity'], 2)
    else:
        tmp['price'] = None
        tmp['volume'] = 0.0
    return tmp

# Load the JSON file into a variable
if os.path.isfile('data.json'):
    with open('data.json', 'r') as file:
        order = json.load(file)
else:
    order = {
        'price': None,
        'quantity': 0.0,
        'volume': 0.0,
        'profit': 0.0,
        'timestamp': int(time.time()),
        }

alpha_range = 0.005
profit = 0.0
stop_loss = 0.987
quantity = 0.0001

while True:

    # Environment long and short
    env1 = environment(600)
    env2 = environment(120)        
    
    # Get the current price
    current_price = round(get_ticker_price(), 2)
    
    if env2['variance'] > env1['variance']:
        for i in range(6):
            print(i)
            env3 = environment(60) 
            direction = env2['mean_price'] > env3['mean_price']
                                  
            if env3['variance'] > env2['variance']:
                print('sleep 10')
                time.sleep(10)
                continue
            elif alpha_range > alpha(current_price, env3['mean_price']):
                print('alpha_range condition')
                if direction:
                    new_order = {
                        'price': current_price,
                        'quantity': quantity,
                        'volume': current_price * quantity,
                        'profit': 0.0,
                        'timestamp': int(time.time()),
                        }
                    order = calc_order(new_order, order)
                    
                elif order['volume'] > 0:
                    new_order = {
                        'price': current_price,
                        'quantity': -1 * quantity,
                        'volume': current_price * quantity * -1,
                        'timestamp': int(time.time()),
                        }
                    new_order['profit'] = (quantity * order['price']) + new_order['volume'] + order['profit']
                    order = calc_order(new_order, order)
                    
                print("Got to alpha_range break")
                break
                
            if order['price'] is None:
                print('min_price_order is None, sleep 10')
                time.sleep(10)
                continue
            elif (current_price / order['price']) < stop_loss:
                print('stop_loss reached')
                new_order = {
                        'price': current_price,
                        'quantity': -1 * order['quantity'],
                        'volume': current_price * order['quantity'] * -1,
                        'timestamp': int(time.time()),
                        }
                new_order['profit'] = order['profit'] + new_order['volume'] + order['volume']
                order = calc_order(new_order, order)
                continue
                
    # Writing the dictionary to a JSON file
    print(f'\nTicker: R${current_price:,.2f}')
    print(f'Profit/Loss: R${profit:.2f}')
    print(order)
    with open('data.json', 'w') as file:
        json.dump(order, file)
    time.sleep(60)
