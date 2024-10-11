import os
import time
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock, Event
from . import  db
from .models import User
from flask import session, current_app

def accesstokenchecker(BEARER_TOKENS, key):
    # Get a specific user based on their Lite key
    user = User.query.filter_by(key=key).first()

    # Retrieve all the associated access tokens
    if user:
        access_tokens = [token.token for token in user.access_tokens]
        for BEARER_TOKEN in BEARER_TOKENS:
            if BEARER_TOKEN[:10] not in access_tokens:
                return False
        return True
    else:
        return False
    

def accountnumgrabber(BEARER_TOKEN):
    # Grabs all accounts
    response = requests.get('https://api.tradier.com/v1/user/profile',
        params={},
        headers={'Authorization': f'Bearer {BEARER_TOKEN}', 'Accept': 'application/json'}
    )
    json_response = response.json()
    accounts = json_response['profile']['account']
    if type(accounts) is dict:
        acclist = []
        acclist.append(accounts['account_number'])
        return acclist
    if type(accounts) is list:
        acclist = []
        for i in range(len(accounts)):
            acclist.append(accounts[i]['account_number'])
        return acclist

def accSorter(acclist):
    sorted_accounts = sorted(acclist, key=lambda x: x[-5:])
    return sorted_accounts

def accByPlanHandler(BEARER_TOKEN, key):
    user = User.query.filter_by(key=key).first()

    if not user:
        return None
    
    subscription_type = user.subscription_type

    if subscription_type == 'Speed':
        return accountnumgrabber(BEARER_TOKEN)
    elif subscription_type == 'Exclusive':
        netaccs = accountnumgrabber(BEARER_TOKEN)
        if len(netaccs)<=100:
            return netaccs
        else:
            filteredaccs = []
            sortedaccs = accSorter(netaccs)
            for acct in range(1,101):
                filteredaccs.append(sortedaccs[acct])
            return filteredaccs
    elif subscription_type == 'Platinum':
        netaccs = accountnumgrabber(BEARER_TOKEN)
        if len(netaccs)<=60:
            return netaccs
        else:
            filteredaccs = []
            sortedaccs = accSorter(netaccs)
            for acct in range(1,61):
                filteredaccs.append(sortedaccs[acct])
            return filteredaccs
    elif subscription_type == 'Gold':
        netaccs = accountnumgrabber(BEARER_TOKEN)
        if len(netaccs)<=30:
            return netaccs
        else:
            filteredaccs = []
            sortedaccs = accSorter(netaccs)
            for acct in range(1,31):
                filteredaccs.append(sortedaccs[acct])
            return filteredaccs
    elif subscription_type == 'Silver':
        netaccs = accountnumgrabber(BEARER_TOKEN)
        if len(netaccs)<=8:
            return netaccs
        else:
            filteredaccs = []
            sortedaccs = accSorter(netaccs)
            for acct in range(1,9):
                filteredaccs.append(sortedaccs[acct])
            return filteredaccs

def threadHandler(BEARER_TOKEN, ticker, amount, side, accts, ordertype, price, duration):
    acclist = accts
    orderside = buyorder if side == "b" else sellorder

    MAX_REQUESTS = 100
    REQUEST_COUNT = 0
    T_0 = time.time()

    success_count = 0
    error_count = 0
    acctswitherror = []
    rate_limit_needed = len(acclist) > MAX_REQUESTS

    # Create a ThreadPoolExecutor, but we’ll submit jobs to it manually after rate-limiting checks
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {}

        for i, account_id in enumerate(acclist):
            # Submit a new task to the thread pool
            futures[executor.submit(orderside, BEARER_TOKEN, ticker, amount, account_id, ordertype, price, duration)] = account_id

            REQUEST_COUNT += 1

            # Handle rate-limiting every MAX_REQUESTS (e.g., 2 requests)
            if rate_limit_needed and REQUEST_COUNT >= MAX_REQUESTS:
                T = time.time() - T_0
                if T < 60:
                    SLEEP_TIME = 60 - T
                    time.sleep(SLEEP_TIME)  # Make this blocking to wait before continuing
                REQUEST_COUNT = 0  # Reset request count
                T_0 = time.time()  # Reset timer for next block

        # Process completed tasks as before
        for future in as_completed(futures):
            account_id = futures[future]
            try:
                result = future.result()
                # print(result)
                if result['status_code'] == 200 and "ok" in result['content']:
                    success_count += 1
                else:
                    error_count += 1
                    acctswitherror.append(account_id)
            except Exception as e:
                error_count += 1
                acctswitherror.append(account_id)

    if acctswitherror:
        error_accounts_str = ', '.join(acctswitherror)
        error_message = f" | Accounts with errors: {error_accounts_str}"
    else:
        error_message = " | No accounts encountered errors."

    return f"Successful orders on {BEARER_TOKEN[0:10]}: {success_count} | Unsuccessful orders: {error_count} for {ticker}{error_message}"
                
def buyorder(BEARER_TOKEN, ticker, amount, account_id, ordertype, price, duration):
    if ordertype == 'Market':
        # Information for request that will be sent
        headers = {
            'Authorization': f'Bearer {BEARER_TOKEN}', 
            'Accept': 'application/json'
        }
        order_data = {
            'class': 'equity',
            'symbol': ticker,
            'side': 'buy',
            'quantity': amount,
            'type': 'market',
            'duration': 'day'
        }

        urlorder = f'https://api.tradier.com/v1/accounts/{account_id}/orders'
        try:
            # Send the POST request to place the order
            buyresponse = requests.post(urlorder, data=order_data, headers=headers)

            # Return a structured dictionary with relevant data
            return {
                'status_code': buyresponse.status_code,
                'content': buyresponse.json() if buyresponse.headers.get('Content-Type') == 'application/json' else buyresponse.text,
                'account_id': account_id
            }

        except requests.exceptions.RequestException as e:
            # Handle any request-related errors
            return {
                'status_code': None,
                'content': str(e),
                'account_id': account_id
            }
    elif ordertype == 'Limit':
        # Information for request that will be sent
        headers = {
            'Authorization': f'Bearer {BEARER_TOKEN}', 
            'Accept': 'application/json'
        }
        order_data = {
            'class': 'equity',
            'symbol': ticker,
            'side': 'buy',
            'quantity': amount,
            'type': 'limit',
            'duration': f'{duration}',
            'price': f'{price}'
        }

        urlorder = f'https://api.tradier.com/v1/accounts/{account_id}/orders'
        try:
            # Send the POST request to place the order
            buyresponse = requests.post(urlorder, data=order_data, headers=headers)
            # print(buyresponse.json() if buyresponse.headers.get('Content-Type') == 'application/json' else buyresponse.text)

            # Return a structured dictionary with relevant data
            return {
                'status_code': buyresponse.status_code,
                'content': buyresponse.json() if buyresponse.headers.get('Content-Type') == 'application/json' else buyresponse.text,
                'account_id': account_id
            }

        except requests.exceptions.RequestException as e:
            # Handle any request-related errors
            return {
                'status_code': None,
                'content': str(e),
                'account_id': account_id
            }
        

    
def sellorder(BEARER_TOKEN, ticker, amount, account_id, ordertype, price, duration):
    if ordertype == 'Market':
        # Information for request that will be sent
        headers = {
            'Authorization': f'Bearer {BEARER_TOKEN}', 
            'Accept': 'application/json'
        }
        order_data = {
            'class': 'equity',
            'symbol': ticker,
            'side': 'sell',
            'quantity': amount,
            'type': 'market',
            'duration': 'day'
        }

        urlorder = f'https://api.tradier.com/v1/accounts/{account_id}/orders'
        try:
            # Send the POST request to place the order
            sellresponse = requests.post(urlorder, data=order_data, headers=headers)

            # Return a structured dictionary with relevant data
            return {
                'status_code': sellresponse.status_code,
                'content': sellresponse.json() if sellresponse.headers.get('Content-Type') == 'application/json' else sellresponse.text,
                'account_id': account_id
            }

        except requests.exceptions.RequestException as e:
            # Handle any request-related errors
            return {
            'status_code': None,
            'content': str(e),
            'account_id': account_id
            }
    elif ordertype == 'Limit':
        # Information for request that will be sent
        headers = {
            'Authorization': f'Bearer {BEARER_TOKEN}', 
            'Accept': 'application/json'
        }
        order_data = {
            'class': 'equity',
            'symbol': ticker,
            'side': 'sell',
            'quantity': amount,
            'type': 'limit',
            'duration': f'{duration}',
            'price': f'{price}'
        }

        urlorder = f'https://api.tradier.com/v1/accounts/{account_id}/orders'
        try:
            # Send the POST request to place the order
            sellresponse = requests.post(urlorder, data=order_data, headers=headers)

            # Return a structured dictionary with relevant data
            return {
                'status_code': sellresponse.status_code,
                'content': sellresponse.json() if sellresponse.headers.get('Content-Type') == 'application/json' else sellresponse.text,
                'account_id': account_id
            }

        except requests.exceptions.RequestException as e:
            # Handle any request-related errors
            return {
            'status_code': None,
            'content': str(e),
            'account_id': account_id
            }