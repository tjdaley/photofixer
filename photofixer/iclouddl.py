"""
iClouddl.py - Class for downloading photos from iCloud.
"""
import os
from dotenv import load_dotenv
from pyicloud import PyiCloudService as api
from pyicloud.exceptions import PyiCloudFailedLoginException
load_dotenv()

class IcloudDownload():
	"""
	Class to download photos from iCloud.
	"""
	def __init__(self, username: str = None, password: str = None, destination: str = 'data/output'):
		self.username = username or input("Enter your iCloud username: ")
		self.password = password or input("Enter your iCloud password: ")
		self.api = None
		self.destination = destination
		self.albums = None
		self.albums_list = None
		self.photos = None
		self.album = None

	def login(self) -> bool:
		"""
		Login to iCloud.

		Returns:
			bool: True if login successful, False if not.
		"""
		try:
			self.api = api(self.username, self.password)
		except PyiCloudFailedLoginException:
			print('Login failed.')
			return False

		if api.requires_2fa:
			print("Two-factor authentication required.")
			code = input("Enter the code you received of one of your approved devices: ")
			result = api.validate_2fa_code(self.api, code=code)
			print("Code validation result: %s" % result)

			if not result:
				print("Failed to verify security code")
				return False

			if not api.is_trusted_session:
				print("Session is not trusted. Requesting trust...")
				result = api.trust_session()
				print("Session trust result %s" % result)

				if not result:
					print("Failed to request trust. You will likely be prompted for the code again in the coming weeks")
					return False
		elif api.requires_2sa:
			import click
			print("Two-step authentication required. Your trusted devices are:")

			devices = api.trusted_devices
			for i, device in enumerate(devices):
				print(
					"  %s: %s" % (i, device.get('deviceName',
					"SMS to %s" % device.get('phoneNumber')))
				)

			device = click.prompt('Which device would you like to use?', default=0)
			device = devices[device]
			if not api.send_verification_code(device):
				print("Failed to send verification code")
				return False

			code = click.prompt('Please enter validation code')
			if not api.validate_verification_code(device, code):
				print("Failed to verify verification code")
				return False
		return True

	def get_albums(self) -> bool:
		"""
		Get albums from iCloud.

		Returns:
			bool: True if successful, False if not.
		"""
		if self.api is None:
			print('Not logged in.')
			return False
		self.photos = self.api.photos
		self.albums = self.photos.albums
		albums = self.albums.values()
		self.albums_list = [str(a) for a in albums]
		print(*self.albums_list, sep="\n")
		for album in self.albums:
			self.albums_list.append(album)
		return True

	def get_album(self, album_id: str = 'all') -> bool:
		"""
		Get album from iCloud.

		Args:
			album_id (str, optional): Album ID. Defaults to 'all'.

		Returns:
			bool: True if successful, False if not.
		"""
		if self.api is None:
			print('Not logged in.')
			return False
		if album_id == 'all':
			self.album = self.photos.all
		elif album_id == 'favorites':
			self.album = self.photos.favorites
		elif album_id == 'moments':
			self.album = self.photos.moments
		elif album_id == 'years':
			self.album = self.photos.years
		elif album_id == 'shared':
			self.album = self.photos.shared_albums
		elif album_id == 'hidden':
			self.album = self.photos.hidden_albums
		elif album_id == 'folders':
			self.album = self.photos.folders
		else:
			for album in self.albums:
				if album.title == album_id:
					print(album.title)
					self.album = album
					break
		if self.album is None:
			print('Album not found.')
			return False
		self.album_name = self.album.title
		self.album_id = self.album.id
		return True

	def get_photos(self) -> bool:
		"""
		Get photos from iCloud.

		Returns:
			bool: True if successful, False if not.
		"""
		if self.api is None:
			print('Not logged in.')
			return False
		if self.album is None:
			print('Album not found.')
			return False
		self.photos_list = []

		for photo in self.album.photos:
			print("Photo:", photo.filename, photo.id, photo.created, photo.updated, photo.size)
			filename = f'{photo.filename} - {photo.id} - {photo.created} - {photo.location}.jpg'
			filepath = os.path.join(self.destination, self.album_name, filename)
			with open(filepath, 'wb') as f:
				f.write(photo.download().raw.read())
		return True

if __name__ == '__main__':
	icloud = IcloudDownload()
	logged_in = icloud.login()
	if not logged_in:
		exit(1)

	success = icloud.get_albums()
	if not success:
		exit(1)

	success = icloud.get_album('TRIAL PHOTOS')
	if not success:
		exit(1)
	
	success = icloud.get_photos()
	if not success:
		exit(1)
	#icloud.get_album('all')
	#icloud.get_photos()
