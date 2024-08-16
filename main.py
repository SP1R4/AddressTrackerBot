import os
import time
import threading
import telebot
from dotenv import load_dotenv
from bot_handler import config_bot, register_handlers
from utils import logger, load_addresses, save_addresses, load_allowed_users
from web3_handler import init_web3, get_eth_transactions, process_transaction


def monitor_addresses(web3, bot, addresses_to_monitor, allowed_users, lock):
    """
    Continuously monitor Ethereum addresses for new transactions and handle errors.
    
    :param addresses_to_monitor: Dictionary of addresses to monitor.
    :param allowed_users: Dictionary of allowed users.
    :param lock: Thread lock for synchronized access.
    """
    while True:
        try:
            with lock:
                for name, info in addresses_to_monitor.items():
                    from_block = info['last_seen_block'] + 1
                    logger.info(f"Checking for new transactions for {name} ({info['ether_address']}) from block {from_block}")
                    
                    try:
                        transactions = get_eth_transactions(info['ether_address'], from_block)
                        if transactions:
                            for tx in transactions:
                                process_transaction(web3, bot, tx, name, info['ether_address'], allowed_users, addresses_to_monitor)
                                # Update the last seen block after processing transactions
                                addresses_to_monitor[name]['last_seen_block'] = tx['blockNumber']
                                save_addresses()  # Save changes after processing transactions
                    except Exception as e:
                        logger.error(f"Error fetching transactions for {name}: {e}")
        
        except Exception as e:
            logger.error(f"Unexpected error in monitoring loop: {e}")

        # Wait before checking for new transactions
        time.sleep(60)

def main():
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    INFURA_PROJECT_ID = os.getenv('INFURA_PROJECT_ID')
    
    web3 = init_web3(INFURA_PROJECT_ID)
    bot = config_bot(TELEGRAM_BOT_TOKEN)
    lock = threading.Lock()
    addresses_by_user = load_addresses()
    allowed_users = load_allowed_users()
    user_state = {}

    register_handlers(bot, lock, addresses_by_user, allowed_users, user_state, web3)
    
    logger.info("Starting bot polling...")
    try:
        bot.polling(none_stop=True, interval=0, timeout=20)
    except Exception as e:
        logger.error(f"Bot polling failed with error: {e}")
        bot.stop_polling()

    polling_interval = 60  # seconds
    while True:
        for chat_id in addresses_by_user:
            for name, info in addresses_by_user[chat_id].items():
                address = info['ether_address']
                last_seen_block = info['last_seen_block']
                latest_block = web3.eth.block_number
                if latest_block > last_seen_block:
                    transactions = get_eth_transactions(web3, address, last_seen_block + 1)
                    for tx in transactions:
                        process_transaction(web3, bot, tx, name, address, allowed_users, addresses_by_user)
                    addresses_by_user[chat_id][name]['last_seen_block'] = latest_block
                    save_addresses(addresses_by_user)

        time.sleep(polling_interval)

if __name__ == "__main__":
    main()
