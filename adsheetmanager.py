# Google Sheets API and auth
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Helper Classes
from enum import Enum

# Levenshtein metric for fuzzy string matching
import Levenshtein as lev

# Levenshtein ratio minimum threshold
MIN_LEVENSHTEIN_RATIO = 0.8

# Aux constants
NEWLINE_CHAR = '\n'

# Google Sheets data
MAIN_SPREADSHEET_NAME = "Hoja de Geco Ads"

# Enum for sheet data fields
class AdSheetDataEnum(Enum):
	MESSAGE_KEY 	= "MENSAJE"
	MEDIA_KEY 		= "MEDIA"

class GecoAd():
	def __init__(self, msg, media):
		
		# Check for completely ads with no content
		if msg == '':
			raise ValueError

		self.msg 	= msg
		self.media 	= media if media != '' else None 	# Expects a single url to a related image (JPEG)

class AdSheet():

	def __init__(self, sheet_title, sheet_ref):

		# Init sheet title
		self.title = sheet_title
		self.worksheet_ref = sheet_ref

	def get_ads(self):
		ads = []
		for ad_entry in self.worksheet_ref.get_all_records():
			try:
				ads.append(GecoAd(
									ad_entry[AdSheetDataEnum.MESSAGE_KEY.value], 
									ad_entry[AdSheetDataEnum.MEDIA_KEY.value]
								))

			# If ad has invalid data, skip
			except ValueError:
				continue
		
			# If there's a key error, something's wrong with the spreadsheet!
			except KeyError as e:
				return []
		return ads

# Simple class for managing spreadsheet operations using Google Sheets API
class AdSheetManager():

	def __init__(self):

		# Define API scope for our manager
		self.scope = gspread.auth.READONLY_SCOPES

		# Default values for credentials and G Sheet client
		self.creds 	= None
		self.client = None

		# Default worksheet dict
		self.worksheet_dict = {}

		try:
			# Retrieve credentials file and authenticate client
			self.creds 	= ServiceAccountCredentials.from_json_keyfile_name("cred.gkey", self.scope)
			self.client = gspread.authorize(self.creds)
			self.spreadsheet = self.client.open(MAIN_SPREADSHEET_NAME)

		except FileNotFoundError:
			print("AdSheetManager::__init__ Credentials file was not found! Please check your working directory for cred.gkey")

		if self.creds is None or self.client is None:
			raise RuntimeError

		# Build sheet dictionary object
		self.worksheet_list = self.spreadsheet.worksheets()
		for worksheet_object in self.worksheet_list:
			try:
				# Build an AdSheet object from base gspread class
				ad_sheet = AdSheet(worksheet_object.title, worksheet_object)
				self.worksheet_dict[worksheet_object.title] = ad_sheet

			except Exception:
				print("AdSheetManager::__init__ Invalid worksheet object")
				continue
	
	def get_ads_from_string(self, string):
		ad_category = None
		
		# Attempt to resolve an ad category from string
		ad_category = self.get_category_sheet_from_string(string)

		# If no match is available, return None
		if ad_category is None:
			return
		
		# If there is a match, return ad list
		return ad_category.get_ads()

	# Returns a reference to the AdSheet corresponding to the category string as worksheet title (fuzzy matching)
	def get_category_sheet_from_string(self, string):
		computed_lev_ratios = {}

		# Compute Levenshtein distance ratios
		for ad_category in self.worksheet_dict:
			computed_lev_ratios[ad_category] = lev.ratio(string.upper(), ad_category)

		# Return ad_category with highest ratio
		top_category_match = max(computed_lev_ratios, key=computed_lev_ratios.get)

		if computed_lev_ratios[top_category_match] > MIN_LEVENSHTEIN_RATIO:
			return self.worksheet_dict[top_category_match]
		
		# If minimum value is not achieved, return nothing
		return

if __name__ == "__main__":

	# Instantiate Sheet Manager
	manager = SheetManager()

