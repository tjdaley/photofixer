# photofixer
Prepares image files for production in discovery by converting to PDF and applying a Bates label.

## Problem

Clients share image files (jpg, png, meic, tif) that are responsive to requests for production or which must be disclosed prior to trial. Further complicating matters, the image files can contain images of any size from huge to quite small. Litigtion support staff must then resize the images, convert them to PDF files, and then apply Bates numbers. This is a tedious and time-consuming process that not only consumes scarce litigation support resources but also imposes high cost to the client.

## Solution

**photofixer** traverses a source folder, replicates the folder structure to a destination folder, and then resizes, converts, and stamps each image file before placing it in the corresponding replicated folder. The result is a duplicated folder structure containing the "fixed" photos and a source folder that is untouched.

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
## Future Enhancements

### Process Metadata to Extract Date

I developed this on a Windows platform, which prevented me from integrating the *pyheif* package for reading metadata from *.heic* files. Also, none of my test images contained Exif data. A useful enhancement would be to extract the Date the photograph was taken and include it either in the image in a manner similar to the Bates label or in the filename. A common objection to photographs in trial is that they are undated. For the most part, that is an invalid objection so long as the sponsoring witness can attest that the photograph is an accurate representation of that which it depicts at the time relevant to the witness's testimony. Nonetheless, preserving that information would help the attorney generate a timeline of events and overcome objections, however meritless they may be.

### User Interface

This implementation uses the Python *input()* function to obtain runtime parameters. A simple GUI whether implemented as a Python-based GUI or a browser-based GUI that calls on a server would make this more usable. It would also be useful to process command-line arguments for runtime parameters.

## Author

Thomas J. Daley is a Texas Family Law litigation attorney board certified in family law by the Texas Board of Legal Specialization. He practices primarily in Collin, Dallas, Denton, Rockwall, and Tarrant counties in Texas but appears pro hac vice in cases throughout the United States.
