# Utilities
import os
import logging
from enum import Enum

# Telegram bot API
import telegram
from telegram.error import TelegramError
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

class GecoAdBotInstance():
	def __init__(self, user_id, timer_ref, ad_sheet_manager_ref):

		# Initialize internal vars
		self.user_id 				= user_id
		self.timer_ref 				= timer_ref
		self.ad_sheet_manager_ref 	= ad_sheet_manager_ref
		self.buffered_inline_query 	= BufferedCallback(self.process_inline_query)

		# Register buffered callback to timer
		self.timer_ref.register_listener(self.user_id, self.update)

	def update(self):
		# Update counters on buffered_inline_query and own timeout counter
		self.buffered_inline_query.update_counter()

	def set_query(self, query):
		# Pass query data to BufferedCallback instance
		logger.info(f"User instance at {self.user_id} buffering \'{query[0].inline_query.query}\'")
		self.buffered_inline_query.set_data(query)

	def process_inline_query(self, update, context):
		inline_query = update.inline_query
		search_string = inline_query.query

		logger.info(f"User instance at {self.user_id} processing search string \'{search_string}\'")
		ad_list = self.ad_sheet_manager_ref.get_ads_from_string(search_string)

		# If ad_list is valid, respond with list
		if ad_list is not None:
			query_response = self.build_inline_query_response(ad_list)

			try:
				inline_query.answer(query_response, cache_time = 60)
			except TelegramError as e:

				# Hack - the following is a hack because the python-telegram-bot developers can't be bothered to add actual error classes for the different
				# types of query response fails; every error is raised as a BadRequest and it's impossible to check what is a network error, a timeout, or
				# some other kind of error. This snippet is verbatim from a Github discussion on why the developers don't want to add custom errors. This
				# is coloquially considered best practice, despite being an abomination that should never be done anywhere in any piece of production code,
				# ever.

				logger.info(f"An error occurred attempting to answer query \'{search_string}\' from {self.user_id}")
				if str(e) == 'Query is too old and response timeout expired or query id is invalid':
					logger.info("Query is too old and response timeout expired or query id is invalid") # log to INFO and do nothing
				else: 
					logger.error(str(e)) # log to ERROR
			else:
				logger.info(f"User instance at {self.user_id} answered query for search string \'{search_string}\'")

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

		# Init user->bot instance mapping
		self.user_map = {}

		# Initialize Sheet Manager
		self.ad_sheet_manager = AdSheetManager()

		# Initialize HeartBeat and BufferedCallback for inline query buffering
		self.heartbeat = Heartbeat(1)
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
			logger.info(f"Initializing main bot at port {PORT}")

			self.updater.start_webhook(listen = "0.0.0.0", port = PORT, url_path = self.token, 
										webhook_url = f"https://{T_APP_NAME}.herokuapp.com/{self.token}")

		else:

			logger.info("Initializing main bot in dev deploy mode")
			self.updater.start_polling()
			self.updater.idle()

	# Handlers
	def handle_inline_query(self, update, context):
		# Reject empty queries
		if update.inline_query.query == '':
			return

		# Pass query to user instance bot
		if update.inline_query.from_user.id is not None:
			user_id = update.inline_query.from_user.id

			logger.info(f"Received query \'{update.inline_query.query}\' from user_id {user_id}")

			if user_id not in self.user_map:
				self.user_map[user_id] = GecoAdBotInstance(user_id, self.heartbeat, self.ad_sheet_manager)
				logger.info(f"User instance initialized for {user_id}")

			query = (update, context)
			self.user_map[user_id].set_query(query)

if __name__ == "__main__":
	bot = GecoAdBot()
	bot.run()