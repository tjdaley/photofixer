# photofixer
Prepares image files for production in discovery by converting to PDF and applying a Bates label.

## Problem

Clients share image files (jpg, png, meic, tif) that are responsive to requests for production or which must be disclosed prior to trial. Further complicating matters, the image files can contain images of any size from huge to quite small. Litigtion support staff must then resize the images, convert them to PDF files, and then apply Bates numbers. This is a tedious and time-consuming process that not only burns scarce litigation support resources but also imposes unnecessary costs to the client.

Another problem is that obtaining the date of a photo can be tedious and clients don't always remember the exact date a photo was taken.

## Solution

**photofixer** traverses a source folder, replicates the folder structure to a destination folder, and then resizes, converts, and stamps each image file before placing it in the corresponding replicated folder. The result is a duplicated folder structure containing the "fixed" photos and a source folder that is untouched.

It also reads metadata on the image file to determine the date and time the photo was taken and applies a date/timestamp to the photo image.

## Environment Variables

This project uses the *pydotenv* pacakge for loading a file named *.env" so that calls to *os.environ.get()* will retrieve the less commonly adjusted runtime parameters. The following environment variables are used:

Variable | Description | Default
---------|-------------|--------
bates_margin | Number of picxels by which each side of the Bates label box exceeds the size of the text | 4
box_color | Color of background box used in Bates labeling | "white"
bates_digits | Number of digits used to pad out the Bates number | 6
bates_font | Name of the TrueType font used in creating the Bates label | arial.ttf
box_margin | Distance from the left and bottom edges of the image where the Bates label is placed | 1
font_size | Size of the font to use in Bates labeling, in points | 14
filename_date_format | *strftime()* format specifier for date/timestamps (not used, see below) | %Y-%m-%d
points_per_inch | Number of font points per inch | 72
target_dpi | Resolution of the output image in dots per inch | 300
target_height | Height of the output image in inches | 9.0
target_width | Width of the output image in inches | 6.5
text_color | Color of text used in Bates labeling | "black"

## Required packages

Package | Use
--------|-----
Pillow | Reading and processing .jpg, .png, and .tif images
pillow-heif | Reading and processing .heic images
python-dotenv | Processing the *.env* file into os.environ dictionary

These are all referenced in the accompanying ```requirements.txt``` file and can be installed like this:

```
# Windows
python -m venv venv
venv\scripts\activate.bat
pip install -r requirements.txt
```

## Example Usage

If you want to just run it as is, the app will look for a folder called ```input``` in the current directory and replicate its structure in a folder called ```output``` in the current directory.

```
python photofixer.py
Bates prefix (include trailing space if needed): TJD
Bates suffix (include leading space if needed) :  (produced 01/29/2023)
Staring Bates number                           : 1
```
## Author

Thomas J. Daley is a Texas Family Law litigation attorney board certified in family law by the Texas Board of Legal Specialization. He practices primarily in Collin, Dallas, Denton, Rockwall, and Tarrant counties in Texas and appears pro hac vice in cases throughout the United States.
