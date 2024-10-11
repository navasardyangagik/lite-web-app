import requests
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Event
import json

# Function to get all orders for a specific account
def get_order_ids_for_ticker(account_id, token, ticker, quantity=1):
    url = f'https://api.tradier.com/v1/accounts/{account_id}/orders'
    headers = {
        'Authorization': f'Bearer {token}',
        'Accept': 'application/json'
    }
    params = {
        'includeTags': 'true'
    }
    
    response = requests.get(url, headers=headers, params=params)
    
    if response.status_code == 200:
        orders = response.json().get('orders', {}).get('order', [])
        matching_orders = [order['id'] for order in orders if order['symbol'] == ticker and order['quantity'] == quantity]
        return matching_orders
    else:
        return []

# Function to cancel an order by ID
def cancel_order(account_id, token, order_id):
    url = f'https://api.tradier.com/v1/accounts/{account_id}/orders/{order_id}'
    headers = {
        'Authorization': f'Bearer {token}',
        'Accept': 'application/json'
    }

    try:
        # Send the DELETE request to cancel the order
        response = requests.delete(url, headers=headers)

        # Return a structured dictionary with relevant data
        return {
            'status_code': response.status_code,
            'content': response.json() if response.headers.get('Content-Type') == 'application/json' else response.text,
            'account_id': account_id
        }

    except requests.exceptions.RequestException as e:
        # Handle any request-related errors
        return {
            'status_code': None,
            'content': str(e),
            'account_id': account_id
        }

# Function to grab accounts (dummy function - replace with actual implementation)
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

def cancel_threadHandler(BEARER_TOKEN, ticker, accts):
    MAX_REQUESTS = 100
    REQUEST_COUNT = 0
    T_0 = time.time()

    success_count = 0
    error_count = 0
    acctswitherror = set()  # Change to a set to avoid duplicates

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(cancel_orders_for_account, BEARER_TOKEN, ticker, account_id): account_id for account_id in accts}

        for future in as_completed(futures):
            account_id = futures[future]
            try:
                result = future.result()
                for res in result:
                    if res['status_code'] == 200:
                        try:
                            content = res['content'] if isinstance(res['content'], dict) else json.loads(res['content'])
                            if content.get('order', {}).get('status') == 'ok':
                                success_count += 1
                            else:
                                error_count += 1
                                acctswitherror.add(account_id)  # Add to set for any non-ok status
                        except json.JSONDecodeError:
                            error_count += 1
                            acctswitherror.add(account_id)  # Add to set for JSON errors
                    else:
                        error_count += 1
                        acctswitherror.add(account_id)  # Add to set for failed requests

            except Exception as e:
                error_count += 1
                acctswitherror.add(account_id)  # Add to set for exceptions

            REQUEST_COUNT += 1
            # Handle rate limiting
            if REQUEST_COUNT >= MAX_REQUESTS:
                T = time.time() - T_0
                if T < 60:
                    SLEEP_TIME = 60 - T
                    time.sleep(SLEEP_TIME)
                REQUEST_COUNT = 0
                T_0 = time.time()

    # Convert set back to list for displaying
    if acctswitherror:
        error_accounts_str = ', '.join(acctswitherror)
        error_message = f" | Accounts with errors: {error_accounts_str}"
    else:
        error_message = " | No accounts encountered errors."

    return f"Successful cancellations on {BEARER_TOKEN[:10]}: {success_count} | Unsuccessful: {len(accts)-success_count} for {ticker}{error_message}"


# Function to cancel all orders for an account for a specific stock ticker
def cancel_orders_for_account(BEARER_TOKEN, ticker, account_id):
    order_ids = get_order_ids_for_ticker(account_id, BEARER_TOKEN, ticker)
    
    results = []  # Collect results from all cancellations
    
    for order_id in order_ids:
        result = cancel_order(account_id, BEARER_TOKEN, order_id)  # Get the result of each cancellation
        results.append(result)  # Append result to the list
    
    return results  # Return the list of results