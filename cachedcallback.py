import os

DEFAULT_TIMEOUT = 1

class CachedCallback():
	def __init__(self, timeout, callback):
		
		# Set timeout in seconds
		self.timeout = int(timeout) if int(timeout) >= 1 else DEFAULT_TIMEOUT

		# Init value
		self.data = None

		# Set callback
		if callable(callback):
			self.callback = callback
		else:
			raise RuntimeError 

	def set_data(self, data):
		pass

	def trigger_callback(self):
		pass