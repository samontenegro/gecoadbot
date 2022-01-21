import os
from heartbeat import Heartbeat

DEFAULT_TIMEOUT = 3

# Callback wrapper class for load-balancing fast data updates
class BufferedCallback():
	def __init__(self, id, callback, timer = None, timeout = DEFAULT_TIMEOUT):

		# Set timeout in seconds
		self.timeout = int(timeout) if int(timeout) >= 1 else DEFAULT_TIMEOUT
		self.timeout_counter = 0

		# Init value
		self.data = None

		# Set callback
		if callable(callback):
			self.callback = callback
		else:
			raise RuntimeError
		
		# Initialize HeartBeat
		if timer is not None:
			self.heartbeat = timer
			self.heartbeat.register_listener(id, self.update_counter)
		else:
			raise RuntimeError

	def set_data(self, data):
		if data is not None:
			self.data = data
			self.reset_counter()

	def trigger_callback(self):
		# Re-check callback reference is still callable-type
		if callable(self.callback) and self.data is not None:

			# Support expanding arguments via tuple deconstruction (*args)
			if type(self.data) is tuple:
				return self.callback(*self.data)
			else:
				return self.callback(self.data)

	def update_counter(self):
		if self.timeout_counter > 0:
			self.timeout_counter -= 1

			if self.timeout_counter == 0:
				self.trigger_callback()

	def reset_counter(self):
		self.timeout_counter = self.timeout