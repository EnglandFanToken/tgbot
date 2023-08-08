
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, ConversationHandler, CallbackQueryHandler
import gspread
from google.oauth2.service_account import Credentials

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

# Initialize the bot token and create an Updater
TOKEN = '6307468081:AAEHVl22FBACkrBb3UuQ578QjKuEOkpPA0c'
updater = Updater(token=TOKEN, use_context=True)
dispatcher = updater.dispatcher

# Define conversation states
TASK, TWITTER_USERNAME, WALLET_ADDRESS, YOUR_DATA = range(4)  # Remove FB_LINK and INSTAGRAM_USERNAME

# Initialize user data dictionary
user_data = {}

# Initialize referral data and referred users dictionaries
referral_data = {}
referred_users = {}


def start(update: Update, context: CallbackContext) -> int:
    user_id = update.effective_user.id

    # Check if the user was referred
    if context.args:
        referrer_id = context.args[0]
        if referrer_id.startswith('referral_'):
            referrer_id = referrer_id[len('referral_'):]
        referrer_id = int(referrer_id)
        if user_id not in referred_users.get(referrer_id, []):
            if referrer_id not in referral_data:
                referral_data[referrer_id] = 0  # Initialize referral points for the referrer
            referral_data[referrer_id] += 20000  # Increment referral points for the referrer
            referred_users.setdefault(referrer_id, []).append(user_id)  # Update referred users for the referrer
            context.bot.send_message(chat_id=referrer_id, text='😍 Congratulations! You received 20000 referral balance.')

    referral_count = len(referred_users.get(user_id, []))  # Update referral count

    # Save the Telegram username in user data
    user_data['telegram_username'] = update.effective_user.username

    task_options = [
        [InlineKeyboardButton("✳️ Join Telegram Group", url='https://t.me/Spamcoinportal')],
        [InlineKeyboardButton("✳️ Join Twitter", url='https://twitter.com/the_spamcoin')],
        [InlineKeyboardButton(" ✔️ Done", callback_data='done')]
    ]
    reply_markup = InlineKeyboardMarkup(task_options)
    context.bot.send_message(chat_id=user_id, text=f'Welcome to our SPAM official bot!\n',
                             reply_markup=reply_markup)

    return TASK


def button_callback(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()

    if query.data == 'done':
        # Check if the user has joined the Telegram group
        chat_member = context.bot.get_chat_member(chat_id='@Spamcoinportal', user_id=query.from_user.id)
        if chat_member.status == 'member':
            # Get the user's Telegram username and user_id
            telegram_username = query.from_user.username
            user_id = query.from_user.id
            user_data['telegram_username'] = telegram_username

            # Check if the user was referred
            if context.args:
                referrer_id = context.args[0]
                if referrer_id.startswith('referral_'):
                    referrer_id = referrer_id[len('referral_'):]
                referrer_id = int(referrer_id)
                if user_id not in referred_users.get(referrer_id, []):
                    if referrer_id not in referral_data:
                        referral_data[referrer_id] = 0  # Initialize referral points for the referrer
                    referral_data[referrer_id] += 1  # Increment referral count for the referrer
                    referred_users.setdefault(referrer_id, []).append(user_id)  # Update referred users for the referrer


# Prompt the user to enter their Twitter username
            context.bot.send_message(chat_id=update.effective_chat.id, text="📝 Please enter your Twitter username:")
            return TWITTER_USERNAME
        else:
            # User didn't join the group, display an error message
            context.bot.send_message(chat_id=update.effective_chat.id, text="🆘 You are not in the Telegram group. Please join the Telegram group first.")
            return TASK


def save_username(update: Update, context: CallbackContext) -> int:
    # Save the user's Twitter username in user data
    user_data['twitter_username'] = update.message.text

    # Prompt the user to enter their wallet address
    context.bot.send_message(chat_id=update.effective_chat.id, text="📝 Please enter your Wallet address (for communication): Optional")
    return WALLET_ADDRESS


def save_wallet_address(update: Update, context: CallbackContext) -> int:
    # Save the user's wallet address in user data
    user_data['wallet_address'] = update.message.text

    user_id = update.effective_user.id

    if user_id not in referral_data or referral_data[user_id] < 3:
        # Add 3 extra points for completing tasks
        referral_points = referral_data.get(user_id, 0)
        referral_points += 20000
        referral_data[user_id] = referral_points

    # Save the user data to Google Sheets
    save_user_data_to_sheet(user_id)

    # Send a thank you message
    context.bot.send_message(chat_id=update.effective_chat.id, text="Thank you for submitting your data!")

    # Display menu options after the thank you message
    menu_options = [
        ["💰 Balance", "🖇 Refer link"],
        ["☑️ Check Rank", "📨 Your Data"],
        ["ℹ️ INFO"]
    ]
    reply_markup = ReplyKeyboardMarkup(menu_options, resize_keyboard=True)  # Removed one_time_keyboard=True
    context.bot.send_message(chat_id=update.effective_chat.id, text="Here Is All Buttons For You:", reply_markup=reply_markup)

    return ConversationHandler.END


# Function to save user data to Google Sheets
def save_user_data_to_sheet(user_id):
    # Authenticate using service account credentials
    scopes = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    creds = Credentials.from_service_account_file('User-Data.json', scopes=scopes)
    client = gspread.authorize(creds)

    # Open the Google Sheets document by ID
    document_id = '1aiSBL00khUsn0sXEjG3GMzSN74ysDyoxeDIocbInpUM'
    sheet = client.open_by_key(document_id).sheet1

    # Check if the Telegram username already exists in the sheet
    existing_users = sheet.col_values(1)
    telegram_username = user_data['telegram_username']
    if telegram_username in existing_users:
        # Find the index of the existing user's Telegram username
        index = existing_users.index(telegram_username)

        # Update the corresponding row with the new data
        sheet.update_cell(index + 1, 2, user_data['twitter_username'])
        sheet.update_cell(index + 1, 3, user_data['wallet_address'])
        sheet.update_cell(index + 1, 4, referral_data.get(user_id, 0))
        sheet.update_cell(index + 1, 5, len(referred_users.get(user_id, [])))
    else:
        # Append the user data to the sheet
        data = [user_data['telegram_username'], user_data['twitter_username'], user_data['wallet_address'], referral_data.get(user_id, 0), len(referred_users.get(user_id, []))]
        sheet.append_row(data)


# Function to process referral
def process_referral(user_id):
    # Add your implementation to process the referral
    pass


# Balance command handler
def balance(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    referral_points = referral_data.get(user_id, 0)
    referral_count = len(referred_users.get(user_id, []))

    context.bot.send_message(chat_id=user_id, text=f'🏆 Your Total Balance: {referral_points}\n👨‍👩‍👧 Total Referral : {referral_count}')

# Refer link command handler
def refer_link(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    bot_username = context.bot.username
    refer_link = f'https://t.me/{bot_username}?start={user_id}'

    context.bot.send_message(chat_id=user_id, text=f'♾Your referral link:\n{refer_link}')


# Handle the 'Check Rank' command
def check_rank(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id

    # Sort the referral_data dictionary based on referral points in descending order
    sorted_referral_data = dict(sorted(referral_data.items(), key=lambda item: item[1], reverse=True))

    # Get the top 10 referrers
    top_10_referrers = list(sorted_referral_data.items())[:10]

    # Prepare a message with the rank, referral count, and Telegram usernames of the top 10 referrers
    message = "🏆 Top 10 Referrers:\n"
    for rank, (referrer_id, referral_points) in enumerate(top_10_referrers, start=1):
        referrer_username = context.bot.get_chat(referrer_id).username
        referral_count = len(referred_users.get(referrer_id, []))
        message += f"{rank}. @{referrer_username} (Referral Count: {referral_count})\n"

    # Find the user's rank and referral count
    user_rank = list(sorted_referral_data.keys()).index(user_id) + 1 if user_id in sorted_referral_data else 0
    user_referral_count = len(referred_users.get(user_id, []))

    # Send the user's rank and the top 10 referrers' usernames
    message += f"\n👑 Your Rank: {user_rank} (Your Referral: {user_referral_count})"
    context.bot.send_message(chat_id=user_id, text=message)


# Your Data command handler
def your_data(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    telegram_username = update.effective_user.username  # Get the user's Telegram username
    twitter_username = user_data.get('twitter_username', 'Not provided')
    wallet_address = user_data.get('wallet_address', 'Not provided')

    data_message = f"📌 Telegram Username: @{telegram_username}\n📌 Twitter Username: {twitter_username}\n📌 Wallet Address: {wallet_address}"
    context.bot.send_message(chat_id=user_id, text=data_message)


# Handle the 'INFO' command
def info(update: Update, context: CallbackContext) -> None:
    context.bot.send_message(chat_id=update.effective_chat.id, text="Here is our info.")


# Custom filter for plain text inputs
def is_plain_text(update: Update) -> bool:
    text = update.message.text
    return not text.startswith('/')


# Cancel command handler
def cancel(update: Update, context: CallbackContext) -> int:
    user_id = update.effective_user.id
    referred_users.pop(user_id, None)  # Remove user from referred users of others
    user_data.clear()  # Clear user data
    context.bot.send_message(chat_id=user_id, text="Action cancelled.")
    return ConversationHandler.END


# Register the command handlers
dispatcher.add_handler(MessageHandler(Filters.regex('Balance'), balance))
dispatcher.add_handler(MessageHandler(Filters.regex('Refer link'), refer_link))
dispatcher.add_handler(MessageHandler(Filters.regex('Check Rank'), check_rank))
dispatcher.add_handler(MessageHandler(Filters.regex('Your Data'), your_data))
dispatcher.add_handler(MessageHandler(Filters.regex('INFO'), info))  # Register the info command handler
dispatcher.add_handler(CommandHandler('start', start))  # Register the start command handler

# Register the conversation handlers
conv_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(button_callback, pattern='^done$')],
    states={
        TASK: [CallbackQueryHandler(button_callback)],
        TWITTER_USERNAME: [MessageHandler(Filters.text & ~Filters.command, save_username)],
        WALLET_ADDRESS: [MessageHandler(Filters.text & ~Filters.command, save_wallet_address)],
    },
    fallbacks=[CommandHandler('cancel', cancel)]
)
dispatcher.add_handler(conv_handler)


# Your Sheets command handler
def sheets(update: Update, context: CallbackContext) -> None:
    # Check if the user is an admin
    admin_username = 'projectmanagement668'
    if update.effective_user.username == admin_username:
        # Get the list of existing users from the Google Sheets document
        scopes = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
        creds = Credentials.from_service_account_file('User-Data.json', scopes=scopes)
        client = gspread.authorize(creds)

        document_id = '1aiSBL00khUsn0sXEjG3GMzSN74ysDyoxeDIocbInpUM'
        sheet = client.open_by_key(document_id).sheet1
        existing_users = sheet.col_values(1)

        # Send the link to the updated Google Sheets to the admin
        sheet_url = f'https://docs.google.com/spreadsheets/d/{document_id}'
        context.bot.send_message(chat_id=update.effective_chat.id, text=f'Here is the User Data link of Google Sheets:\n{sheet_url}')
    else:
        context.bot.send_message(chat_id=update.effective_chat.id, text="You are not authorized to use this command.")

# Register the command handler for /sheets
dispatcher.add_handler(CommandHandler('sheets', sheets))

# Start the bot
updater.start_polling()
updater.idle()