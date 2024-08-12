import telebot
from web3 import Web3
import time
import emoji
from utils import logger


def init_web3(INFURA_PROJECT_ID):
    """
    Initialize a Web3 instance connected to the Ethereum network via Infura.
    
    :param INFURA_PROJECT_ID: Infura project ID for accessing the Ethereum network.
    :return: Web3 instance connected to the Ethereum network.
    :raises Exception: If the connection to Infura fails.
    """
    infura_url = f'https://mainnet.infura.io/v3/{INFURA_PROJECT_ID}'
    web3 = Web3(Web3.HTTPProvider(infura_url))
    if not web3.is_connected():
        logger.error("Failed to connect to Infura")
        raise Exception("Failed to connect to Infura")
    logger.info("Successfully connected to Infura")
    return web3

def get_eth_balance(web3, address):
    """
    Fetch the Ethereum balance of a given address.
    
    :param web3: Web3 instance used for interacting with the Ethereum network.
    :param address: Ethereum address whose balance is to be fetched.
    :return: Balance in ETH or None if there was an error.
    """
    try:
        balance = web3.eth.get_balance(address)
        return web3.fromWei(balance, 'ether')
    except Exception as e:
        logger.error(f"Error fetching balance for {address}: {e}")
        return None

def process_transaction(web3, bot, tx, name, address, allowed_users, addresses_to_monitor):
    """
    Process an Ethereum transaction and notify allowed users.
    
    :param web3: Web3 instance used for interacting with the Ethereum network.
    :param bot: TeleBot instance used to send notifications.
    :param tx: Transaction data to process.
    :param name: Name associated with the Ethereum address.
    :param address: Ethereum address related to the transaction.
    :param allowed_users: Dictionary of users who are allowed to receive notifications.
    :param addresses_to_monitor: Dictionary of addresses being monitored.
    """
    try:
        tx_hash = tx['transactionHash'].hex()
        try:
            tx_receipt = web3.eth.getTransactionReceipt(tx_hash)
            if tx_receipt:
                from_address = tx_receipt['from']
                to_address = tx_receipt['to']
                value = web3.fromWei(web3.eth.getTransaction(tx_hash)['value'], 'ether')
                block_number = int(tx_receipt['blockNumber'])
                block_timestamp = web3.eth.getBlock(block_number)['timestamp']
                formatted_timestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(block_timestamp))
                alert_emoji = emoji.emojize(":rotating_light:")
                message = (f"{alert_emoji} New transaction for {name} ({address}):\n"
                           f"Hash: {tx_hash}\n"
                           f"From: {from_address}\n"
                           f"To: {to_address}\n"
                           f"Value: {value} ETH\n"
                           f"Block Number: {block_number}\n"
                           f"Timestamp: {formatted_timestamp}\n"
                           "------")
                logger.info(f"Constructed message: {message}")
                if message.strip():
                    for username, chat_id in allowed_users.items():
                        try:
                            bot.send_message(chat_id, message)
                        except telebot.apihelper.ApiTelegramException as e:
                            logger.error(f"Failed to send message to {username} ({chat_id}): {str(e)}")
                addresses_to_monitor[name]['last_seen_block'] = block_number
        except Exception as e:
            logger.error(f"Error processing transaction {tx_hash} for {name} ({address}): {str(e)}")

    except Exception as e:
        logger.error(f"Error processing transaction for {name} ({address}): {str(e)}")

def show_address_history(web3, bot, lock, message, address_name, addresses_to_monitor):
    """
    Show the transaction history for a specific Ethereum address.
    
    :param web3: Web3 instance used for interacting with the Ethereum network.
    :param bot: TeleBot instance used to send messages.
    :param lock: Thread lock for synchronized access.
    :param message: Received message object containing chat details.
    :param address_name: Name of the Ethereum address to fetch history for.
    :param addresses_to_monitor: Dictionary of addresses being monitored.
    """
    chat_id = message.chat.id
    with lock:
        address_info = addresses_to_monitor.get(address_name)
        if address_info:
            address = address_info['ether_address']
            from_block = address_info['last_seen_block'] + 1
            transactions = get_eth_transactions(web3, address, from_block)
            if transactions:
                history_message = "\n".join(
                    f"Hash: {tx['transactionHash'].hex()}\n"
                    f"From: {tx['from']}\n"
                    f"To: {tx['to']}\n"
                    f"Value: {web3.fromWei(tx['value'], 'ether')} ETH\n"
                    f"Block Number: {tx['blockNumber']}\n"
                    for tx in transactions
                )
                bot.send_message(chat_id, f"Transaction History for {address_name}:\n{history_message}")
            else:
                bot.send_message(chat_id, "No transactions found.")
        else:
            bot.send_message(chat_id, f"Address with name '{address_name}' not found.")

def show_address_details(web3, bot, lock, message, address_name, addresses_to_monitor):
    """
    Show the details of a specific Ethereum address.
    
    Retrieves and displays information about the given Ethereum address, including the address itself,
    the last seen block, and the current balance. The details are sent to the user's chat.
    
    :param bot: The TeleBot instance used to send messages.
    :param lock: Thread lock for synchronized access.
    :param message: The received message object containing chat details.
    :param address_name: The name of the Ethereum address for which details are to be shown.
    :param addresses_to_monitor: Dictionary of addresses being monitored.
    """
    chat_id = message.chat.id
    with lock:
        address_info = addresses_to_monitor.get(address_name)

        if address_info:
            address = address_info['ether_address']
            last_seen_block = address_info['last_seen_block']
            balance = get_eth_balance(web3, address)
            
            if balance is None:
                balance = "Error fetching balance"

            details_message = (f"📋 *Details for {address_name}:*\n"
                               f"🔹 Address: {address}\n"
                               f"🔹 Last Seen Block: {last_seen_block}\n"
                               f"🔹 Current Balance: {balance} ETH")
            bot.send_message(chat_id, details_message, parse_mode='Markdown')
        else:
            bot.send_message(chat_id, f"❌ Address with name '{address_name}' not found.")

def is_valid_ethereum_address(address):
    """
    Validate if the provided address is a valid Ethereum address.
    
    :param address: The Ethereum address to validate.
    :return: True if the address is valid, False otherwise.
    """
    web3 = Web3()
    return web3.is_address(address)

def get_eth_transactions(web3, address, from_block):
    """
    Retrieve Ethereum transactions for a given address starting from a specific block.
    
    :param web3: Web3 instance used for interacting with the Ethereum network.
    :param address: The Ethereum address to monitor.
    :param from_block: The block number to start monitoring from.
    :return: List of transactions or an empty list if none are found or an error occurs.
    """
    try:
        logs = web3.eth.get_logs({
            'fromBlock': from_block,
            'toBlock': 'latest',
            'address': address
        })
        return [web3.eth.get_transaction(log['transactionHash']) for log in logs]
    except (ConnectionError) as e:
        logger.error(f"Network error while fetching logs for {address}: {str(e)}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error while fetching logs for {address}: {str(e)}")
        return []
