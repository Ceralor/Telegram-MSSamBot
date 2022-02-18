#!/usr/bin/env python
import requests, logging

from telegram import InlineQueryResultArticle, InlineQueryResultVoice, Update, InputMediaAudio, InputMessageContent
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext, InlineQueryHandler
from uuid import uuid4
from pydub import AudioSegment
from io import BytesIO
from json import load as jsonload
from boto3 import Session as S3Session
from urllib.parse import urlencode, quote as urlquote

sapi4_api_url = 'https://tetyys.com/SAPI4/SAPI4'
s3bucket = 'mssambot'

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

with open('spaces_secret') as f:
    s3conf = jsonload(f)
s3session = S3Session()
s3client = s3session.client('s3', **s3conf)

with open("token_secret") as f:
    token_secret = f.readline()
updater = Updater(token=token_secret)
dispatcher = updater.dispatcher

def start(update: Update, context: CallbackContext):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Hi there! Use me in the inline to send cursed audio!")
start_handler = CommandHandler('start', start)
dispatcher.add_handler(start_handler)

def help(update: Update, context: CallbackContext):
    context.bot.send_message(chat_id=update.effective_chat.id, parse_mode="Markdown", text="""Use me inline to send a message, like so:

`@mssambot This is a tts clip`

Then click on the play button to preview before sending!
**Note:** A maximum of 1000 characters may be used at a time presently. If you exceed this you will not be offered an audio clip.""")
help_handler = CommandHandler('help', help)
dispatcher.add_handler(help_handler)

def inline_tts(update: Update, context: CallbackContext):
    query = update.inline_query.query
    if not query:
        return
    if len(query) > 1000:
        return
    param_dict = {'voice': 'Sam', 'speed': 150, 'pitch': 100, 'text': query}
    prep_params = urlencode(param_dict, quote_via=urlquote)
    r = requests.get(sapi4_api_url,params=prep_params)
    if r.status_code == 200:
        logger.log(logging.INFO, f"Converting audio from URL: {r.url}")
        samwav = AudioSegment.from_wav(BytesIO(r.content))
        samogg = BytesIO()
        samwav.export(samogg, format="libopus")
        fileid = str(uuid4())
        response = s3client.put_object(Bucket=s3bucket, Key=f"{fileid}", Body=samogg, ACL='public-read', ContentType="audio/ogg")
        if response['ResponseMetadata']['HTTPStatusCode'] == 200:
            samogg_url = f"{s3conf['endpoint_url']}/{s3bucket}/{fileid}"
            logger.log(logging.INFO,samogg_url)
            results = [
                InlineQueryResultVoice(id=fileid,
                title=query,
                voice_url=samogg_url,
                voice_duration=round(len(samwav)/1000),
                caption=f"MS Sam says... {query}")
            ]
            context.bot.answer_inline_query(update.inline_query.id, results)

inline_tts_handler = InlineQueryHandler(inline_tts)
dispatcher.add_handler(inline_tts_handler)
updater.start_polling()
