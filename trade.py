#!/usr/bin/env python3
import warnings
warnings.filterwarnings("ignore")

import requests
import json
import time
import numpy as np
import os

# Function to retrieve the current price of Bitcoin from an API
def get_ticker_price():
    price = requests.get('https://www.mercadobitcoin.net/api/BTC/ticker/')
    price = json.loads(price.text)
    return float(price['ticker']['last'])

# Function to retrieve recent trades within a specified timeframe from an API
def get_trades(seconds):
    time_now = int(time.time())
    time_then = time_now - seconds
    trades = requests.get('https://www.mercadobitcoin.net/api/BTC/trades/{0}/{1}'.format(time_then, time_now))
    return trades.json()

# Function to extract a specific attribute from a list of trades
def extract(trades, a_key):
    extract = []
    for trade in trades:
        extract.append(trade[a_key])
    return extract

# Function to calculate the trading environment
def environment(timeframe):
    trades = get_trades(timeframe)
    prices = extract(trades, 'price')
    environment = {
        'variance': np.var(prices),
        'mean_price': float("%.5f" % np.mean(prices)),
    }
    return environment

# Function to calculate the alpha value
def alpha(current, mean):
    alpha = current - mean
    alpha = alpha / mean
    return abs(alpha)

# Function to calculate the updated order details
def calc_order(new_order, order):
    tmp = {
        'quantity': new_order['quantity'] + order['quantity'],
        'volume': new_order['volume'] + order['volume'],
        'timestamp': int(time.time()),
    }
    if tmp['quantity'] > 0:
        tmp['price'] = tmp['volume'] / tmp['quantity']
    else:
        tmp['price'] = None
        tmp['volume'] = 0.0
    return tmp

# Load the JSON file into a variable to store order details
if os.path.isfile('data.json'):
    with open('data.json', 'r') as file:
        order = json.load(file)
else:
    order = {
        'price': None,
        'quantity': 0.0,
        'volume': 0.0,
        'timestamp': int(time.time()),
    }

# Set up variables for trading parameters
alpha_range = 0.005
profit = 0.0
stop_loss = 0.987
quantity = 0.0001

# Main loop for trading
while True:

    # Calculate long and short trading environments
    env1 = environment(600)
    env2 = environment(120)

    # Get the current price
    current_price = round(get_ticker_price(), 2)

    # Check if short variance is greater than long variance
    if env2['variance'] > env1['variance']:
        for i in range(6):
            print(i)
            # Calculate the current trading environment
            env3 = environment(60)
            direction = env2['mean_price'] > env3['mean_price']

            if env3['variance'] > env2['variance']:
                print('sleep 10')
                time.sleep(10)
                continue
            elif alpha_range > alpha(current_price, env3['mean_price']):
                print('alpha_range condition')
                # Enter a new long position
                if direction:
                    new_order = {
                        'price': current_price,
                        'quantity': quantity,
                        'volume': current_price * quantity,
                        'timestamp': int(time.time()),
                    }
                    order = calc_order(new_order, order)
                # Exit the current position
                elif order['volume'] > 0:
                    new_order = {
                        'price': current_price,
                        'quantity': -1 * order['quantity'],
                        'volume': current_price * order['quantity'] * -1,
                        'timestamp': int(time.time()),
                    }
                    profit = profit + new_order['volume'] - order['volume']
                    order = calc_order(new_order, order)

                print("Got to alpha_range break")
                break

            if order['price'] is None:
                print('min_price_order is None, sleep 10')
                time.sleep(10)
                continue
            elif (current_price / order['price']) < stop_loss:
                print('stop_loss reached')
                # Exit the current position if stop-loss condition is met
                new_order = {
                    'price': current_price,
                    'quantity': -1 * order['quantity'],
                    'volume': current_price * order['quantity'] * -1,
                    'timestamp': int(time.time()),
                }
                profit = profit + new_order['volume'] - order['volume']
                order = calc_order(new_order, order)
                continue

    # Write the order details to a JSON file
    print(f'\nTicker: R${current_price:,.2f}')
    print(f'Profit/Loss: R${profit:.2f}')
    print(order)
    with open('data.json', 'w') as file:
        json.dump(order, file)
    time.sleep(60)
