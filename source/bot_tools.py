from pymongo import MongoClient
import requests
import source.config as config
import logging

from datetime import datetime
from source.config import HEADERS, PARAMS

MONGODB_URI = config.MONGODB_URI
BOT_TOKEN = config.BOT_TOKEN
TOKEN = BOT_TOKEN
HELIUS_KEY = config.HELIUS_KEY
HELIUS_WEBHOOK_URL = config.HELIUS_WEBHOOK_URL
HELIUS_WEBHOOK_ID = config.HELIUS_WEBHOOK_ID

client = MongoClient(MONGODB_URI)
db = client.sol_wallets
wallets_collection = db.wallets_test


# Set up logging
logging.basicConfig(
    filename='bot.log',
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def get_webhook(HELIUS_WEBHOOK_ID):
    try:
        r = requests.get(
            'https://api.helius.xyz/v0/webhooks/8fb7d244-5cc6-49ec-91e1-ed906f36cfdc',
            params=PARAMS,
            headers=HEADERS,
        )
        if r.status_code == 200:
            return True, r.json()['webhookID'], r.json()['accountAddresses']
        else:
            logging.info('error get webhook')
            return False
    except Exception as err:
        print(err)


def add_webhook(user_id, user_wallet, webhook_id, addresses):
    if user_wallet in addresses:
        logging.info('existing wallet, returning true')
        return True
    addresses.append(user_wallet)
    data = {
        "webhookURL": HELIUS_WEBHOOK_URL,
        "accountAddresses": addresses,
        "transactionTypes": ["Any"],
        "webhookType": "enhanced",
    }

    try:
        r = requests.put(
            'https://api.helius.xyz/v0/webhooks/8fb7d244-5cc6-49ec-91e1-ed906f36cfdc',
            json=data,
            params=PARAMS,
            headers=HEADERS
        )
        if r.status_code == 200:
            return True
        else:
            return False
    except Exception as err:
        print(err)

def delete_webhook(user_wallet, addresses):
    url = f'https://api.helius.xyz/v0/webhooks/8fb7d244-5cc6-49ec-91e1-ed906f36cfdc?api-key={HELIUS_KEY}'
    if user_wallet not in addresses:
        return True
    addresses.remove(user_wallet)

    data = {
        "webhookURL": HELIUS_WEBHOOK_URL,
        "accountAddresses": addresses,
        "transactionTypes": ["Any"],
        "webhookType": "enhanced",
    }
    r = requests.put(url, json=data)
    if r.status_code == 200:
        return True
    else:
        return False
    
def is_solana_wallet_address(address):
    base58_chars = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'
    address_length = [32, 44]
    if len(address) < address_length[0]:
        return False

    if len(address) > address_length[1]:
        return False

    for char in address:
        if char not in base58_chars:
            return False

    return True

def wallet_count_for_user(user_id: int) -> int:
    try:
        wallet_count = wallets_collection.count_documents({"user_id": str(user_id), "status": "active"})
        print(wallet_count)
        return wallet_count
    except Exception as err:
        logger.error(f"Error while wallet counting for user: {err}")


def check_wallet_transactions(wallet):

    try:
        url = f'https://api.helius.xyz/v0/addresses/{wallet}/raw-transactions?api-key={HELIUS_KEY}'
        r = requests.get(url)
        j = r.json()
        if len(j) < 10:
            return True, 0
        first_date = datetime.utcfromtimestamp(j[-1]['blockTime'])
        current_date = datetime.now()
        num_txs = len(j)
        delta = (current_date - first_date).total_seconds()
        av_per_day = num_txs / delta * 86400
        if av_per_day > 50:
            return False, av_per_day
        else:
            return True, av_per_day
    except:
        logging.info('ERROR checking wallet txs')
        return True, 0