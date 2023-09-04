"""
photofixer.py - Class for fixing photos to produce in discovery
"""
import json
import os
import re
from datetime import datetime
from dateutil import parser as date_parser
from PIL import Image, ExifTags, ImageDraw, ImageFont, ImageOps
from pillow_heif import register_heif_opener
import PySimpleGUI as sg
import shutil
from hachoir.parser import createParser
from hachoir.metadata import extractMetadata
import cv2
from dotenv import load_dotenv
load_dotenv()


class PhotoFixer():
	"""
	Class to fix photos for discovery.
	"""
	def __init__(self, root_dir: str = 'input', output_path: str = 'output'):
		self.root_dir = root_dir
		self.output_path = output_path
		self.font_size = int(os.environ.get('font_size', 36))
		self.text_color = os.environ.get('text_color', 'black')
		self.box_color = os.environ.get('box_color', 'white')
		self.text_margin = int(os.environ.get('bates_margin', 4)) * 2
		self.box_margin = int(os.environ.get('box_margin', 1))
		font_name = os.environ.get('bates_font', 'arial.ttf')
		self.font = ImageFont.truetype(font_name, self.font_size)
		self.bates_prefix = ''
		self.bates_number = 1
		self.bates_digits = int(os.environ.get('bates_digits', 6))
		self.bates_suffix = ''
		self.target_width = float(os.environ.get('target_width', 6.5))
		self.target_height = float(os.environ.get('target_height', 9.0))
		self.target_dpi = int(os.environ.get('target_dpi', 300))
		self.filename_date_format = os.environ.get('filename_date_format', '%Y-%m-%d')
		self.image_date_format = os.environ.get('image_date_format', '%m/%d/%Y')
		self.points_per_inch = int(os.environ.get('points_per_inch', 72))
		self.valid_photo_file_types = ['.jpg', '.jpeg', '.png', '.heic', '.heif']
		self.valid_video_file_types = ['.mp4', '.mov', '.avi', '.wmv', '.mpg', '.mpeg', '.mkv']
		self.tmp_dir = os.environ.get('tmp_dir', 'tmp')
		register_heif_opener()
	
	def fix_malformed_date(self, date_str: str) -> str:
		"""
		Fix malformed date strings. For example, some cameras use a date format like
		```2020-12-31 23:59:59-05:00``` which is not a valid ISO 8601 date. This method
		fixes that by removing the colon from the timezone offset, resulting in a date
		string like ```2020-12-31 23:59:59-0500```.

		Also, some cameras use a date format like ```2020:12:31 23:59:59``` which is not
		a valid ISO 8601 date. This method fixes that by replacing the colons with dashes,
		resulting in a date string like ```2020-12-31 23:59:59```.

		Args:
			date_str (str): Date string to fix.

		Returns:
			(str): Fixed date string.
		"""
		result = date_str

		# Fix malformed date strings like 2020-12-31 23:59:59-05:00
		if date_str[-3] == ':' and date_str[-6] == '-':
			result = date_str[:-3] + date_str[-2:]

		# Fix malformed date strings like 2020:12:31 23:59:59
		if malformed := re.match("(\d)+:(\d+):(\d+) (\d+:\d+:\d+)", result):
			result = f"{malformed.group(0)}-{malformed.group(1)}-{malformed.group(2)} {malformed.group(3)}"

		return result
		
	def date_taken(self, filepath, img) -> str:
		"""
		Return a string containing the date the photograph was taken. Uses the *filename_date_format*
		environment variable to specify the format of the output string. If unable to determine the date
		then an empty string is returned.

		Args:
			filepath (str): Full path to the file
			img (PIL.Image): Image data to read.

		Returns:
			(str): Date from image metadata or an empty string if none found.
		"""
		result = ''
		try:
			exif_data = self.meta_list(filepath)
			date_taken_str = exif_data.get('DateTimeOriginal')
			if date_taken_str is None:
				date_taken_str = exif_data.get('DateTime')
			if date_taken_str is None:
				date_taken_str = exif_data.get('CreateDate')
			if date_taken_str is None:
				date_taken_str = exif_data.get('FileModifyDate')
			if date_taken_str is None:
				date_taken_str = exif_data.get('FileCreateDate')
			if date_taken_str is None:
				return ''
			date_taken_str = self.fix_malformed_date(date_taken_str)
			date_taken_dt = date_parser.parse(date_taken_str)
			result = date_taken_dt.strftime(self.filename_date_format)
		except Exception as e:
			print(f"date_taken(): Error extracting exif data: {str(e)}")
			pass
		return result
		
	def base_name(self, filepath: str) -> str:
		"""
		Return a string containing just the base name of the file, without the path and without
		the file type extension. For example ```/path/filename.jpg``` results in ```filename```.

		Args:
			filepath (str): Full path to the file

		Returns:
			(str): Base filename.
		"""
		filename = os.path.basename(filepath)
		name_parts = os.path.splitext(filename)[0].split('.')
		if len(name_parts) > 1:
			result = '.'.join(name_parts[:-1])
		else:
			result = name_parts[0]
		return result
		
	def meta_list(self, filepath: str):
		"""
		Method for testing reading metadata.
		"""
		with Image.open(filepath) as img:
			if hasattr(img, "_getexif"):
				exif_data = img._getexif()
				print("Meta_List():", exif_data)
				if exif_data:
					exif = {ExifTags.TAGS[k]: v for k, v in img._getexif().items()} #if k in ExifTags.TAGS}
					return exif
		return {}

	def image_date(self, filepath: str, image) -> str:
		"""
		Return the date the image was taken. If the image does not have an EXIF date then
		return None.

		Args:
			filepath (str): Full path to the file
			image (PIL.Image): Image data to read.

		Returns:
			(str): Date the image was taken.
		"""
		# If this is an image or video file, look for the date taken in the EXIF data.
		if os.path.splitext(filepath)[1].lower() in self.valid_photo_file_types + self.valid_video_file_types:
			return self.date_taken(filepath, image)

		# If this is a PDF file, look for the date created in the metadata.
		parser = createParser(filename)
		metadata = extractMetadata(parser)
		z=json.dumps(metadata, indent=4, sort_keys=True, default=str)
		parts = z.split('\\n')
		for part in parts:
			#print(f"part: {part}")
			if 'creation date' in part.lower():
				date_str = part.split(': ')[1].strip()
				date = datetime.strptime(date_str.replace('-', ':'), '%Y:%m:%d %H:%M:%S')
				#print(f"date: {date}")
				return date

		return None
		
	def date_stamp(self, img, date_str: str = None):
		"""
		Apply a date stamp to the image.

		Args:
			img (PIL.Image): Image data to which to add the Bates stamp.
			date_str (str): Date string to add to the image.

		Returns:
			(PIL.Image): Modified image
		"""
		if date_str is None:
			return img
		draw = ImageDraw.Draw(img)
		left, top, right, bottom = draw.textbbox((0,0), date_str, self.font)
		box_width = right - left
		box_height = bottom - top
		box_width += self.text_margin
		box_height += self.text_margin
		box_x = self.box_margin * self.points_per_inch
		box_y = img.height - box_height - (self.box_margin * self.points_per_inch)
		rectangle_dimensions = (box_x, box_y, box_x + box_width, box_y + box_height)
		draw.rectangle(rectangle_dimensions, fill=self.box_color)
		draw.text(
			(box_x + self.text_margin//2, box_y - self.text_margin//2),
			date_str,
			fill=self.text_color,
			font=self.font
		)
		return img

	def bates_stamp(self, img):
		"""
		Apply a Bates stamp to the image.

		Args:
			img (PIL.Image): Image data to which to add the Bates stamp.

		Returns:
			(PIL.Image): Modified image
		"""
		# If user starts with 0, then we don't want to stamp anything.
		if self.bates_number == 0:
			return img, ''

		bates_num_str = self.bates_num_str()
		bates_str = f'{self.bates_prefix}{bates_num_str}{self.bates_suffix}'
		draw = ImageDraw.Draw(img)
		left, top, right, bottom = draw.textbbox((0,0), bates_str, self.font)
		box_width = right - left
		box_height = bottom - top
		box_width += self.text_margin
		box_height += self.text_margin
		box_x = img.width - box_width - (self.box_margin * self.points_per_inch)
		box_y = img.height - box_height - (self.box_margin * self.points_per_inch)
		rectangle_dimensions = (box_x, box_y, box_x + box_width, box_y + box_height)
		draw.rectangle(rectangle_dimensions, fill=self.box_color)
		draw.text(
			(box_x + self.text_margin//2, box_y - self.text_margin//2),
			bates_str,
			fill=self.text_color,
			font=self.font
		)
		return img, bates_num_str

	def bates_num_str(self):
		"""
		Return a string containing the current Bates number, padded with leading zeros.
		"""
		bates_num = self.bates_number
		self.bates_number += 1
		bates_num_str = (('0'*self.bates_digits) + str(bates_num))[-self.bates_digits:]
		return bates_num_str
	
	def resize(self, img):
		"""
		Resize the image to the target dimensions.

		Args:
			img (PIL.Image): Image data to resize.

		Returns:
			(PIL.Image): Modified image
		"""
		tw = int(self.target_width * self.target_dpi)
		th = int(self.target_height * self.target_dpi)
		img = ImageOps.contain(img, (tw, th))
		return img

	def convert(self, filepath: str, output_path: str, apply_timestamps: bool = False):
		"""
		Read an image file, extract the date it was taken, resize the image, and apply
		a Bates label.

		Args:
			filepath (str): Path to the input file, e.g. /input/holiday/photo1.png
			output_path (str): Path for the output file, e.g. /output/holiday
			apply_timestamps (bool): If True, apply timestamps to the image.

		Returns:
			None
		"""
		with Image.open(filepath) as img:
			image_date_str = self.image_date(filepath, img)
			if image_date_str:
				image_date_str = ' (' + image_date_str + ')'
			else:
				image_date_str = ''
			img = self.resize(img)
			img, bates_num_str = self.bates_stamp(img)
			if apply_timestamps:
				img = self.date_stamp(img, image_date_str)
			filename = self.base_name(filepath)
			if self.bates_number != 0:
				pdf_name = f'{bates_num_str} - {filename}{image_date_str}.pdf'
			else:
				pdf_name = f'{filename}{image_date_str}.pdf'
			pdf_path = os.path.join(output_subdir, pdf_name)
			img.save(pdf_path, 'PDF', resolution=float(self.target_dpi), save_all=True)

	def tmp_video_file(self, filename: str) -> str:
		"""
		Use CV2 to capture a single video frame at the one second mark and save it as
		a temporary file, returning the filename.

		Args:
			filename (str): Path to the video file

		Returns:
			(str): Path to the temporary image file
		"""
		cap = cv2.VideoCapture(filename)
		cap.set(cv2.CAP_PROP_POS_MSEC, 1000)
		success, image = cap.read()
		if success:
			tmp_filename = os.path.join(self.tmp_dir, f'{self.base_name(filename)}_frame.png')
			cv2.imwrite(tmp_filename, image)
			return tmp_filename
		else:
			return None

def get_params():
	"""
	Use PySimpleGUI to get the user's input parameters. THe parameters are
	(1) Source Folder; (2) Destination Folder; (3) Bates Prefix; (4) Bates Suffix;
	(5) Bates Number; and (6) Bates Digits.
	"""
	# Define the window's contents
	image_elem = sg.Image(
		filename='./assets/splash_logo_400x267.png',
		key='-LOGO-',
		size=(400, 267)
	)

	width = 15
	layout = [
		[image_elem],
		[
			sg.Text(
				f"PhotoFixer 0.0.3",
				justification='center',
				expand_x=True,
				font=('Helvetica', 25),
				text_color="yellow"
			)
		],
		[sg.Text("Source Folder", size=width), sg.Input(key='-SOURCE-'), sg.FolderBrowse()],
		[sg.Text("Destination Folder", size=width), sg.Input(key='-DEST-'), sg.FolderBrowse()],
		[sg.Text("Bates Prefix", size=width), sg.Input(key='-PREFIX-')],
		[sg.Text("Bates Suffix", size=width), sg.Input(key='-SUFFIX-')],
		[sg.Text("Starting Bates Number", size=width), sg.Input(key='-NUMBER-')],
		[sg.Text("Bates Digits", size=width), sg.Input(key='-DIGITS-')],
		[sg.Text("Max file count", size=width), sg.Input(key='-MAX_FILES-')],
		[sg.Checkbox("Skip non-images", key='-SKIP_NONIMAGES-')],
		[sg.Checkbox("Apply timestamps", key='-TIMESTAMPS-')],
		[sg.Button('Ok'), sg.Button('Cancel')],
	]

	# Create the window
	window = sg.Window('Photo Fixer', layout)

	# Display and interact with the Window using an Event Loop
	_, values = window.read(close=True)
	return values

def _safeint(s) -> int:
	"""
	Safely convert a string to an integer. If the string cannot be converted,
	return 0.
	"""
	try:
		return int(s)
	except ValueError:
		return 0

"""
Reference usage of the PhotoFixer() class.
"""
if __name__ == '__main__':
	params = get_params()
	source_dir = params['-SOURCE-']
	dest_dir = params['-DEST-']
	bates_prefix = params['-PREFIX-']
	bates_suffix = params['-SUFFIX-']
	bates_number = _safeint(params['-NUMBER-'])
	bates_digits = _safeint(params['-DIGITS-'])
	max_files = _safeint(params['-MAX_FILES-'])
	skip_nonimages = params['-SKIP_NONIMAGES-']
	apply_timestamps = params['-TIMESTAMPS-']

	fixer = PhotoFixer(
		root_dir=source_dir,
		output_path=dest_dir,
	)
	fixer.bates_prefix = bates_prefix
	fixer.bates_suffix = bates_suffix
	fixer.bates_number = bates_number
	fixer.bates_digits = bates_digits
	valid_file_types = fixer.valid_photo_file_types + fixer.valid_video_file_types
	file_count = 0
	os.makedirs(fixer.tmp_dir, exist_ok=True)

	for subdir, dirs, files in os.walk(fixer.root_dir):
		# Create target folder
		relative_subdir = os.path.relpath(subdir, fixer.root_dir)
		output_subdir = os.path.join(fixer.output_path, relative_subdir)
		os.makedirs(output_subdir, exist_ok=True)
		
		# Process each file in the folder
		for file in files:
			# Stop if we've reached the maximum file count.
			if file_count >= max_files and max_files > 0:
				break

			print(file.center(80, "*"))
			filename = os.path.join(subdir, file)
			file_type = os.path.splitext(file)[1].lower()

			# Skip non-images if requested.
			if skip_nonimages and file_type not in valid_file_types:
				continue

			# Nothing to do for directories.
			if os.path.isdir(filename):
				continue

			# Copy files that are not images.
			if file_type not in valid_file_types:
				file_count += 1
				source = os.path.join(subdir, file)
				file_date = fixer.image_date(source, None)
				if file_date:
					file_date_str = ' (' + file_date.strftime(fixer.filename_date_format) + ')'
				else:
					file_date_str = ''
				basename = os.path.splitext(file)[0]
				file_type = os.path.splitext(file)[1]
				bates_str = 'X' * fixer.bates_digits
				destination = os.path.join(fixer.output_path, f'{bates_str} - {basename}{file_date_str}{file_type}')
				shutil.copy(source, destination)
				continue

			if file_type in fixer.valid_photo_file_types:
				# Process photos.
				file_count += 1
				fixer.convert(filename, output_subdir, apply_timestamps)
				continue

			if file_type in fixer.valid_video_file_types:
				# Process videos.
				file_count += 1
				tmp_filename = fixer.tmp_video_file(filename)
				if tmp_filename:
					fixer.convert(tmp_filename, output_subdir, apply_timestamps)
					os.remove(tmp_filename)

				# Copy the original file.
				source = os.path.join(subdir, file)
				file_date = fixer.image_date(source, None)
				if file_date:
					file_date_str = ' (' + file_date.strftime(fixer.filename_date_format) + ')'
				else:
					file_date_str = ''

				basename = os.path.splitext(file)[0]
				file_type = os.path.splitext(file)[1]
				bates_str = fixer.bates_num_str()
				destination = os.path.join(fixer.output_path, f'{bates_str} - {basename}{file_date_str}{file_type}')
				shutil.copy(filename, destination)
				continue
