"""
photofixer.py - Class for fixing photos to produce in discovery
"""
import json
import os
from datetime import datetime
from PIL import Image, ExifTags, ImageDraw, ImageFont, ImageOps
from pillow_heif import register_heif_opener
import shutil
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
		self.points_per_inch = int(os.environ.get('points_per_inch', 72))
		self.valid_file_types = ['.jpg', '.jpeg', '.png', '.heic', '.heif']
		register_heif_opener()
		
	def date_taken(self, img):
		"""
		Return a string containing the date the photograph was taken. Uses the *filename_date_format*
		environment variable to specify the format of the output string. If unable to determine the date
		then an empty string is returned.

		Args:
			img (PIL.Image): Image data to read.

		Returns:
			(str): Date from image metadata or an empty string if none found.
		"""
		result = ''
		try:
			date_taken_str = img._getexif.get(36867)
			date_taken = datetime.strptime(date_taken_str, '%Y:%m:%d %H:%M:%S')
			result = date_taken.strftime(self.filename_date_format)
		except Exception as e:
			# print(f"Error extracting exif data: {str(e)}")
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
				print(exif_data)
				if exif_data:
					exif = {ExifTags.TAGS[k]: v for k, v in img._getexif().items()} #if k in ExifTags.TAGS}
					return exif
		return {}
		
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
			(box_x + self.text_margin//2, box_y + self.text_margin//2),
			bates_str,
			fill=self.text_color,
			font=self.font
		)
		self.bates_number += 1
		return img, bates_num_str

	def bates_num_str(self):
		bates_num = self.bates_number
		self.bates_number += 1
		bates_num_str = (('0'*self.bates_digits) + str(bates_num))[-self.bates_digits:]
		return bates_num_str
	
	def resize(self, img):
		tw = int(self.target_width * self.target_dpi)
		th = int(self.target_height * self.target_dpi)
		img = ImageOps.contain(img, (tw, th))
		return img

	def resize_gpt(self, img, width=None, height=None):
		"""Resizes an image while maintaining its aspect ratio, and ensuring that neither the
		width nor the height of the image is increased."""
		img_width, img_height = img.size
		if width is None:
			width = self.target_width * self.target_dpi
		else:
			width *= self.target_dpi
		if height is None:
			height = self.target_height * self.target_dpi
		else:
			height *= self.target_dpi
		print(width, height, self.target_dpi, img_width, img_height)
		if img_width / img_height > width / height:
			# The width of the image is greater than the target width/height ratio
			new_width = int(img_height * (width / height))
			new_height = img_height
		else:
			# The height of the image is greater than the target width/height ratio
			new_width = img_width
			new_height = int(img_width * (height / width))
		resized_img = img.resize((new_width, new_height))
		return resized_img

	def resize_old(self, img):
		"""
		Resize an image to a uniform, fixed size, preserving the aspect ratio.

		Args:
			img (PIL.Image): Input image data from original image file.

		Returns:
			(PIL.Image): New image, resized per values set in environment variables.
		"""
		original_width, original_height = img.size
		if original_width >= original_height:
			aspect_ratio = original_height / original_width
			tw = self.target_height
			th = self.target_width
		else:
			aspect_ratio = original_width / original_height
			tw = self.target_width
			th = self.target_height
		target_width_px = int(tw * aspect_ratio * self.target_dpi)
		target_height_px = int(th * aspect_ratio * self.target_dpi)
		return img.resize((target_width_px, target_height_px))
		
	def convert(self, filepath: str, output_path: str):
		"""
		Read an image file, extract the date it was taken, resize the image, and apply
		a Bates label.

		Args:
			filepath (str): Path to the input file, e.g. /input/holiday/photo1.png
			output_path (str): Path for the output file, e.g. /output/holiday

		Returns:
			None
		"""
		with Image.open(filepath) as img:
			date_str = self.date_taken(img)
			img = self.resize(img)
			img, bates_num_str = self.bates_stamp(img)
			filename = self.base_name(filepath)
			if self.bates_number != 0:
				pdf_name = f'{bates_num_str} - {filename}.pdf'
			else:
				pdf_name = f'{filename}.pdf'
			pdf_path = os.path.join(output_subdir, pdf_name)
			img.save(pdf_path, 'PDF', resolution=float(self.target_dpi), save_all=True)

"""
Reference usage of the PhotoFixer() class.
"""
if __name__ == '__main__':
	fixer = PhotoFixer(root_dir='collard_deleted_dad', output_path='collard_deleted_dad_pdf')
	fixer.bates_prefix = input("Bates prefix (include trailing space if needed): ")
	fixer.bates_suffix = input("Bates suffix (include leading space if needed) : ")
	fixer.bates_number = int(input("Starting Bates number                          : "))
	for subdir, dirs, files in os.walk(fixer.root_dir):
		# Create target folder
		relative_subdir = os.path.relpath(subdir, fixer.root_dir)
		output_subdir = os.path.join(fixer.output_path, relative_subdir)
		os.makedirs(output_subdir, exist_ok=True)
		
		# Process each file in the folder
		for file in files:
			file_type = os.path.splitext(file)[1]
			if file_type.lower() not in fixer.valid_file_types:
				source = os.path.join(subdir, file)
				destination = os.path.join(fixer.output_path, f'{fixer.bates_num_str()} - {file}')
				print(f"Copying {source} to {destination}".center(80, "*"))
				shutil.copy(source, destination)
				continue
			print(file.center(80, "*"))
			filename = os.path.join(subdir, file)
			if not os.path.isdir(filename):
				fixer.convert(filename, output_subdir)
				# print(fixer.meta_list(filename))
