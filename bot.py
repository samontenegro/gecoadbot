# Utilities
import os
import logging
from enum import Enum

# Telegram bot API
import telegram
from telegram.ext import Updater, Filters, InlineQueryHandler

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
		print("SAM::INLIN QUERY")
		print(update, context)

if __name__ == "__main__":
	bot = GecoAdBot()
	bot.run()