import os
import logging
from typing import Final
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    CallbackQueryHandler,
)

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Bot token and staff group
TOKEN: Final = "7692272382:AAEePO8DMJCoDC4RTyFq5DqKAQAKL97uwKU"
STAFF_GROUP_CHAT_ID = "-4779662690"

# Menu data with descriptions and images
MENU = {
    "Soups": {
        "description": "Warm and comforting soups made with fresh ingredients.",
        "image_ids": ["AgACAgQAAxkBAAPNaBy7WmNb6gkEMAdB--jfTE__grYAArPMMRtOwOlQnXdqGpaz0HYBAAMCAAN5AAM2BA"]
    },
    "Salads": {
        "description": "Fresh and vibrant salads to complement your meal.",
        "image_ids": ["AgACAgQAAxkBAAIBbmgd8VJ_Lw1vITZO-6PucMpi5D-VAALcyDEbTsDxUGD9fGfOqoEoAQADAgADeQADNgQ"]
    },
    "Pasta": {
        "description": "Delicious pasta dishes with a variety of sauces.",
        "image_ids": ["AgACAgQAAxkBAAPdaBz3NKECzE4atUXulloGyXeVTAADf80xG07A6VC6-A457c4MqQEAAwIAA3kAAzYE"]
    },
    "Main Courses": {
        "description": "Hearty and flavorful main courses to satisfy your appetite.",
        "image_ids": ["AgACAgQAAxkBAAIBLWgdw1ZF0f02GEFcYCe_I1JDAVhpAALwxzEbTsDxUGWdzxvml5iQAQADAgADeQADNgQ"]
    },
    "Juices": {
        "description": "Refreshing and natural fruit juices.",
        "image_ids": ["AgACAgQAAxkBAAPxaB2eisEQsn7Bgl9jGGmZHl1Sq0MAAnHOMRtOwOlQl7yTVuJSCxUBAAMCAAN5AAM2BA"]
    },
    "Pizza and Egg Specials": {
        "description": "Freshly baked pizzas and delicious egg-based specials.",
        "image_ids": ["AgACAgQAAxkBAAPCaByu5qLeh9l1z3s1KMCCIY702PgAAqjMMRtOwOlQ4vXAc3UD3XgBAAMCAAN5AAM2BA"]
    },
    "Beverages": {
        "description": "A wide selection of refreshing drinks and fine wines.",
        "image_ids": ["AgACAgQAAxkBAAIBI2gdsr6hCkd7AkJS4_VobBeCBTXTAAK5xzEbTsDxUI1IArzN1IGcAQADAgADeQADNgQ"]
    },
    "Hot Drinks": {
        "description": "Warm and aromatic coffee, tea, and specialty drinks.",
        "image_ids": ["AgACAgQAAxkBAAIBOWgd4SFLwtWTGbf8O0Qzlo5bNlJHAAJMyDEbTsDxUNIdsibU1yvMAQADAgADeQADNgQ"]
    },
    "Hard Drinks": {
        "description": "Premium spirits and cocktails for a refined experience.",
        "image_ids": ["AgACAgQAAxkBAAIBN2gd4QX8y4ceF5SLzvgRulCRmr2CAAJLyDEbTsDxUBJYBWgsN9lAAQADAgADeQADNgQ"]
    }
}

BANK_ACCOUNTS = [
    {
        "bank_name": "Commercial Bank of Ethiopia (CBE)",
        "account_holder": "Bisrat Hotel",
        "account_number": "1000014828657"
    },
    {
        "bank_name": "Sinqe Bank",
        "account_holder": "Bisrat Hotel",
        "account_number": "1048094320118"
    }
]

# Start or /menu command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.message.chat_id
    logger.info(f"Start command used in chat ID: {chat_id}")
    # Clear all previous menu messages
    await clear_previous_menu(chat_id, context)
    # Clear the /start command message itself
    try:
        await context.bot.delete_message(chat_id=chat_id, message_id=update.message.message_id)
    except Exception as e:
        logger.warning(f"Failed to delete /start message in chat {chat_id}: {e}")
    await show_category_menu(chat_id, context)

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.message.chat_id
    logger.info(f"Menu command used in chat ID: {chat_id}")
    # Clear all previous menu messages
    await clear_previous_menu(chat_id, context)
    # Clear the /menu command message itself
    try:
        await context.bot.delete_message(chat_id=chat_id, message_id=update.message.message_id)
    except Exception as e:
        logger.warning(f"Failed to delete /menu message in chat {chat_id}: {e}")
    await show_category_menu(chat_id, context)

# Show category menu
async def show_category_menu(chat_id, context):
    categories = list(MENU.keys())
    keyboard = [[InlineKeyboardButton(category, callback_data=f"category_{category}")] for category in categories]
    reply_markup = InlineKeyboardMarkup(keyboard)
    try:
        msg = await context.bot.send_message(
            chat_id=chat_id,
            text="🍽️ Please select a category:",
            reply_markup=reply_markup
        )
        context.user_data["menu_messages"] = [msg.message_id]
        logger.info(f"Category menu sent to chat ID: {chat_id}, message ID: {msg.message_id}")
    except Exception as e:
        logger.error(f"Failed to send category menu to chat {chat_id}: {e}")
        await context.bot.send_message(
            chat_id=chat_id,
            text="⚠️ An error occurred. Please try again later."
        )

# Show category details (images and description)
async def show_category_details(chat_id, category, context):
    logger.info(f"Attempting to show details for category: {category} in chat ID: {chat_id}")
    menu_messages = []
    category_data = MENU.get(category)

    if not category_data:
        logger.error(f"Category {category} not found in MENU")
        msg = await context.bot.send_message(
            chat_id=chat_id,
            text="⚠️ Category not found. Please select another category."
        )
        menu_messages.append(msg.message_id)
        context.user_data["menu_messages"] = menu_messages
        return

    # Send each image
    for image_id in category_data["image_ids"]:
        try:
            logger.info(f"Sending image {image_id} for category {category}")
            msg = await context.bot.send_photo(
                chat_id=chat_id,
                photo=image_id
            )
            menu_messages.append(msg.message_id)
            logger.info(f"Image {image_id} sent, message ID: {msg.message_id}")
        except Exception as e:
            logger.warning(f"Failed to send image {image_id} for category {category}: {e}")
            msg = await context.bot.send_message(
                chat_id=chat_id,
                text=f"📸 Image for {category} not available."
            )
            menu_messages.append(msg.message_id)
            logger.info(f"Fallback text sent for image {image_id}, message ID: {msg.message_id}")

    # Send category description with back button
    caption = f"🍽️ <b>{category}</b>\n📝 {category_data['description']}"
    keyboard = [
        [InlineKeyboardButton("⬅ Back to Categories", callback_data="back_to_categories")]
    ]
    try:
        msg = await context.bot.send_message(
            chat_id=chat_id,
            text=caption,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )
        menu_messages.append(msg.message_id)
        logger.info(f"Category description sent for {category}, message ID: {msg.message_id}")
    except Exception as e:
        logger.error(f"Failed to send category description for {category}: {e}")
        msg = await context.bot.send_message(
            chat_id=chat_id,
            text="⚠️ Unable to display category details. Please try again."
        )
        menu_messages.append(msg.message_id)

    # Save all sent message IDs
    context.user_data["menu_messages"] = menu_messages

# Delete previous menu messages
async def clear_previous_menu(chat_id, context):
    for msg_id in context.user_data.get("menu_messages", []):
        try:
            await context.bot.delete_message(chat_id=chat_id, message_id=msg_id)
        except Exception as e:
            logger.warning(f"Failed to delete message {msg_id} in chat {chat_id}: {e}")
    context.user_data["menu_messages"] = []

# Account handler
async def account(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.message.chat_id
    logger.info(f"Account command used in chat ID: {chat_id}")
    await clear_previous_menu(chat_id, context)
    try:
        await context.bot.delete_message(chat_id=chat_id, message_id=update.message.message_id)
    except Exception as e:
        logger.warning(f"Failed to delete /account message in chat {chat_id}: {e}")
    account_info = "🏦 Bank Account Information:\n\n"
    for bank in BANK_ACCOUNTS:
        account_info += (
            f"🏛️ Bank: {bank['bank_name']}\n"
            f"👤 Account Holder: {bank['account_holder']}\n"
            f"💳 Account Number: `{bank['account_number']}`\n\n"
        )
    await update.message.reply_text(account_info, parse_mode="Markdown")

# Comment handler
async def comment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.message.chat_id
    logger.info(f"Comment command used in chat ID: {chat_id}")
    await clear_previous_menu(chat_id, context)
    try:
        await context.bot.delete_message(chat_id=chat_id, message_id=update.message.message_id)
    except Exception as e:
        logger.warning(f"Failed to delete /comment message in chat {chat_id}: {e}")
    context.user_data["awaiting_comment"] = True
    msg = await context.bot.send_message(chat_id=chat_id, text="💬 Please type your comment below.")
    context.user_data.setdefault("menu_messages", []).append(msg.message_id)

# Message handler
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.message
    user_id = message.from_user.id
    chat_id = message.chat_id

    # Ignore photos
    if message.photo:
        try:
            await context.bot.delete_message(chat_id=chat_id, message_id=message.message_id)
        except Exception as e:
            logger.warning(f"Failed to delete photo message in chat {chat_id}: {e}")
        return

    # Handle text input
    if context.user_data.get("awaiting_comment", False):
        context.user_data["awaiting_comment"] = False
        feedback = message.text.strip()
        await clear_previous_menu(chat_id, context)
        try:
            await context.bot.delete_message(chat_id=chat_id, message_id=message.message_id)
        except Exception as e:
            logger.warning(f"Failed to delete feedback message in chat {chat_id}: {e}")
        await context.bot.send_message(
            chat_id=STAFF_GROUP_CHAT_ID,
            text=f"💬 Feedback from {user_id}:\n{feedback}"
        )
        feedback_msg = await context.bot.send_message(
            chat_id=chat_id,
            text="✅ Thanks for your feedback!"
        )
        context.user_data.setdefault("menu_messages", []).append(feedback_msg.message_id)
    else:
        await clear_previous_menu(chat_id, context)
        try:
            await context.bot.delete_message(chat_id=chat_id, message_id=message.message_id)
        except Exception as e:
            logger.warning(f"Failed to delete invalid text message in chat {chat_id}: {e}")
        msg = await context.bot.send_message(
            chat_id=chat_id,
            text="Please use one of the commands: /start, /menu, /account, /comment"
        )
        context.user_data.setdefault("menu_messages", []).append(msg.message_id)

# Callback buttons
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    chat_id = query.message.chat_id
    data = query.data

    logger.info(f"Button clicked in chat ID: {chat_id}, callback_data: {data}")

    if data == "refresh_menu":
        logger.info(f"Refreshing menu for chat ID: {chat_id}")
        await clear_previous_menu(chat_id, context)
        await show_category_menu(chat_id, context)
        return

    if data == "back_to_categories":
        logger.info(f"Returning to categories for chat ID: {chat_id}")
        await clear_previous_menu(chat_id, context)
        await show_category_menu(chat_id, context)
        return

    if data.startswith("category_"):
        category = data[len("category_"):]
        logger.info(f"Processing category selection: {category} for chat ID: {chat_id}")
        await clear_previous_menu(chat_id, context)
        await show_category_details(chat_id, category, context)
        return

    logger.warning(f"Unknown callback data: {data} in chat ID: {chat_id}")

# Main
if __name__ == "__main__":
    if not TOKEN:
        raise ValueError("BOT_TOKEN environment variable is not set")
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("menu", menu))
    app.add_handler(CommandHandler("account", account))
    app.add_handler(CommandHandler("comment", comment))
    app.add_handler(MessageHandler(filters.TEXT | filters.PHOTO, handle_message))
    app.add_handler(CallbackQueryHandler(button))

    print("🤖 Bot is running...")
    app.run_polling()