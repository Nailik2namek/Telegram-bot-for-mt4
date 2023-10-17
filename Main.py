#!/usr/bin/env python3
import asyncio
import logging
import math
import os
 
from metaapi_cloud_sdk import MetaApi
from prettytable import PrettyTable
from telegram import ParseMode, Update
from telegram.ext import CommandHandler, Filters, MessageHandler, Updater, ConversationHandler, CallbackContext
 
# MetaAPI Credentials
API_KEY = os.environ.get("API_KEY")
ACCOUNT_ID = os.environ.get("ACCOUNT_ID")
 
# Telegram Credentials
TOKEN = os.environ.get("TOKEN")
 
# Port number for Telegram bot webhook
PORT = int(os.environ.get('PORT', '8443'))
 
# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)
 
# Conversation states
CALCULATE, TRADE, DECISION, CONNECT, SET_LANGUAGE, SET_CURRENCY, FINISH = range(7)
 
# Allowed FX symbols (you can add more)
SYMBOLS = ['AUDCAD', 'AUDCHF', 'AUDJPY', 'AUDNZD', 'AUDUSD', 'CADCHF', 'CADJPY', 'CHFJPY', 'EURAUD', 'EURCAD',
           'EURCHF', 'EURGBP', 'EURJPY', 'EURNZD', 'EURUSD', 'GBPAUD', 'GBPCAD', 'GBPCHF', 'GBPJPY', 'GBPNZD', 'GBPUSD',
           'NZDCAD', 'NZDCHF', 'NZDJPY', 'NZDUSD', 'USDCAD', 'USDCHF', 'USDJPY', 'XAGUSD', 'XAUUSD']
 
# Risk factor
RISK_FACTOR = float(os.environ.get("RISK_FACTOR", 0.01))
 
# Dictionary to store user data during conversation
user_data = {}
 
 
# Helper Functions
def parse_signal(signal: str) -> dict:
    """Parses a trading signal and returns trade information."""
    signal = signal.splitlines()
    signal = [line.strip() for line in signal]
    trade = {}
 
    if 'LONG' in signal[0]:
        trade['OrderType'] = 'Buy'
    elif 'SHORT' in signal[0]:
        trade['OrderType'] = 'Sell'
    else:
        return {}
 
    # Extract symbol from trade signal
    trade['Symbol'] = signal[0].split()[-1].upper()
    if trade['Symbol'] not in SYMBOLS:
        return {}
 
    for line in signal[1:]:
        if 'TP' in line:
            if 'TP 1' not in trade:
                trade['TP 1'] = float(line.split()[-1].replace(',', '.'))
            else:
                trade['TP 2'] = float(line.split()[-1].replace(',', '.'))
 
        if 'SL' in line:
            trade['StopLoss'] = float(line.split()[-1].replace(',', '.'))
 
    if not ('StopLoss' in trade and 'TP 1' in trade):
        return {}
 
    return trade
 
 
def get_trade_information(trade: dict, balance: float) -> str:
    """Calculates trade information and returns it as a string."""
    symbol_info = {
        'XAUUSD': 0.1,  # Modify as needed
        'XAGUSD': 0.01,  # Modify as needed
    }
    symbol = trade['Symbol']
 
    # Calculate stop loss in pips
    multiplier = symbol_info.get(symbol, 0.0001)  # Default multiplier for unsupported symbols
    stop_loss_pips = round(abs((trade['StopLoss'] - trade['Entry']) / multiplier))
 
    # Calculate position size using risk factor
    position_size = math.floor(((balance * trade['RiskFactor']) / stop_loss_pips) / 10 * 100) / 100
 
    # Calculate take profit in pips
    take_profit_pips = [round(abs((tp - trade['Entry']) / multiplier)) for tp in [trade['TP 1'], trade.get('TP 2', 0)]]
 
    table = PrettyTable()
    table.title = "Trade Information"
    table.field_names = ["Key", "Value"]
    table.align["Key"] = "l"
    table.align["Value"] = "l"
 
    table.add_row(['Order Type', trade['OrderType']])
    table.add_row(['Symbol', symbol])
    table.add_row(['Entry', trade['Entry']])
    table.add_row(['Stop Loss', '{} pips'.format(stop_loss_pips)])
    for i, tp in enumerate(take_profit_pips):
        table.add_row(['TP {}'.format(i + 1), '{} pips'.format(tp)]
                     if i == 0 else ['TP {}'.format(i + 1), '{} pips'.format(tp) + " (Split)"])
    table.add_row(['Risk Factor', '{:.0%}'.format(trade['RiskFactor'])])
    table.add_row(['Position Size', position_size])
 
    potential_loss = round((position_size * 10) * stop_loss_pips, 2)
    table.add_row(['Potential Loss', '$ {:,.2f}'.format(potential_loss)])
 
    total_profit = 0
    for i, tp in enumerate(take_profit_pips):
        profit = round((position_size * 10 * (1 / len(take_profit_pips))) * tp, 2)
        table.add_row(['TP {} Profit'.format(i + 1), '$ {:,.2f}'.format(profit)]
                     if i == 0 else ['TP {} Profit'.format(i + 1), '$ {:,.2f}'.format(profit) + " (Split)"])
        total_profit += profit
 
    table.add_row(['Total Potential Profit', '$ {:,.2f}'.format(total_profit)])
 
    return table.get_string()
 
 
# Define the /start command handler to initiate the conversation
def start(update: Update, context: CallbackContext):
    user_data.clear()
    user_data['balance'] = 10000  # Replace with your actual account balance
    user_data['RiskFactor'] = RISK_FACTOR
    user_data['Language'] = 'English'
    user_data['Currency'] = 'USD'
 
    update.message.reply_text("Welcome to the Trading Signal Bot! Please use the following commands to proceed:\n\n"
                              "/connect - Connect your MetaTrader account\n"
                              "/language - Set your preferred language\n"
                              "/currency - Set your preferred currency\n"
                              "/trade - Provide a trade signal\n\n"
                              "You can change your language and currency settings at any time.")
 
    return DECISION
 
 
# Define the /connect command handler to set MetaAPI credentials
def connect(update: Update, context: CallbackContext):
    user_data['api_key'] = API_KEY
    user_data['account_id'] = ACCOUNT_ID
 
    update.message.reply_text("Your MetaTrader account is now connected!")
 
    return DECISION
 
 
# Define the /language command handler to set the preferred language
def set_language(update: Update, context: CallbackContext):
    user_data['Language'] = context.args[0]
 
    update.message.reply_text(f"Your preferred language is set to {user_data['Language']}!")
 
    return DECISION
 
 
# Define the /currency command handler to set the preferred currency
def set_currency(update: Update, context: CallbackContext):
    user_data['Currency'] = context.args[0]
 
    update.message.reply_text(f"Your preferred currency is set to {user_data['Currency']}!")
 
    return DECISION
 
 
# Define the /trade command handler to provide a trade signal
def trade(update: Update, context: CallbackContext):
    update.message.reply_text("Please provide the trade signal in the following format:\n\n"
                              "📈 LONG EURUSD : 1.12345\n"
                              "🚀 TP 1 : 1.12845\n"
                              "🚀 TP 2 : 1.13345\n"
                              "💣 SL : 1.11845\n"
                              "Ensure it follows this format for proper processing.")
    return CALCULATE
 
 
# Define the conversation handler for trade signal processing
def calculate(update: Update, context: CallbackContext):
    signal = update.message.text
    trade = parse_signal(signal)
    if not trade:
        update.message.reply_text("Invalid trade signal. Please use the format specified.")
        return CALCULATE
 
    # Store the trade signal in user data
    user_data['trade'] = trade
 
    # Calculate trade information
    balance = user_data['balance']
    trade['RiskFactor'] = user_data['RiskFactor']
    trade['Entry'] = trade['StopLoss'] + 0.001  # Replace with your preferred entry price
    trade_info = get_trade_information(trade, balance)
 
    update.message.reply_text(f"Trade information:\n{trade_info}",
                              parse_mode=ParseMode.MARKDOWN)
 
    return FINISH
 
 
# Define the /finish command handler to confirm the trade
def finish(update: Update, context: CallbackContext):
    if 'trade' in user_data:
        trade = user_data['trade']
        # You can execute the trade here using MetaAPI
        # Example: meta_api_instance.create_market_buy_order(ACCOUNT_ID, trade['Symbol'], trade['Volume'], trade['Entry'], trade['StopLoss'], trade['TakeProfit'])
 
        balance = user_data['balance']
        trade_info = get_trade_information(trade, balance)
 
        update.message.reply_text(f"Trade confirmed! Here are the trade details:\n{trade_info}",
                                  parse_mode=ParseMode.MARKDOWN)
 
    return DECISION
 
 
def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher
 
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            DECISION: [MessageHandler(Filters.regex('^/connect$'), connect),
                       MessageHandler(Filters.regex('^/language$'), set_language),
                       MessageHandler(Filters.regex('^/currency$'), set_currency),
                       MessageHandler(Filters.regex('^/trade$'), trade)],
            CALCULATE: [MessageHandler(Filters.text, calculate)],
            FINISH: [MessageHandler(Filters.regex('^/finish$'), finish)]
        },
        fallbacks=[]
    )
    dp.add_handler(conv_handler)
 
    updater.start_polling()
    updater.idle()
 
 
if __name__ == '__main__':
    main()
