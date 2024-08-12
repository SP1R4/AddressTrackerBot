import os
import json
import logging
from logging.handlers import RotatingFileHandler


# Configure logging with rotation
log_handler = RotatingFileHandler('monitor.log', maxBytes=1000000, backupCount=3)
log_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(log_handler)


def load_addresses(file_path='addresses.json'):
    """
    Load Ethereum addresses from a JSON file.

    :param file_path: Path to the JSON file containing the addresses.
    :return: A dictionary with Ethereum addresses and their details.
    """
    addresses_to_monitor = {}
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r') as file:
                addresses_to_monitor = json.load(file)
            logger.info("Loaded addresses from file.")
        except Exception as e:
            logger.error(f"Error loading addresses: {e}")
    else:
        logger.info("No existing addresses to load.")
    
    return addresses_to_monitor

def save_addresses(addresses_to_monitor, file_path='addresses.json'):
    """
    Save Ethereum addresses to a JSON file.

    This function writes the current state of the `addresses_to_monitor` dictionary
    to a specified JSON file. It handles any exceptions that may occur during the
    file writing process and logs the error if one occurs.

    :param file_path: Path to the JSON file to save the addresses. Defaults to 'addresses.json'.
    """
    try:
        with open(file_path, 'w') as file:
            json.dump(addresses_to_monitor, file, indent=4)
        logger.info("Addresses saved to file.")
    except Exception as e:
        logger.error(f"Error saving addresses: {e}")

def load_allowed_users(file_path='users.json'):
    """
    Load the allowed users who can interact with the Telegram bot from a JSON file.
    
    :param file_path: Path to the JSON file containing the allowed users.
    :return: A dictionary of allowed users.
    """
    global allowed_users
    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            data = json.load(file)
            allowed_users = {user['username']: user['chat_id'] for user in data['users']}
        logger.info("Loaded allowed users from file.")
        logger.debug(f"Allowed users: {allowed_users}")
        return allowed_users
    else:
        logger.error("No users.json file found. No users are allowed to interact with the bot.")
        return {}

def is_allowed_user(chat_id):
    """
    Check if the provided chat ID belongs to an allowed user.
    
    :param chat_id: The chat ID to check.
    :return: True if the chat ID is allowed, otherwise False.
    """
    return chat_id in allowed_users.values()

def show_addresses(bot, message, addresses_to_monitor):
    """
    Displays the list of Ethereum addresses currently being monitored.

    Constructs a message that lists all Ethereum addresses being monitored along with their names,
    Ethereum addresses, and the last seen block. The message is sent to the user's chat.

    :param bot: The TeleBot instance used to send messages.
    :param message: The message object containing chat details, used to identify where to send the response.
    """
    chat_id = message.chat.id

    # Check if there are any addresses to monitor
    if addresses_to_monitor:
        # Format the address information
        addresses_info = '\n'.join(
            f"🔹 Name: {name}\n"
            f"   Address: {info['ether_address']}\n"
            f"   Last Seen Block: {info['last_seen_block']}\n"
            for name, info in addresses_to_monitor.items()
        )
        # Send the formatted message to the user
        bot.send_message(chat_id, f"📋 Addresses Being Monitored:\n{addresses_info}")
    else:
        # Send a message indicating no addresses are being monitored
        bot.send_message(chat_id, "🚫 No addresses are currently being monitored.")
