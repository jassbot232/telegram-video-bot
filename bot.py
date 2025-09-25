import os
import logging
from telegram import (
    Update, 
    InlineKeyboardButton, 
    InlineKeyboardMarkup,
    InputFile
)
from telegram.ext import (
    Application, 
    CommandHandler, 
    MessageHandler, 
    CallbackQueryHandler, 
    ContextTypes,
    filters
)
from config import BOT_TOKEN, get_temp_path, get_file_type, SUPPORTED_DOCUMENT_FORMATS, SUPPORTED_IMAGE_FORMATS
from user_manager import user_manager
from video_processor import VideoProcessor
import asyncio

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Enhanced Main Menu
MAIN_MENU = [
    [
        InlineKeyboardButton("🎥 Video Tools", callback_data="video_tools"),
        InlineKeyboardButton("📄 Document Tools", callback_data="document_tools")
    ],
    [
        InlineKeyboardButton("🖼️ Image Tools", callback_data="image_tools"),
        InlineKeyboardButton("🔊 Audio Tools", callback_data="audio_tools")
    ]
]

# Video Tools Menu
VIDEO_MENU = [
    [
        InlineKeyboardButton("🎞️ Convert Video", callback_data="video_convert_menu"),
        InlineKeyboardButton("🔀 Merge Videos", callback_data="video_merge_menu")
    ],
    [
        InlineKeyboardButton("✂️ Split Video", callback_data="video_split_menu"),
        InlineKeyboardButton("📊 Compress Video", callback_data="video_compress_menu")
    ],
    [
        InlineKeyboardButton("🔊 Extract Audio", callback_data="video_audio_menu"),
        InlineKeyboardButton("🎵 Merge Video+Audio", callback_data="video_av_merge_menu")
    ],
    [InlineKeyboardButton("🔙 Back", callback_data="main_menu")]
]

# Document Tools Menu
DOCUMENT_MENU = [
    [
        InlineKeyboardButton("📄 PDF to DOCX", callback_data="doc_pdf_docx"),
        InlineKeyboardButton("📝 PDF to TXT", callback_data="doc_pdf_txt")
    ],
    [
        InlineKeyboardButton("📋 DOCX to PDF", callback_data="doc_docx_pdf"),
        InlineKeyboardButton("🖼️ Image to PDF", callback_data="doc_img_pdf")
    ],
    [
        InlineKeyboardButton("🔄 Convert Format", callback_data="doc_convert_menu"),
        InlineKeyboardButton("📊 Compress PDF", callback_data="doc_compress_pdf")
    ],
    [InlineKeyboardButton("🔙 Back", callback_data="main_menu")]
]

# Image Tools Menu
IMAGE_MENU = [
    [
        InlineKeyboardButton("🖼️ Convert Format", callback_data="img_convert_menu"),
        InlineKeyboardButton("📐 Resize Image", callback_data="img_resize_menu")
    ],
    [
        InlineKeyboardButton("🎨 Compress Image", callback_data="img_compress_menu"),
        InlineKeyboardButton("🔄 Rotate Image", callback_data="img_rotate_menu")
    ],
    [InlineKeyboardButton("🔙 Back", callback_data="main_menu")]
]

# Video Format Selection
VIDEO_FORMATS = [
    [InlineKeyboardButton("MP4", callback_data="vformat_mp4"),
     InlineKeyboardButton("AVI", callback_data="vformat_avi")],
    [InlineKeyboardButton("MOV", callback_data="vformat_mov"),
     InlineKeyboardButton("MKV", callback_data="vformat_mkv")],
    [InlineKeyboardButton("WEBM", callback_data="vformat_webm"),
     InlineKeyboardButton("WMV", callback_data="vformat_wmv")],
    [InlineKeyboardButton("🔙 Back", callback_data="video_tools")]
]

# Document Format Selection
DOCUMENT_FORMATS = [
    [InlineKeyboardButton("PDF", callback_data="dformat_pdf"),
     InlineKeyboardButton("DOCX", callback_data="dformat_docx")],
    [InlineKeyboardButton("TXT", callback_data="dformat_txt"),
     InlineKeyboardButton("RTF", callback_data="dformat_rtf")],
    [InlineKeyboardButton("🔙 Back", callback_data="document_tools")]
]

# Image Format Selection
IMAGE_FORMATS = [
    [InlineKeyboardButton("JPG", callback_data="iformat_jpg"),
     InlineKeyboardButton("PNG", callback_data="iformat_png")],
    [InlineKeyboardButton("WEBP", callback_data="iformat_webp"),
     InlineKeyboardButton("BMP", callback_data="iformat_bmp")],
    [InlineKeyboardButton("PDF", callback_data="iformat_pdf"),
     InlineKeyboardButton("ICO", callback_data="iformat_ico")],
    [InlineKeyboardButton("🔙 Back", callback_data="image_tools")]
]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send welcome message and main menu"""
    welcome_text = """
🎬 *Welcome to Advanced File Converter Bot!*

I can help you convert and process:
• 🎥 Videos (Convert, Merge, Split, Compress)
• 📄 Documents (PDF, DOCX, TXT conversions)
• 🖼️ Images (Convert, Resize, Compress)
• 🔊 Audio (Extract, Convert)

Simply send me a file to get started!
    """
    
    keyboard = InlineKeyboardMarkup(MAIN_MENU)
    await update.message.reply_text(welcome_text, parse_mode='Markdown', reply_markup=keyboard)

async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming video files"""
    await handle_file(update, context, 'video')

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle document files"""
    document = update.message.document
    file_type = get_file_type(document.file_name)
    await handle_file(update, context, file_type)

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle photo files"""
    await handle_file(update, context, 'image')

async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE, file_type: str):
    """Generic file handler"""
    user_id = update.message.from_user.id
    
    try:
        # Download the file
        if file_type == 'video':
            file_obj = update.message.video
            file_ext = '.mp4'
        elif file_type == 'image':
            file_obj = update.message.photo[-1]  # Highest resolution
            file_ext = '.jpg'
        else:  # document
            file_obj = update.message.document
            file_ext = os.path.splitext(file_obj.file_name)[1].lower()
        
        file = await file_obj.get_file()
        file_path = get_temp_path(f"{user_id}_{file_obj.file_id}{file_ext}")
        await file.download_to_drive(file_path)
        
        # Store file info
        context.user_data['current_file'] = file_path
        context.user_data['file_type'] = file_type
        context.user_data['original_filename'] = getattr(file_obj, 'file_name', 'file')
        
        # Get file info
        file_info = await VideoProcessor.get_file_info(file_path)
        
        # Show appropriate menu based on file type
        if file_type == 'video':
            keyboard = InlineKeyboardMarkup(VIDEO_MENU)
            menu_text = "🎥 Video Tools"
        elif file_type == 'document':
            keyboard = InlineKeyboardMarkup(DOCUMENT_MENU)
            menu_text = "📄 Document Tools"
        elif file_type == 'image':
            keyboard = InlineKeyboardMarkup(IMAGE_MENU)
            menu_text = "🖼️ Image Tools"
        else:
            keyboard = InlineKeyboardMarkup(MAIN_MENU)
            menu_text = "Main Menu"
        
        info_text = f"✅ {file_type.upper()} received!\n"
        info_text += f"📁 Size: {file_info['size'] / 1024 / 1024:.2f} MB\n"
        
        if 'duration' in file_info:
            info_text += f"⏱️ Duration: {file_info['duration']:.2f}s\n"
        if 'resolution' in file_info:
            info_text += f"📊 Resolution: {file_info['resolution']}\n"
        if 'pages' in file_info:
            info_text += f"📄 Pages: {file_info['pages']}\n"
        
        await update.message.reply_text(info_text + f"\nWhat would you like to do?", reply_markup=keyboard)
        
    except Exception as e:
        logger.error(f"Error handling file: {e}")
        await update.message.reply_text("❌ Error processing file!")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle inline button clicks"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    data = query.data
    
    # Main menu navigation
    if data == "main_menu":
        keyboard = InlineKeyboardMarkup(MAIN_MENU)
        await query.edit_message_text("Choose an option:", reply_markup=keyboard)
    
    elif data == "video_tools":
        keyboard = InlineKeyboardMarkup(VIDEO_MENU)
        await query.edit_message_text("🎥 Video Tools - Choose an action:", reply_markup=keyboard)
    
    elif data == "document_tools":
        keyboard = InlineKeyboardMarkup(DOCUMENT_MENU)
        await query.edit_message_text("📄 Document Tools - Choose an action:", reply_markup=keyboard)
    
    elif data == "image_tools":
        keyboard = InlineKeyboardMarkup(IMAGE_MENU)
        await query.edit_message_text("🖼️ Image Tools - Choose an action:", reply_markup=keyboard)
    
    # Video conversions
    elif data == "video_convert_menu":
        keyboard = InlineKeyboardMarkup(VIDEO_FORMATS)
        await query.edit_message_text("Select output video format:", reply_markup=keyboard)
    
    elif data.startswith("vformat_"):
        format_type = data.replace("vformat_", "")
        await process_video_conversion(query, context, format_type)
    
    # Document conversions
    elif data == "doc_convert_menu":
        keyboard = InlineKeyboardMarkup(DOCUMENT_FORMATS)
        await query.edit_message_text("Select output document format:", reply_markup=keyboard)
    
    elif data.startswith("dformat_"):
        format_type = data.replace("dformat_", "")
        await process_document_conversion(query, context, format_type)
    
    # Image conversions
    elif data == "img_convert_menu":
        keyboard = InlineKeyboardMarkup(IMAGE_FORMATS)
        await query.edit_message_text("Select output image format:", reply_markup=keyboard)
    
    elif data.startswith("iformat_"):
        format_type = data.replace("iformat_", "")
        await process_image_conversion(query, context, format_type)
    
    # Specific document operations
    elif data == "doc_pdf_docx":
        await process_document_conversion(query, context, "docx")
    
    elif data == "doc_pdf_txt":
        await process_document_conversion(query, context, "txt")
    
    elif data == "doc_docx_pdf":
        await process_document_conversion(query, context, "pdf")

async def process_video_conversion(query, context, output_format):
    """Process video conversion"""
    if 'current_file' not in context.user_data:
        await query.edit_message_text("❌ Please send a video file first!")
        return
    
    await query.edit_message_text("🔄 Starting video conversion...")
    
    async def progress_callback(progress, status):
        try:
            await query.edit_message_text(f"🔄 Converting video... {progress}%\n{status}")
        except:
            pass
    
    try:
        output_path = await VideoProcessor.convert_video(
            context.user_data['current_file'],
            output_format,
            "high",
            progress_callback
        )
        
        # Send the converted file
        with open(output_path, 'rb') as file:
            await context.bot.send_document(
                chat_id=query.message.chat_id,
                document=InputFile(file, filename=f"converted.{output_format}"),
                caption=f"✅ Video converted to {output_format.upper()}!"
            )
        
        # Clean up
        os.unlink(output_path)
        
    except Exception as e:
        logger.error(f"Video conversion error: {e}")
        await query.edit_message_text("❌ Error during video conversion!")

async def process_document_conversion(query, context, output_format):
    """Process document conversion"""
    if 'current_file' not in context.user_data:
        await query.edit_message_text("❌ Please send a document file first!")
        return
    
    await query.edit_message_text("🔄 Starting document conversion...")
    
    async def progress_callback(progress, status):
        try:
            await query.edit_message_text(f"🔄 Converting document... {progress}%\n{status}")
        except:
            pass
    
    try:
        output_path = await VideoProcessor.convert_document(
            context.user_data['current_file'],
            output_format,
            progress_callback
        )
        
        # Send the converted file
        with open(output_path, 'rb') as file:
            await context.bot.send_document(
                chat_id=query.message.chat_id,
                document=InputFile(file, filename=f"converted.{output_format}"),
                caption=f"✅ Document converted to {output_format.upper()}!"
            )
        
        # Clean up
        os.unlink(output_path)
        
    except Exception as e:
        logger.error(f"Document conversion error: {e}")
        await query.edit_message_text("❌ Error during document conversion!")

async def process_image_conversion(query, context, output_format):
    """Process image conversion"""
    if 'current_file' not in context.user_data:
        await query.edit_message_text("❌ Please send an image file first!")
        return
    
    await query.edit_message_text("🔄 Starting image conversion...")
    
    async def progress_callback(progress, status):
        try:
            await query.edit_message_text(f"🔄 Converting image... {progress}%\n{status}")
        except:
            pass
    
    try:
        output_path = await VideoProcessor.convert_document(
            context.user_data['current_file'],
            output_format,
            progress_callback
        )
        
        # Send the converted file
        if output_format == 'pdf':
            with open(output_path, 'rb') as file:
                await context.bot.send_document(
                    chat_id=query.message.chat_id,
                    document=InputFile(file, filename="converted.pdf"),
                    caption="✅ Image converted to PDF!"
                )
        else:
            with open(output_path, 'rb') as file:
                await context.bot.send_photo(
                    chat_id=query.message.chat_id,
                    photo=InputFile(file),
                    caption=f"✅ Image converted to {output_format.upper()}!"
                )
        
        # Clean up
        os.unlink(output_path)
        
    except Exception as e:
        logger.error(f"Image conversion error: {e}")
        await query.edit_message_text("❌ Error during image conversion!")

def main():
    """Start the bot"""
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.VIDEO, handle_video))
    application.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    application.add_handler(CallbackQueryHandler(button_handler))
    
    # Start bot
    print("Advanced File Converter Bot is running...")
    application.run_polling()

if __name__ == "__main__":
    main()
