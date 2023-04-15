"""
photofixer.py - Class for fixing photos to produce in discovery
"""
import json
import os
from datetime import datetime
from PIL import Image, ExifTags, ImageDraw, ImageFont
from pillow_heif import register_heif_opener
from pydotenv import load_dotenv
load_dotenv()


class PhotoFixer():
	"""
	Class to fix photos for discovery.
	"""
	def __init__(self, root_dir: str = 'input', output_path: str = 'output'):
		self.root_dir = root_dir
		self.output_path = output_path
		self.font_size = int(os.environ.get('font_size', 14))
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
		bates_num_str = (('0'*self.bates_digits) + str(self.bates_number))[-self.bates_digits:]
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
		return img
		
	def resize(self, img):
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
			img = self.bates_stamp(img)
			filename = self.base_name(filepath)
			pdf_name = f'{date_str} - {filename}.pdf'
			pdf_path = os.path.join(output_subdir, pdf_name)
			img.save(pdf_path, 'PDF', resolution=self.target_dpi)

"""
Reference usage of the PhotoFixer() class.
"""
if __name__ == '__main__':
	fixer = PhotoFixer()
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
			print(file.center(80, "*"))
			filename = os.path.join(subdir, file)
			if not os.path.isdir(filename):
				fixer.convert(filename, output_subdir)
				# print(fixer.meta_list(filename))
