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
```

<img width="412" alt="PhotoFixerGui" src="https://user-images.githubusercontent.com/14339485/234171120-43336df4-7253-471d-bb6f-843bbf2d1c21.png">

### Field Descriptions
Name | Description | Required?
-----|-------------|----------
Source Folder | The top-level folder to process. *photofixer* will traverse through all subfolders, replicating the folder structure in the *Destination Folder*. | Yes
Destination Folder | The top-level folder to copy files to. *photofixer* will replicate the structure of the *Source Folder* and its children here. | Yes
Bates Prefix | Characters to place before the Bates number. If you want a space between the characters and the Bates number, include it here. For example, if you enter "TJD" as the Bates Prefix, the Bates stamps will look like "TJD000001". If you enter "TJD " as the Bates Prefix, the Bates stamps will look like "TJD 000001". | No
Bates Suffix | Characters to place after the Bates number. If you want a space between the Bates number and these characters, then enter it here. For example if the Bates Suffix is "(Produced 2023.04.24)" then the Bates numbers will loo like "000001(Produced 2023.04.24)". If you precede the characters with a space, e.g. " (Produced 2023.04.24)", the Bates stampe will look like "000001 (Produced 2023.04.24)". | No
Starting Bates Number | The Bates number to start with. If you do NOT want your documents to be Bates labeled, enter "0" (zero) as the starting number. Otherwise, enter the integer number at which you want Bates numbering to begin. | Yes
Bates Digits | This is the number of digits that the Bates number will be left-zero-filled to produce. For example, if you enter 6 as the Bates Digits value, then the Bates numbers will look like this: 000001, 000002, 000003, etc. If you enter, say, 4, they will look like this: 0001, 0002, 0003, etc. This number is required if Starting Bates Number is an integer value greater than one, i.e. you want the photos to be Bates numbered. Otherwise, the value is not needed. | No

## Future Enhancements

### Bullet-Proof GUI

Right now, a careless user can blow up the program by entering invalid values or skipping required values. No harm is done, but it's annoying for a program to let you mess up and then laugh at you.

Also, provide GUI access to all possible settings.

### Preserve Settings

Save settings between sessions so that you can easily re-run the program with the same settings.

### Allow User-Defined Date/Time Format

The description says it all.

### Permit Users to Select Colors and Alpha Channels

Let the user select back ground colors, no background color, and the alpha channel for see-throguh backgrounds. Let the user select foreground colors.

### Create an Output Log

Create an output log showing the Bates number and the file name.

###

Install as a package so that it's easier to create a click to install/click to run interface that does not require an excursion into the command line interface.

## Author

Thomas J. Daley is a Texas Family Law litigation attorney board certified in family law by the Texas Board of Legal Specialization. He practices primarily in Collin, Dallas, Denton, Rockwall, and Tarrant counties in Texas and appears pro hac vice in cases throughout the United States.
