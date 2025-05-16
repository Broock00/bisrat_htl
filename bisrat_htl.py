import os
import logging
import asyncio
from typing import Final
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
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
TOKEN: Final = os.getenv("BOT_TOKEN")
STAFF_GROUP_CHAT_ID = int(os.getenv("GROUP_CHAT_ID", "0"))

# Menu data with descriptions and images
# Note: Replace image_ids with new file IDs obtained by uploading high-resolution images (e.g., 1280x720, 16:9 or 4:3).
# To get new file IDs, temporarily uncomment the photo handler in handle_message below.
MENU = {
    "Soups": {
        "description": "Warm and comforting soups made with fresh ingredients.",
        "image_ids": ["AgACAgQAAxkBAAIDHWgm5uh6vUnYQIT6GIClTw1KEixtAAJ1zzEbyiE4UUCYqJZT3-uXAQADAgADeQADNgQ"]
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
        "image_ids": ["AgACAgQAAxkBAAIDEGgm3NWsep92yeW8uUMz9nb4g7hMAAJqzzEbyiE4UYdEUwcGfohFAQADAgADeQADNgQ"]
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
    await clear_previous_menu(chat_id, context)
    try:
        await context.bot.delete_message(chat_id=chat_id, message_id=update.message.message_id)
        logger.info(f"Deleted /start message in chat ID {chat_id}")
    except Exception as e:
        logger.warning(f"Failed to delete /start message in chat {chat_id}: {e}")
    context.user_data["carousel_index"] = 0
    await show_carousel(chat_id, context)

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.message.chat_id
    logger.info(f"Menu command used in chat ID: {chat_id}")
    await clear_previous_menu(chat_id, context)
    try:
        await context.bot.delete_message(chat_id=chat_id, message_id=update.message.message_id)
        logger.info(f"Deleted /menu message in chat ID {chat_id}")
    except Exception as e:
        logger.warning(f"Failed to delete /menu message in chat {chat_id}: {e}")
    context.user_data["carousel_index"] = 0
    await show_carousel(chat_id, context)

# Show carousel for current category
async def show_carousel(chat_id, context, update_message_id=None):
    categories = list(MENU.keys())
    logger.info(f"Categories loaded: {categories}, total: {len(categories)}")
    index = context.user_data.get("carousel_index", 0)
    if index < 0 or index >= len(categories):
        logger.warning(f"Invalid carousel index {index} for chat ID {chat_id}, resetting to 0")
        index = 0
        context.user_data["carousel_index"] = 0

    category = categories[index]
    category_data = MENU[category]

    # Create Previous and Next buttons
    buttons = []
    if index > 0:
        buttons.append(InlineKeyboardButton("⬅️ Previous", callback_data="carousel_prev"))
    else:
        buttons.append(InlineKeyboardButton("⬅️ Previous", callback_data="noop"))  # Disabled
    buttons.append(InlineKeyboardButton("🔄 Back to Menu", callback_data="carousel_reset"))
    if index < len(categories) - 1:
        buttons.append(InlineKeyboardButton("➡️ Next", callback_data="carousel_next"))
    else:
        buttons.append(InlineKeyboardButton("➡️ Next", callback_data="noop"))  # Disabled
    keyboard = [buttons]
    reply_markup = InlineKeyboardMarkup(keyboard)
    logger.info(f"Generated navigation buttons for index {index} in chat ID {chat_id}")

    # Prepare caption and image
    caption = f"🍽️ <b>{category}</b>\n📝 {category_data['description']}\n📄 Page {index + 1}/{len(categories)}"
    image_id = category_data["image_ids"][0]  # Use first image

    # If updating an existing message
    if update_message_id:
        try:
            logger.info(f"Attempting to edit image and caption for category {category} in message {update_message_id}, chat ID {chat_id}")
            await context.bot.edit_message_media(
                chat_id=chat_id,
                message_id=update_message_id,
                media=InputMediaPhoto(media=image_id, caption=caption, parse_mode="HTML"),
                reply_markup=reply_markup
            )
            logger.info(f"Edited message {update_message_id} for category {category}")
            context.user_data["menu_messages"] = [update_message_id]
            # Additional logging for Hard Drinks
            if category == "Hard Drinks":
                logger.info(f"Specifically checked Hard Drinks: image_id {image_id}, message ID: {update_message_id}")
            await asyncio.sleep(0.5)  # Avoid rate limits
            return
        except Exception as e:
            logger.error(f"Failed to edit message {update_message_id} for category {category}: {e}")
            # Fall back to sending a new message
            await clear_previous_menu(chat_id, context)

    # Send new message (initial or fallback)
    menu_messages = []
    try:
        logger.info(f"Attempting to send image {image_id} for category {category} in chat ID {chat_id}")
        msg = await context.bot.send_photo(
            chat_id=chat_id,
            photo=image_id,
            caption=caption,
            reply_markup=reply_markup,
            parse_mode="HTML"
        )
        menu_messages.append(msg.message_id)
        logger.info(f"Sent image for category {category}, message ID: {msg.message_id}")
    except Exception as e:
        logger.error(f"Failed to send image {image_id} for category {category}: {e}")
        msg = await context.bot.send_message(
            chat_id=chat_id,
            text=f"📸 Image for {category} not available.\n{caption}",
            reply_markup=reply_markup,
            parse_mode="HTML"
        )
        menu_messages.append(msg.message_id)
        logger.info(f"Fallback text sent for category {category}, message ID: {msg.message_id}")

    # Additional logging for Hard Drinks
    if category == "Hard Drinks":
        logger.info(f"Specifically checked Hard Drinks: image_id {image_id}, message ID: {msg.message_id}")

    context.user_data["menu_messages"] = menu_messages
    await asyncio.sleep(0.5)  # Avoid rate limits

# Delete previous menu messages
async def clear_previous_menu(chat_id, context):
    for msg_id in context.user_data.get("menu_messages", []):
        try:
            await context.bot.delete_message(chat_id=chat_id, message_id=msg_id)
            logger.info(f"Deleted message {msg_id} in chat ID {chat_id}")
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

    # Ignore photos (uncomment below to enable file_id retrieval for debugging)
    if message.photo:
        try:
            await context.bot.delete_message(chat_id=chat_id, message_id=message.message_id)
        except Exception as e:
            logger.warning(f"Failed to delete photo message in chat {chat_id}: {e}")
        return

    # Temporary photo handler to get file_id (uncomment to use)
    # if message.photo:
    #     file_id = message.photo[-1].file_id
    #     msg = await context.bot.send_message(
    #         chat_id=chat_id,
    #         text=f"📷 Received image! File ID: {file_id}"
    #     )
    #     logger.info(f"Received photo with file_id: {file_id}")
    #     return

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
            text="❌ Please use one of the commands: /start, /menu, /account, /comment"
        )
        context.user_data.setdefault("menu_messages", []).append(msg.message_id)

# Callback buttons
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    chat_id = query.message.chat_id
    message_id = query.message.message_id
    data = query.data

    logger.info(f"Button clicked in chat ID: {chat_id}, message ID: {message_id}, callback_data: {data}, current index: {context.user_data.get('carousel_index', 0)}")

    if data == "carousel_prev":
        current_index = context.user_data.get("carousel_index", 0)
        if current_index > 0:
            context.user_data["carousel_index"] = current_index - 1
            logger.info(f"Moving to previous index {context.user_data['carousel_index']} for chat ID {chat_id}")
            await show_carousel(chat_id, context, update_message_id=message_id)
        return

    if data == "carousel_next":
        current_index = context.user_data.get("carousel_index", 0)
        if current_index < len(MENU) - 1:
            context.user_data["carousel_index"] = current_index + 1
            logger.info(f"Moving to next index {context.user_data['carousel_index']} for chat ID {chat_id}")
            await show_carousel(chat_id, context, update_message_id=message_id)
        return

    if data == "carousel_reset":
        logger.info(f"Resetting carousel for chat ID {chat_id}")
        context.user_data["carousel_index"] = 0
        await clear_previous_menu(chat_id, context)
        await show_carousel(chat_id, context)
        return

    if data == "noop":
        logger.info(f"No-op button clicked in chat ID {chat_id}")
        return

    logger.warning(f"Unknown callback data: {data} in chat ID {chat_id}")

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
