#!/usr/bin/env python3
import logging
import math
import os
import re

from prettytable import PrettyTable
from telegram import Update, ParseMode
from telegram.ext import CommandHandler, Filters, MessageHandler, Updater, ConversationHandler, CallbackContext

# Replace with your MetaAPI and Telegram credentials
API_KEY = 'YOUR_META_API_KEY'
ACCOUNT_ID = 'YOUR_ACCOUNT_ID'
TOKEN = 'YOUR_TELEGRAM_BOT_TOKEN'
RISK_FACTOR = 0.01

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name)

# Conversation states
CALCULATE, TRADE, DECISION, SET_LANGUAGE, SET_CURRENCY, SET_RISK, FINISH = range(7)

# Allowed FX symbols (you can add more)
SYMBOLS = ['AUDCAD', 'AUDCHF', 'AUDJPY', 'AUDNZD', 'AUDUSD', 'CADCHF', 'CADJPY', 'CHFJPY', 'EURAUD', 'EURCAD',
           'EURCHF', 'EURGBP', 'EURJPY', 'EURNZD', 'EURUSD', 'GBPAUD', 'GBPCAD', 'GBPCHF', 'GBPJPY', 'GBPNZD', 'GBPUSD',
           'NZDCAD', 'NZDCHF', 'NZDJPY', 'NZDUSD', 'USDCAD', 'USDCHF', 'USDJPY', 'XAGUSD', 'XAUUSD']

# Dictionary to store user data during conversation
user_data = {}


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
    trade['Symbol'] = re.search(r'\b([A-Z]{6})\b', signal[0]).group(1)
    if trade['Symbol'] not in SYMBOLS:
        return {}

    for line in signal[1:]:
        if 'TP' in line:
            if 'TP 1' not in trade:
                trade['TP 1'] = float(re.search(r'[-+]?\d*\.\d+|\d+', line).group(0))
            else:
                trade['TP 2'] = float(re.search(r'[-+]?\d*\.\d+|\d+', line).group(0))

        if 'SL' in line:
            trade['StopLoss'] = float(re.search(r'[-+]?\d*\.\d+|\d+', line).group(0))

    if not ('StopLoss' in trade and 'TP 1' in trade):
        return {}

    return trade


def get_trade_information(trade: dict, balance: float) -> str:
    """Calculates trade information and returns it as a string."""
    symbol_info = {
        'XAUUSD': 0.1,
        'XAGUSD': 0.01,
    }
    symbol = trade['Symbol']

    multiplier = symbol_info.get(symbol, 0.0001)
    stop_loss_pips = round(abs((trade['StopLoss'] - trade['Entry']) / multiplier))

    position_size = math.floor(((balance * trade['RiskFactor']) / stop_loss_pips) / 10 * 100) / 100

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
        table.add_row(['TP {}'.format(i + 1), '{} pips'.format(tp) if i == 0 else '{} pips (Split)'])
    table.add_row(['Risk Factor', '{:.0%}'.format(trade['RiskFactor'])])

    potential_loss = round((position_size * 10) * stop_loss_pips, 2)
    table.add_row(['Total Potential Profit', '$ {:,.2f}'.format(total_profit)]

    total_profit = 0
    for i, tp in enumerate(take_profit_pips):
        profit = round((position_size * 10 * (1 / len(take_profit_pips))) * tp, 2)
        table.add_row(['TP {} Profit'.format(i + 1), '$ {:,.2f}'.format(profit) if i == 0 else '$ {:,.2f} (Split)'])
        total_profit += profit

    table.add_row(['Total Potential Profit', '$ {:,.2f}'.format(total_profit)])

    return table.get_string()


def start(update: Update, context: CallbackContext):
    user_data.clear()
    user_data['balance'] = 10000  # Replace with your actual account balance
    user_data['RiskFactor'] = RISK_FACTOR
    user_data['Language'] = 'English'
    user_data['Currency'] = 'USD'

    update.message.reply_text("Welcome to the Trading Signal Bot! Please use the following commands to proceed:\n\n"
                              "/set_language - Set your preferred language\n"
                              "/set_currency - Set your preferred currency\n"
                              "/set_risk - Set your preferred risk percentage\n"
                              "/trade - Provide a trade signal\n\n"
                              "You can change your language, currency, and risk settings at any time.")

    return DECISION

def set_language(update: Update, context: CallbackContext):
    user_data['Language'] = context.args[0]
    update.message.reply_text(f"Your preferred language is set to {user_data['Language']}!")
    return DECISION


def set_currency(update: Update, context: CallbackContext):
    user_data['Currency'] = context.args[0]
    update.message.reply_text(f"Your preferred currency is set to {user_data['Currency']}!")
    return DECISION


def set_risk(update: Update, context: CallbackContext):
    risk_percentage = float(context.args[0])
    if 0 <= risk_percentage <= 1:
        user_data['RiskFactor'] = risk_percentage
        update.message.reply_text(f"Your preferred risk percentage is set to {user_data['RiskFactor']:.0%}!")
    else:
        update.message.reply_text("Invalid risk percentage. Please provide a value between 0 and 1.")
    return DECISION


def trade(update: Update, context: CallbackContext):
    update.message.reply_text("Please provide the trade signal in the following format:\n\n"
                              "📈 LONG EURUSD : 1.12345\n"
                              "🚀 TP 1 : 1.12845\n"
                              "🚀 TP 2 : 1.13345\n"
                              "💣 SL : 1.11845\n"
                              "Ensure it follows this format for proper processing.")
    return CALCULATE

def calculate(update: Update, context: CallbackContext):
    signal = update.message.text
    trade = parse_signal(signal)
    if not trade:
        update.message.reply_text("Invalid trade signal. Please use the specified format.")
        return CALCULATE

    user_data['trade'] = trade

    balance = user_data['balance']
    trade['RiskFactor'] = user_data['RiskFactor']
    trade['Entry'] = trade['StopLoss'] + 0.001
    trade_info = get_trade_information(trade, balance)

    update.message.reply_text(f"Trade information:\n{trade_info}", parse_mode=ParseMode.MARKDOWN)
    return FINISH

def finish(update: Update, context: CallbackContext):
    if 'trade' in user_data:
        trade = user_data['trade']
        # Vous pouvez exécuter le trade ici en utilisant MetaAPI
        # Exemple: meta_api_instance.create_market_buy_order(ACCOUNT_ID, trade['Symbol'], trade['Volume'], trade['Entry'], trade['StopLoss'], trade['TakeProfit'])

        balance = user_data['balance']
        trade_info = get_trade_information(trade, balance)

        update.message.reply_text(f"Trade confirmed! Here are the trade details:\n{trade_info}", parse_mode=ParseMode.MARKDOWN)

    return DECISION

def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            DECISION: [MessageHandler(Filters.regex('^/set_language$'), set_language),
                       MessageHandler(Filters.regex('^/set_currency$'), set_currency),
                       MessageHandler(Filters.regex('^/set_risk$'), set_risk),
                       MessageHandler(Filters.regex('^/trade$'), trade)],
            CALCULATE: [MessageHandler(Filters.text & ~Filters.command, calculate)],
            FINISH: [MessageHandler(Filters.regex('^/finish$'), finish)]
        },
        fallbacks=[]
    )
    dp.add_handler(conv_handler)

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()

