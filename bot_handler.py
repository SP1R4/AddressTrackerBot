import telebot
import threading
from telebot import types
from typing import Dict
from utils import is_allowed_user, save_addresses, show_addresses, load_addresses
from web3_handler import is_valid_ethereum_address


def config_bot(token: str) -> telebot.TeleBot:
    """
    Configures and returns a new instance of the Telegram bot.
    
    :param token: The token for authenticating the bot with Telegram.
    :return: A configured TeleBot instance.
    """
    return telebot.TeleBot(token)

def register_handlers(bot, lock, addresses_by_user, allowed_users, user_state, web3):
    @bot.message_handler(commands=['start'])
    def handle_start_help(message):
        chat_id = message.chat.id
        if not is_allowed_user(chat_id, allowed_users):
            bot.reply_to(message, "🚫 Unauthorized access.")
            return
        welcome_message = (
            "👋 Welcome to the WalletTracker bot!\n\n"
            "📜 *Available commands:*\n"
            "• /start - Displays a welcome message and available commands.\n"
            "• /addAddress - 📥 Add a new Ethereum address to your monitoring list.\n"
            "• /rmAddress - ❌ Remove an Ethereum address from your monitoring list.\n"
            "• /show - 📊 Display a list of all Ethereum addresses currently being monitored.\n"
        )
        bot.send_message(chat_id, welcome_message, parse_mode='Markdown')

    @bot.message_handler(commands=['addAddress'])
    def handle_add(message):
        chat_id = message.chat.id
        if not is_allowed_user(chat_id, allowed_users):
            bot.reply_to(message, "🚫 Unauthorized access.")
            return

        bot.send_message(chat_id, "Please enter the Ethereum address:")
        bot.register_next_step_handler(message, add_address)

    def add_address(message):
        chat_id = message.chat.id
        address = message.text.strip()

        if not is_valid_ethereum_address(address):
            bot.send_message(chat_id, "❌ Invalid Ethereum address. Please enter a valid address.")
            return

        bot.send_message(chat_id, "Please enter a name for the address (use '_' instead of spaces):")
        bot.register_next_step_handler(message, handle_name, address)

    def handle_name(message, address):
        chat_id = message.chat.id
        name = message.text.strip()

        if ' ' in name:
            bot.send_message(chat_id, "Name cannot contain spaces. Please use '_' instead of spaces.")
            return

        if not name:
            bot.send_message(chat_id, "Name cannot be empty.")
            return

        addresses_by_user = load_addresses()
        user_addresses = addresses_by_user.get(str(chat_id), {})

        if name in user_addresses:
            bot.send_message(chat_id, f"Address with name '{name}' already exists.")
            return

        user_addresses[name] = {
            'ether_address': address,
            'last_seen_block': web3.eth.block_number
        }
        addresses_by_user[str(chat_id)] = user_addresses
        save_addresses(addresses_by_user)
        bot.send_message(chat_id, f"✅ Added Ethereum address '{name}': '{address}'.")
        
    @bot.message_handler(commands=['rmAddress'])
    def handle_remove(message):
        chat_id = message.chat.id
        if not is_allowed_user(chat_id, allowed_users):
            bot.reply_to(message, "🚫 Unauthorized access.")
            return

        addresses_by_user = load_addresses()
        user_addresses = addresses_by_user.get(str(chat_id), {})

        if not user_addresses:
            bot.send_message(chat_id, "❌ No addresses available to remove.")
            return

        markup = types.InlineKeyboardMarkup()
        for name in user_addresses:
            markup.add(types.InlineKeyboardButton(name, callback_data=f'remove_{name}'))

        bot.send_message(chat_id, "🔍 Please select the address to remove:", reply_markup=markup)
        user_state[chat_id] = {'stage': 'awaiting_address'}

    @bot.callback_query_handler(func=lambda call: call.data.startswith('remove_'))
    def handle_address_removal(call):
        chat_id = call.message.chat.id
        address_name = call.data[len('remove_'):]

        if chat_id not in user_state or user_state[chat_id]['stage'] != 'awaiting_address':
            bot.send_message(chat_id, "⚠️ Unexpected error. Please try the command again.")
            return

        addresses_by_user = load_addresses()
        user_addresses = addresses_by_user.get(str(chat_id), {})

        if address_name in user_addresses:
            del user_addresses[address_name]
            if not user_addresses:
                del addresses_by_user[str(chat_id)]
            else:
                addresses_by_user[str(chat_id)] = user_addresses
            save_addresses(addresses_by_user)
            bot.send_message(chat_id, f"✅ Removed address with name '{address_name}' from your monitoring list.")
        else:
            bot.send_message(chat_id, f"❌ Address with name '{address_name}' not found in your monitoring list.")

        if chat_id in user_state:
            del user_state[chat_id]

        bot.answer_callback_query(call.id)

    @bot.message_handler(commands=['show'])
    def handle_show(message):
        chat_id = message.chat.id
        if not is_allowed_user(chat_id, allowed_users):
            bot.reply_to(message, "🚫 Unauthorized access.")
            return

        # Load the user-specific addresses from the JSON file
        addresses_by_user = load_addresses()  # Ensure this function loads the data correctly

        # Access the user's addresses
        user_addresses = addresses_by_user.get(str(chat_id), {})

        # Show addresses
        show_addresses(bot, message, user_addresses)
