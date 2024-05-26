import os
import instaloader
from telegram import Update, InputFile
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext, ConversationHandler
from dotenv import load_dotenv
import shutil

# Load environment variables
load_dotenv()
tg_token = os.getenv("TG_TOKEN")

# Initialize Instaloader
L = instaloader.Instaloader()

# Define states for conversation handler
WAITING_FOR_LINK = 0

# Define start command
async def start_command(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text('Welcome! Use /downloadreel to download an Instagram reel.')

# Define help command
async def help_command(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text('Use /start to go to the main menu and use /downloadreel to download an Instagram reel.')

async def send_user_info_to_admin(context: CallbackContext, user_info: str) -> None:
    await context.bot.send_message(chat_id=971994173, text=user_info)

# Define download reel command
async def download_reel_command(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text('Send a reel link to receive the video.')
    return WAITING_FOR_LINK

# Function to download Instagram Reel
def download_reel(url: str, download_dir: str) -> str:
    try:
        # Extract shortcode from URL
        shortcode = url.split("/")[-2]
        post = instaloader.Post.from_shortcode(L.context, shortcode)

        # Set directory for download
        L.download_post(post, target=download_dir)

        # Check if video file exists in the download directory
        for root, _, files in os.walk(download_dir):
            for file in files:
                if file.endswith('.mp4'):
                    source_path = os.path.join(root, file)
                    dest_path = os.path.join(download_dir, f"{shortcode}.mp4")
                    shutil.move(source_path, dest_path)
                    return dest_path
        return None
    except Exception as e:
        print(e)
        return None

# Function to handle reel link input
async def handle_reel_link(update: Update, context: CallbackContext) -> None:
    url = update.message.text
    if "instagram.com/reel" in url or "instagram.com/p" in url:
        await update.message.reply_text('Downloading the reel...')
        download_dir = "downloads"
        os.makedirs(download_dir, exist_ok=True)
        file_path = download_reel(url, download_dir)
        if file_path:
            await update.message.reply_text('Reel downloaded successfully. Sending it to you...')
            try:
                print(update.message.chat_id, update.message.chat.first_name, update.message.chat.last_name, update.message.chat.username)
                user_info = f"Chat ID: {update.message.chat_id}\nFirst Name: {update.message.chat.first_name}\nLast Name: {update.message.chat.last_name}\nUsername: {update.message.chat.username}"
                await send_user_info_to_admin(context, user_info)
                await context.bot.send_video(chat_id=update.message.chat_id, video=open(file_path, 'rb'))
            except Exception as e:
                await update.message.reply_text(f'Failed to send the video: {e}')
            finally:
                shutil.rmtree(download_dir)
        else:
            await update.message.reply_text('Failed to download the reel. Please check the URL and try again.')
    else:
        await update.message.reply_text('Invalid URL. Please send a valid Instagram Reel link.')
        return WAITING_FOR_LINK

    return ConversationHandler.END

if __name__ == '__main__':
    print("Starting the bot...")
    app = Application.builder().token(tg_token).build()

    # Conversation handler
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('downloadreel', download_reel_command)],
        states={
            WAITING_FOR_LINK: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_reel_link)
            ]
        },
        fallbacks=[CommandHandler('start', start_command)]
    )

    # Command handlers
    app.add_handler(conv_handler)
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))

    print("Looking for new messages...")
    app.run_polling(poll_interval=5)
