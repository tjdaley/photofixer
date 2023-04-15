# photofixer
Prepares image files for production in discovery by converting to PDF and applying a Bates label.

## Problem

Clients share image files (jpg, png, meic, tif) that are responsive to requests for production or which must be disclosed prior to trial. Further complicating matters, the image files can contain images of any size from huge to quite small. Litigtion support staff must then resize the images, convert them to PDF files, and then apply Bates numbers. This is a tedious and time-consuming process that not only consumes scarce litigation support resources but also imposes high cost to the client.

## Solution

**photofixer** traverses a source folder, replicates the folder structure to a destination folder, and then resizes, converts, and stamps each image file before placing it in the corresponding replicated folder. The result is a duplicated folder structure containing the "fixed" photos and a source folder that is untouched.

## Author

Thomas J. Daley is a Texas Family Law litigation attorney board certified in family law by the Texas Board of Legal Specialization. He practices primarily in Collin, Dallas, Denton, Rockwall, and Tarrant counties in Texas but appears pro hac vice in cases throughout the United States.
