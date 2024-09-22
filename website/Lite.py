import os
import time
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
from . import  db
from .models import User
from flask import session

USR_INFO = []

def accesstokenchecker(BEARER_TOKENS, key):
    # Get a specific user based on their Lite key
    user = User.query.filter_by(key=key).first()

    # Retrieve all the associated access tokens
    if user:
        access_tokens = [token.token for token in user.access_tokens]
        USR_INFO.append({'username': user.username, 'subscription_type': user.subscription_type})
        for BEARER_TOKEN in BEARER_TOKENS:
            if BEARER_TOKEN[:10] not in access_tokens:
                return False
        return True
    else:
        return False
    
    return False  # Default return if checks don't pass

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
    if USR_INFO[0]['subscription_type'] == 'Speed':
        return accountnumgrabber(BEARER_TOKEN)
    elif USR_INFO[0]['subscription_type'] == 'Platinum':
        netaccs = accountnumgrabber(BEARER_TOKEN)
        if len(netaccs)<=60:
            return netaccs
        else:
            filteredaccs = []
            sortedaccs = accSorter(netaccs)
            for acct in range(1,61):
                filteredaccs.append(sortedaccs[acct])
            return filteredaccs
    elif USR_INFO[0]['subscription_type'] == 'Gold':
        netaccs = accountnumgrabber(BEARER_TOKEN)
        if len(netaccs)<=60:
            return netaccs
        else:
            filteredaccs = []
            sortedaccs = accSorter(netaccs)
            for acct in range(1,31):
                filteredaccs.append(sortedaccs[acct])
            return filteredaccs
    elif USR_INFO[0]['subscription_type'] == 'Silver':
        netaccs = accountnumgrabber(BEARER_TOKEN)
        if len(netaccs)<=8:
            return netaccs
        else:
            filteredaccs = []
            sortedaccs = accSorter(netaccs)
            for acct in range(1,9):
                filteredaccs.append(sortedaccs[acct])
            return filteredaccs

def orderhandler(BEARER_TOKENS, ticker, amount, side, key):
    for BEARER_TOKEN in BEARER_TOKENS:
        if BEARER_TOKEN != '':
            threadHandler(BEARER_TOKEN, ticker, amount, side, key)
            time.sleep(4)

def threadHandler(BEARER_TOKEN, ticker, amount, side, key):
    acclist = accByPlanHandler(BEARER_TOKEN, key)
    ordertype = buyorder if side == "b" else sellorder

    MAX_REQUESTS = 60
    REQUEST_COUNT = 0
    T_0 = time.time()
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(ordertype, BEARER_TOKEN, ticker, amount, account_id) for account_id in acclist]
        success_count = 0
        error_count = 0
        acctswitherror = []
        for future in as_completed(futures):
            try:
                result = future.result()  # Get result
                if result['status_code'] == 200 and "errors" in result['content']:
                    error_count += 1
                    acctswitherror.append(result['account_id'])
                elif result['status_code'] == 200 and "ok" in result['content']:
                    success_count += 1

                # Artificial wait after processing each future
                time.sleep(0.01)

                REQUEST_COUNT += 1  # Increment after each order
                
                if REQUEST_COUNT >= MAX_REQUESTS:
                    T = time.time() - T_0
                    if T <= 60:
                        SLEEP_TIME = 60 - T
                        time.sleep(SLEEP_TIME)
                    REQUEST_COUNT = 0
                    T_0 = time.time()

            except Exception as e:
                # Handle error (e.g., log it or save it somewhere)
                pass
    
    # Create a string to display accounts with errors
    if acctswitherror:
        error_accounts_str = ', '.join(acctswitherror)
        error_message = f" | Accounts with errors: {error_accounts_str}"
    else:
        error_message = " | No accounts encountered errors."

    # Return the complete message including the error accounts
    return(f"Successful orders on {BEARER_TOKEN[0:10]}: {success_count} | Unsuccessful orders: {error_count} for {ticker}{error_message}")
    
                
def buyorder(BEARER_TOKEN, ticker, amount, account_id):
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
    
def sellorder(BEARER_TOKEN, ticker, amount, account_id):
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