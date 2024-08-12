import telebot
from telebot import types
#Import utils functions
from utils import (is_allowed_user, 
                   save_addresses, 
                   show_addresses)
#Import Web handle functions
from web3_handler import (show_address_details, 
                          show_address_history)


def config_bot(TELEGRAM_BOT_TOKEN):
    """
    Configures and returns a new instance of the Telegram bot.
    
    :param TELEGRAM_BOT_TOKEN: The token for authenticating the bot with Telegram.
    :return: A configured TeleBot instance.
    """
    bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)
    return bot

def register_handlers(bot, lock, addresses_to_monitor, allowed_users, user_state, web3):
    """
    Registers handlers for various bot commands and callback queries.
    
    :param bot: The TeleBot instance to register handlers for.
    :param web3: The Web3 instance for interacting with the Ethereum blockchain.
    """
    
    @bot.message_handler(commands=['start'])
    def handle_start_help(message):
        """
        Handles the /start command by sending a welcome message and listing available commands.
        
        :param message: The received message object.
        """
        if not is_allowed_user(message.chat.id):
            bot.reply_to(message, "🚫 Unauthorized access.")
            return
        welcome_message = (
            "👋 Welcome to the WalletTracker bot!\n\n"
            "📜 *Available commands:*\n"
            "• /addAddress - 📥 Add a new Ethereum address to the monitoring list.\n"
            "• /rmAddress - ❌ Remove an Ethereum address from the monitoring list.\n"
            "• /show - 📊 Display a list of all Ethereum addresses currently being monitored.\n"
        )
        bot.send_message(message.chat.id, welcome_message, parse_mode='Markdown')

    @bot.message_handler(commands=['addAddress'])
    def handle_add(message):
        if not is_allowed_user(message.chat.id):
            bot.reply_to(message, "🚫 Unauthorized access.")
            return
        bot.send_message(message.chat.id, "Please enter the Ethereum address:")
        bot.register_next_step_handler(message, add_address)

    def add_address(message):
        chat_id = message.chat.id
        address = message.text.strip()

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

        if name in addresses_to_monitor:
            bot.send_message(chat_id, f"Address with name '{name}' already exists.")
            return

        addresses_to_monitor[name] = {
            'ether_address': address,
            'last_seen_block': web3.eth.block_number
        }

        save_addresses(addresses_to_monitor)
        bot.send_message(chat_id, f"✅ Added Ethereum address '{name}': '{address}'.")    
        
        bot.message_handler(func=lambda m: m.chat.id == chat_id and m.text)(handle_name)

    @bot.message_handler(commands=['rmAddress'])
    def handle_remove(message):
        """
        Handles the /rmaddress command by displaying a list of Ethereum addresses to remove.
        
        :param message: The received message object.
        """
        if not is_allowed_user(message.chat.id):
            bot.reply_to(message, "🚫 Unauthorized access.")
            return

        # Directly use addresses_to_monitor assuming it's a flat dictionary of addresses
        addresses = addresses_to_monitor

        if not addresses:
            bot.send_message(message.chat.id, "❌ No addresses available to remove.")
            return

        # Create buttons for each address
        markup = types.InlineKeyboardMarkup()
        for name in addresses:
            markup.add(types.InlineKeyboardButton(name, callback_data=f'remove_{name}'))

        bot.send_message(message.chat.id, "🔍 Please select the address to remove:", reply_markup=markup)
        user_state[message.chat.id] = {'stage': 'awaiting_address'}

    @bot.callback_query_handler(func=lambda call: call.data.startswith('remove_'))
    def handle_address_removal(call):
        """
        Handles the removal of an address based on user selection.
        
        :param call: The callback query object.
        """
        chat_id = call.message.chat.id
        address_name = call.data[len('remove_'):]  # Extract the address name from callback data

        print(f"User {chat_id} selected address: {address_name}")

        if chat_id not in user_state or user_state[chat_id]['stage'] != 'awaiting_address':
            bot.send_message(chat_id, "⚠️ Unexpected error. Please try the command again.")
            return

        if address_name in addresses_to_monitor:
            del addresses_to_monitor[address_name]
            save_addresses(addresses_to_monitor)  # Save the updated addresses list
            bot.send_message(chat_id, f"✅ Removed address with name '{address_name}' from the Ethereum monitoring list.")
        else:
            bot.send_message(chat_id, f"❌ Address with name '{address_name}' not found in the monitoring list.")

        if chat_id in user_state:
            del user_state[chat_id]

        bot.answer_callback_query(call.id)

    @bot.message_handler(commands=['show'])
    def handle_show(message):
        """
        Handles the /show command by displaying all monitored Ethereum addresses.
        
        :param message: The received message object.
        """
        if not is_allowed_user(message.chat.id):
            bot.reply_to(message, "🚫 Unauthorized access.")
            return
        show_addresses(bot, message, addresses_to_monitor)