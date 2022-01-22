# Utilities
import os
import logging
from enum import Enum

# Telegram bot API
import telegram
from telegram.ext import Updater, Filters, InlineQueryHandler
from telegram import InlineQueryResultPhoto, InlineQueryResultArticle, InputTextMessageContent

# Helper classes
from heartbeat import Heartbeat
from bufferedcallback import BufferedCallback
from adsheetmanager import AdSheetManager
from uuid import uuid4

# Instantiate and configure logger
logging.basicConfig(
	level = logging.INFO, format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s,"
)

logger = logging.getLogger()

class GecoAdBot():

	def __init__(self):

		# Fetch deploy mode
		self.deploy_mode = os.getenv("T_DEPLOY_MODE")

		# Fetch API token and hashed password from environment variables
		self.token = os.getenv("T_API_TOKEN") if self.deploy_mode == "prod" else os.getenv("T_DEV_API_TOKEN")

		# Halt runtime if token isn't set
		if not self.token:
			raise RuntimeError

		# Instantiate Updater and Dispatcher
		self.updater 	= Updater(self.token, use_context=True, workers=8)
		self.dispatcher = self.updater.dispatcher

		# Initialize Sheet Manager
		self.ad_sheet_manager = AdSheetManager()

		# Initialize HeartBeat and BufferedCallback for inline query buffering
		self.heartbeat = Heartbeat(1)
		self.buffered_inline_query = BufferedCallback("process_inline_query", self.process_inline_query, self.heartbeat)
		self.heartbeat.start_timer()

	def add_handlers(self):

		# Build inline query handlers
		inline_query_handler = InlineQueryHandler(self.handle_inline_query)

		# Data and flow
		self.dispatcher.add_handler(inline_query_handler)

	def run(self):

		# Add handlers and start bot
		self.add_handlers()

		if self.deploy_mode == "prod":

			# if deployed to production environment, set up webhook
			PORT = int(os.environ.get('PORT', '8443'))

			# Start and set webhook
			T_APP_NAME = os.getenv("T_APP_NAME")

			# Log init
			logger.info("Initializing main bot at port {port}".format(port=PORT))

			self.updater.start_webhook(listen = "0.0.0.0", port = PORT, url_path = self.token, 
										webhook_url = f"https://{T_APP_NAME}.herokuapp.com/{self.token}")

		else:
			self.updater.start_polling()
			self.updater.idle()

	# Handlers
	def handle_inline_query(self, update, context):
		# Reject empty queries
		if update.inline_query.query == '':
			return

		# Pass down query
		query = (update, context)
		self.buffered_inline_query.set_data(query)

	def process_inline_query(self, update, context):
		inline_query = update.inline_query
		search_string = inline_query.query
		ad_list = self.ad_sheet_manager.get_ads_from_string(search_string)

		# If ad_list is valid, respond with list
		if ad_list is not None:
			query_response = self.build_inline_query_response(ad_list)
			inline_query.answer(query_response, cache_time = 20)

	# Inline Response
	def build_inline_query_response(self, ad_list):
		response_list = []

		for geco_ad in ad_list:
			if geco_ad.media is not None:
				response_list.append(
					InlineQueryResultPhoto(
						id 			= str(uuid4()),
						title 		= geco_ad.msg[:20] + "...",
						description = geco_ad.msg,
						photo_url 	= geco_ad.media,
						thumb_url 	= geco_ad.media,
						caption 	= geco_ad.msg
				))
			else:
				response_list.append(
					InlineQueryResultArticle(
						id 			= str(uuid4()),
						title 		= geco_ad.msg[:20] + "...",
						description = geco_ad.msg,
						input_message_content = InputTextMessageContent(
							message_text = geco_ad.msg
						)
				))
		
		return response_list

if __name__ == "__main__":
	bot = GecoAdBot()
	bot.run()