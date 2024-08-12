import time
import threading
from dotenv import load_dotenv
#Import bot
from bot_handler import config_bot, register_handlers
#Import util functions
from utils import (logger, 
                   load_addresses, 
                   save_addresses, 
                   load_allowed_users)
#Import web3 handle functions
from web3_handler import (init_web3, 
                          get_eth_transactions, 
                          process_transaction)


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
    """
    Main function to initialize and start the bot, and begin monitoring Ethereum addresses.
    """
    # Load environment variables
    load_dotenv()

    INFURA_PROJECT_ID = 'YOUR_INFURA_KEY'
    TELEGRAM_BOT_TOKEN = 'YOUR_TELEGRAM_KEY'

    # Initialize global variables
    addresses_to_monitor = {}
    allowed_users = {}
    user_state = {}
    lock = threading.Lock()

    # Configure and start the bot
    bot = config_bot(TELEGRAM_BOT_TOKEN)
    web3 = init_web3(INFURA_PROJECT_ID)

    while True:
        try:
            # Load allowed users and addresses
            allowed_users.update(load_allowed_users())
            addresses_to_monitor.update(load_addresses())  # Update with the loaded addresses
            logger.info(f"Allowed users: {allowed_users}")
            logger.info(f"Addresses to monitor: {addresses_to_monitor}")

            # Register bot handlers
            register_handlers(bot, lock, addresses_to_monitor, allowed_users, user_state, web3)
            
            # Start the bot
            bot.polling()

            # Start monitoring thread with required parameters
            monitor_thread = threading.Thread(target=monitor_addresses, args=(web3, bot, addresses_to_monitor, allowed_users, lock), daemon=True)
            monitor_thread.start()

            # Join the monitoring thread to keep it running
            monitor_thread.join()

        except KeyboardInterrupt:
            logger.info("Monitoring stopped by user")
            break
        except Exception as e:
            logger.error(f"Error occurred: {str(e)}. Restarting in 10 seconds...")
            time.sleep(10)  # Wait for 10 seconds before restarting

if __name__ == "__main__":
    main()
