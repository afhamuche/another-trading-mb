#!/usr/bin/env python3
import warnings
warnings.filterwarnings("ignore")

import requests
import json
import time
import numpy as np
import os

def get_ticker_price():
    price = requests.get('https://www.mercadobitcoin.net/api/BTC/ticker/')
    price = json.loads(price.text)
    return float(price['ticker']['last'])

def get_trades(seconds):
    time_now = int(time.time())
    time_then = time_now - seconds
    trades = requests.get('https://www.mercadobitcoin.net/api/BTC/trades/{0}/{1}'.format(time_then, time_now))
    return trades.json()

def extract(trades, a_key):
    extract = []
    for trade in trades:
        extract.append(trade[a_key])
    return extract
    
def environment(timeframe):
    trades = get_trades(timeframe)
    prices = extract(trades, 'price') 
    mean = round(np.mean(prices), 2)
    environment = {
        'variance': round(np.var(prices), 2), 
        'mean_price': mean, 
        'alpha': alpha(get_ticker_price(), mean),
        }
    return environment
    
def alpha(current, mean):
    alpha = current - mean
    alpha = alpha / mean
    return round(alpha * 100, 4)

def calc_order(new_order, order):
    tmp = {
        'quantity': new_order['quantity'] + order['quantity'],
        'volume': round(new_order['volume'] + order['volume'], 2),
        'timestamp': int(time.time()),
        'profit': round(new_order['profit'], 2),
        'stoploss': order['stoploss'],
        'budget': round(new_order['budget'] + new_order['profit'], 2),
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
        'status': 'ON',
        'stoploss': 0,
        'budget': 1000.0,
        }

alpha_range = 0.5
profit = 0.0
stop_loss = 0.987
quantity = 0.0001

while True:
    
    print('\n- - - - - - - - - - - - - - - - - - - - - - - - - - - - - -\n')
    
    # Environment long and short
    env1 = environment(3600)
    env2 = environment(600)        
    print(f'env1: {env1}\nenv2: {env2}')
    
    # Get the current price
    current_price = round(get_ticker_price(), 2)
    order['ticker'] = current_price
    order['timestamp'] = int(time.time())
    order['status'] = 'pre-conditions'
    
    if order['price'] is not None and (current_price / order['price']) < stop_loss:
        print('stop_loss reached')
        new_order = {
            'price': current_price,
            'quantity': -1 * order['quantity'],
            'volume': current_price * order['quantity'] * -1,
            'timestamp': int(time.time()),
            }
        order['stoploss'] += 1
        new_order['profit'] = new_order['volume'] + order['volume'] + order['profit']
        new_order['budget'] = order['budget'] + new_order['profit']
        order = calc_order(new_order, order)
        order['status'] = f'stoploss {quantity} @ R${current_price}'
        print(order)
        time.sleep(60)
        continue
    
    if env2['variance'] > env1['variance']:
        env2 = environment(300)  
        for i in range(4):
            
            order['status'] = 'for: var2 > var1'
            print(order)
            time.sleep(15)
            env3 = environment(120) 
            print(f'env3: {env3}\nenv4: {env2}')
            direction = env3['alpha'] != abs(env3['alpha'])
            
            # if env3['alpha'] > env2['alpha']:
                # order['status'] = 'break: alpha3 > alpha2'
                # break
                
            if alpha_range > env3['alpha']:
                print('alpha_range condition')
                order['status'] = 'alpha_range > alpha3'
                volume = current_price * quantity
                
                if direction and order['budget'] > volume:
                    new_order = {
                        'price': current_price,
                        'quantity': quantity,
                        'volume': volume,
                        'profit': order['profit'],
                        'timestamp': int(time.time()),
                        }
                    new_order['budget'] = order['budget'] - new_order['volume']
                    order = calc_order(new_order, order)
                    order['status'] = f'buy {quantity} @ R${current_price}'
                   
                    
                elif not direction and order['volume'] > 0:
                    new_order = {
                        'price': current_price,
                        'quantity': -1 * quantity,
                        'volume': current_price * quantity * -1,
                        'timestamp': int(time.time()),
                        }
                    new_order['profit'] = (quantity * order['price']) + new_order['volume'] + order['profit']
                    new_order['budget'] = order['budget'] - new_order['volume'] + new_order['profit']
                    order = calc_order(new_order, order)
                    order['status'] = f'sell {quantity} @ R${current_price}'
                    
                    
                print("Got to alpha_range break")
                break
                
    # Writing the dictionary to a JSON file
    print(f'\nTicker: R${current_price:,.2f}')
    print(f'Profit/Loss: R${order["profit"]:.2f}')
    print(order)
    with open('data.json', 'w') as file:
        json.dump(order, file)
    time.sleep(60)
