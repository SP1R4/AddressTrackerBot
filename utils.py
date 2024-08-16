import os
import json
import telebot
import logging
from logging.handlers import RotatingFileHandler
from typing import Dict, Any

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
    :return: A dictionary with user chat IDs as keys and their addresses as values.
    """
    addresses_by_user = {}
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r') as file:
                addresses_by_user = json.load(file)
            logger.info("Loaded addresses from file.")
        except Exception as e:
            logger.error(f"Error loading addresses: {e}")
    else:
        logger.info("No existing addresses to load.")
    
    return addresses_by_user

def save_addresses(addresses_by_user):
    """
    Save the current state of addresses being monitored by users to the JSON file.
    
    :param addresses_by_user: The dictionary containing user-specific addresses.
    """
    try:
        with open('addresses.json', 'w') as json_file:
            json.dump(addresses_by_user, json_file, indent=4)
        logger.info("Addresses successfully saved.")
    except Exception as e:
        logger.error(f"Failed to save addresses: {str(e)}")

def load_allowed_users(file_path: str = 'users.json') -> Dict[int, str]:
    """
    Load the allowed users who can interact with the Telegram bot from a JSON file.
    
    :param file_path: Path to the JSON file containing the allowed users.
    :return: A dictionary of allowed users.
    """
    if not os.path.exists(file_path):
        logger.error("No users.json file found. No users are allowed to interact with the bot.")
        return {}

    try:
        with open(file_path, 'r') as file:
            data = json.load(file)
            allowed_users = {user['chat_id']: user['username'] for user in data['users']}
        logger.info("Loaded allowed users from file.")
        logger.debug(f"Allowed users: {allowed_users}")
        return allowed_users
    except Exception as e:
        logger.error(f"Error loading allowed users: {e}")
        return {}

def is_allowed_user(chat_id: int, allowed_users: Dict[int, str]) -> bool:
    """
    Check if the provided chat ID belongs to an allowed user.
    
    :param chat_id: The chat ID to check.
    :param allowed_users: Dictionary of allowed users.
    :return: True if the chat ID is allowed, otherwise False.
    """
    return chat_id in allowed_users

def show_addresses(bot: telebot.TeleBot, message: telebot.types.Message, addresses_to_monitor: Dict[str, Dict[str, Any]]) -> None:
    """
    Displays the list of Ethereum addresses currently being monitored.

    :param bot: The TeleBot instance used to send messages.
    :param message: The message object containing chat details, used to identify where to send the response.
    :param addresses_to_monitor: Dictionary of addresses to monitor.
    """
    chat_id = message.chat.id

    if addresses_to_monitor:
        addresses_info = '\n'.join(
            f"🔹 Name: {name}\n"
            f"   Address: {info['ether_address']}\n"
            f"   Last Seen Block: {info['last_seen_block']}\n"
            for name, info in addresses_to_monitor.items()
        )
        bot.send_message(chat_id, f"📋 Addresses Being Monitored:\n{addresses_info}")
    else:
        bot.send_message(chat_id, "🚫 No addresses are currently being monitored.")
