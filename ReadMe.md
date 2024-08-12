# Ethereum Adrress Monitoring Bot

Welcome to the Ethereum Monitoring Bot! This project is a Telegram bot designed to monitor Ethereum addresses for transactions and provide real-time updates. It uses the Infura API to interact with the Ethereum blockchain and sends notifications to users when transactions occur on monitored addresses.

## Features

- **Monitor Ethereum Addresses**: Track transactions for specified Ethereum addresses.
- **Real-Time Notifications**: Get immediate alerts about transactions through Telegram.
- **Transaction History**: Retrieve and view historical transactions for any monitored address.
- **Address Details**: View details of monitored addresses including current balance and last seen block.

## Requirements

- Python 3.7+
- `python-dotenv` for environment variable management
- `web3` for interacting with the Ethereum blockchain
- `pyTelegramBotAPI` for Telegram bot functionality
- `emoji` for adding emojis to messages

## Installation

1. **Clone the Repository**

    ```bash
    git clone https://github.com/SP1R4/WalletTrackerBot.git
    cd WalletTrackerBot
    ```

2. **Create a Virtual Environment**

    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3. **Install Dependencies**

    ```bash
    pip3 install -r requirements.txt
    ```

4. **Create a `.env` File**

    Create a `.env` file in the root directory of the project and add your Infura Project ID and Telegram Bot Token:

    ```dotenv
    INFURA_PROJECT_ID=your_infura_project_id
    TELEGRAM_BOT_TOKEN=your_telegram_bot_token
    ```

## Configuration

1. **Infura Project ID**: You need an Infura project ID to connect to the Ethereum network. Sign up at [Infura](https://infura.io/) to get your project ID.

2. **Telegram Bot Token**: Create a bot on Telegram using [BotFather](https://core.telegram.org/bots#botfather) and get your bot token.

## Usage

1. **Start the Bot**

    Run the following command to start the bot:

    ```bash
    python3 main.py
    ```

2. **Interact with the Bot**:

    Use the following commands to interact with the bot:

    ### `/start`

    - **Description**: Shows a welcome message with a list of available commands.
    - **Usage**: `/start`

    ### `/add_address`

    - **Description**: Add a new Ethereum address to the monitoring list.
    - **Usage**: `/add_address`
    - **Interaction**: 
      1. Enter the Ethereum address.
      2. Provide a name for the address.
      3. Confirm and the address will be added.

    ### `/rm_address`

    - **Description**: Remove an address from monitoring.
    - **Usage**: `/rm_address`
    - **Interaction**: 
      1. The bot will display a list of currently monitored addresses.
      2. Select an address to remove.
      3. Confirm the removal.

    ### `/show`

    - **Description**: Display a list of all monitored Ethereum addresses.
    - **Usage**: `/show`

    ### `/details`

    - **Description**: Shows detailed information about a specific monitored address.
    - **Usage**: `/details <name>`
    - **Example**: `/details MyWallet`
    - **Interaction**:
      1. Enter the name of the address.
      2. The bot will provide details about the address, including balance and last seen block.

    ### `/history`

    - **Description**: Retrieves and displays the transaction history for a specific monitored address.
    - **Usage**: `/history <name>`
    - **Example**: `/history MyWallet`
    - **Interaction**:
      1. Enter the name of the address.
      2. The bot will display the transaction history for that address.

## Code Overview

- **`bot_handler.py`**: Contains the bot configuration and handlers for processing commands.
- **`utils.py`**: Utility functions for logging, loading and saving addresses, and managing allowed users.
- **`web3_handler.py`**: Functions for interacting with the Ethereum blockchain, including transaction processing and balance retrieval.
- **`main.py`**: The entry point of the application, initializing the bot, web3 instance, and starting the monitoring thread.

## Error Handling

The bot is designed to handle errors gracefully:
- **Connection Errors**: Logs and retries on network issues.
- **Transaction Processing Errors**: Logs and continues monitoring.

## Contributing

Feel free to contribute to this project by submitting issues or pull requests. 

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for more details.

## Contact

For any questions or support, please reach out to:

- **Author**: SP1R4
- **Email**: sp1r4.work@gmail.com

---

Thank you for using the Ethereum Monitoring Bot! We hope it serves your needs for monitoring Ethereum transactions effectively.
