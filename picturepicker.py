import numpy as np
import sys
import os
import argparse

#for moving files (the images)
import shutil

import threading
import time

import tkinter as tk
from PIL import Image, ImageTk
from PIL import UnidentifiedImageError
from tkinter.ttk import Frame, Button, Style

def makeFileList(mypath, extension = None):
	"""
	Makes list of files with certain file extension

	Input: mypath (str), extension (str): for example .fits

	Returns: str array (location of files)
	"""
	import glob

	if extension is None:
		objectfiles = glob.glob(mypath + '*')
	else:
		objectfiles = glob.glob(mypath + '*' + extension)

	objectfiles = np.sort(objectfiles)

	return objectfiles

def checkpathsyntax(path):
	"""
	Check whether a path ends with a forward slash
	"""
	if path[-1] is not '/':
		path += '/'

	return path

def checkFolders(folders):
	"""
	Check whether folders are present and creates them if necessary
	"""
	for folder in folders:
		if not os.path.exists(folder):
			print(f'Directory {folder} does not exist; creating it now...')
			os.makedirs(folder)

def get_file_extension(filename):
	return filename[::-1].split('.', 1)[0][::-1]

def filterFileExtensions(fname_list, allowed_extensions):
	"""
	Filter a list of filenames to only include:
		.bmp
		.jpg
		.JPG
		.jpeg
		.gif
		.png
		.CR2 (RAW)
	"""

	filtered_fnames = []

	not_allowed_counter = 0

	for fname in fname_list:
		#extract the file extension without the dot
		extension = get_file_extension(fname)#fname[::-1].split('.', 1)[0][::-1]

		if extension in allowed_extensions:
			filtered_fnames.append(fname)
		else:
			not_allowed_counter += 1

	print(f'{not_allowed_counter} files not selected due to incompatible file extension.')

	return filtered_fnames


class ImageWindow():
	"""
	Tkinter image display and update code based on:
	https://raspberrypi.stackexchange.com/questions/18261/how-do-i-display-an-image-file-png-in-a-simple-window
	"""
	def __init__(self, images_fnames, moveto_path):
		#### fixed parameters
		#set the frame size (can be adjusted later)
		self.w = 960
		self.h = 1080

		# position coordinates of root 'upper left corner'
		x = 0
		y = 0

		self.image_not_found_path = '/home/jelle/Documents/Python/PicturePicker/image-not-found.png'

		#set up the frame
		self.root = tk.Tk()
		self.root.title('My Pictures')

		# make the root window the alotted size
		self.root.geometry("%dx%d+%d+%d" % (self.w, self.h, x, y))

		#obtain filenames and move path
		self.images_fnames = images_fnames
		self.moveto_path = moveto_path

		self.image1 = self.loadImage(images_fnames[0])

		self.image2 = ImageTk.PhotoImage(Image.open(images_fnames[1]))

		# make the panel for displaying the image
		# root has no image argument, so use a label as a panel
		self.panel1 = tk.Label(self.root)
		self.panel1.pack(side = tk.TOP, fill = tk.BOTH, expand = tk.YES)

		#set the iterator by asking at what image you want to start. Useful when
		#the program crashes at a high image count and you need to restart sorting
		startpoint_answer = input(f'There are {len(self.images_fnames) + 1} images to be sorted. Where do you want to start (starting from 1)? ')

		try:
			self.image_iterator = int(startpoint_answer) - 1
		except ValueError:
			sys.exit('Aborting: please give an integer input.')

		print(self.image_iterator)


		#count the number of images moved
		self.n_images_moved = 0
		#also note which images have already been moved
		self.moved_images = np.zeros(len(self.images_fnames))

		self.rotate = 'h'

		#image buffer list
		self.img_buffer = []
		self.img_buffer_fnames = []
		#the desired buffer length
		self.img_buffer_target_length = 10

		#parameter to indicate stopping loading the image buffer
		self.stop_buffer_loading = False

		#start the image buffer loading thread
		thread = threading.Thread(target = self.fillImageBuffer, args = ())
		thread.daemon = True
		thread.start()


		self.root.after(1, self.nextImage)
		self.root.mainloop()

	def loadImage(self, fname):
		"""
		Load a new image and put it in the frame
		"""
		# load the image
		try:
			img = Image.open(fname)
		except UnidentifiedImageError:
			print('Image loading failed')
			img = Image.open(self.image_not_found_path)
		#determine size
		imgwidth, imgheight = img.size
		#determine resize ratio
		ratio = min(self.w/imgwidth, self.h/imgheight)
		#resize it
		try:
			img = img.resize((int(imgwidth * ratio), int(imgheight * ratio)))
		except ValueError:
			print('Error encountered: box cannot exceed original size')

		return img

	def fillImageBuffer(self):
		"""
		Fill an image buffer and show the first image from the buffer
		"""

		while not self.stop_buffer_loading:
			for i in range(self.img_buffer_target_length - len(self.img_buffer)):
				it = self.image_iterator + len(self.img_buffer)
				if it <= len(self.images_fnames) - 1:
					fname = self.images_fnames[it]
					self.img_buffer.append(self.loadImage(fname))
					self.img_buffer_fnames.append(fname)
				else:
					self.stop_buffer_loading = True

	def prependBuffer(self, fname):
		"""
		Prepend an image and filename to the buffers
		"""
		self.img_buffer.insert(0, self.loadImage(fname))
		self.img_buffer_fnames.insert(0, fname)

	def getImage(self, rotate = None):
		"""
		Get an image from the image buffer
		"""

		while len(self.img_buffer) == 0 and not self.stop_buffer_loading:
			time.sleep(0.05)

		img = self.img_buffer[0]

		if rotate == 'l':
			img = img.rotate(90)
		elif rotate == 'r':
			img = img.rotate(-90)

		#check if the image is in a raw format. If so, convert to RGB
		imgextension = get_file_extension(self.img_buffer_fnames[0])#[::-1].split('.')[0][::-1]

		if imgextension in raw_formats:
			img = img.convert('RGB')

		return ImageTk.PhotoImage(img)

	def popBuffer(self):
		"""
		Remove the first item from the image buffer
		"""
		del self.img_buffer[0]
		del self.img_buffer_fnames[0]

	def nextImage(self):
		"""
		Put in the next image and ask whether it should be moved
		"""

		#update the width and height of the window if it is changed from the default
		#this allows the user to change the window shape and have the images
		#adjust after an update
		if self.root.winfo_height() is not 1 and self.root.winfo_width() is not 1:
			self.w = self.root.winfo_width()
			self.h = self.root.winfo_height()

		#load image
		image = self.getImage(rotate = self.rotate)
		# self.rotate = None

		#display image
		self.panel1.configure(image = image)
		self.display = image

		display_fname = self.img_buffer_fnames[0][::-1].split('/', 1)[0][::-1]

		#ask for input
		move_answer = input(f'{display_fname} [{self.image_iterator+1}/{len(self.images_fnames) + 1}/{self.n_images_moved}] Move the image? (y/n/exit) ')

		# print(f'[{self.image_iterator+1}/{len(self.images_fnames) + 1}] Move the image? (y/n/exit) ', end = '')
		# move_answer = sys.stdin.read(1)

		#move file if desired
		if move_answer.lower() == 'y':
			shutil.move(self.img_buffer_fnames[0], self.moveto_path)
			self.n_images_moved += 1
			self.moved_images[self.image_iterator] = 1

			self.image_iterator += 1

			#remove first from buffer
			self.popBuffer()
		elif move_answer.lower() == 'exit':
			sys.exit('Exiting...')
		elif move_answer == '\x1b[D':
			#press the left arrow

			#move one back if that image wasn't moved already
			if not self.moved_images[self.image_iterator - 1]:
				self.image_iterator -= 1
				#prepend this filename to the image buffer list
				self.prependBuffer(self.images_fnames[self.image_iterator])
			else:
				print('Image already moved.')
		elif move_answer.lower() in ['l', 'r', 'h']:
			#rotate image (or set rotation back to zero)
			self.rotate = move_answer.lower()
		else:
			#press the right arrow, input 'n' or no input (is a quick way forward)
			self.image_iterator += 1

			#remove first from buffer
			self.popBuffer()
		if self.image_iterator > len(self.images_fnames) - 1:
			self.stop_buffer_loading = True
			sys.exit('Final image reached, ending program...')

		#loop
		self.root.after(1, self.nextImage)

### allowed file extensions and RAW image formats
raw_formats = [
	'CR2',
	'TIF',
	'tif'
	]

allowed_extensions = [
	'bmp',
	'jpg',
	'JPG',
	'jpeg',
	'gif',
	'png'
	]
allowed_extensions.extend(raw_formats)

def main(devmode):
	"""
	This script allows one to easily sort images manually. The path of a folder
	containing a list of images is given, as well as a folder path where selected
	images are moved to. The images which were not selected, remain in the original
	folder and can be moved later manually.
	"""
	if not devmode:
		#obtain file path
		images_path = input('Please insert path of folder containing images to be organized:\n')

		#obtain path of folder where good images should be moved to
		moveto_path = input('Please insert path of folder where selected images should be moved to:\n')
	else:
		images_path = './testimages/'
		moveto_path = './testmoveto/'

	#make sure the paths end with a forward slash
	images_path = checkpathsyntax(images_path)
	moveto_path = checkpathsyntax(moveto_path)

	#check if the moveto path actually exists and if not, make it
	checkFolders([moveto_path])

	#obtain the filenames of the images.
	images_fnames = makeFileList(images_path)

	#filter the file extensions
	images_fnames = filterFileExtensions(images_fnames, allowed_extensions)

	#open the image window
	img_window = ImageWindow(images_fnames, moveto_path)

parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('--devmode', help = 'Do not ask for file paths but use default values. Used for quick code testing.', default = 'false')
args = parser.parse_args()

main(args.devmode.lower() == 'true')
