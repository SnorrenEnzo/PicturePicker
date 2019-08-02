import numpy as np
import sys
import argparse

#for moving files (the images)
import shutil

import tkinter as tk
from PIL import Image, ImageTk
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

class ImageWindow():
	"""
	Code based on: https://raspberrypi.stackexchange.com/questions/18261/how-do-i-display-an-image-file-png-in-a-simple-window
	"""
	def __init__(self, images_fnames, moveto_path):
		#### fixed parameters
		#fix the frame size
		self.w = 960
		self.h = 1080

		# position coordinates of root 'upper left corner'
		x = 0
		y = 0


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

		#iterator for the images
		self.image_iterator = 0

		self.root.after(1, self.nextImage)
		self.root.mainloop()

	def loadImage(self, fname):
		"""
		Load a new image and put it in the frame
		"""
		# load the image
		img = Image.open(fname)
		#determine size
		imgwidth, imgheight = img.size
		#determine resize ratio
		ratio = min(self.w/imgwidth, self.h/imgheight)
		#resize it
		img = img.resize((int(imgwidth * ratio), int(imgheight * ratio)))
		#covert it to a Tkinter image object
		return ImageTk.PhotoImage(img)

	def nextImage(self):
		"""
		Put in the next image and ask whether it should be moved
		"""
		#load image
		image = self.loadImage(self.images_fnames[self.image_iterator])

		#display image
		self.panel1.configure(image = image)
		self.display = image

		#ask for input
		move_answer = input(f'[{self.image_iterator+1}/{len(self.images_fnames) + 1}] Move the image? (y/n/exit)')

		#move if desired
		if move_answer.lower() == 'y':
			shutil.move(self.images_fnames[self.image_iterator], self.moveto_path)
		elif move_answer.lower() == 'exit':
			sys.exit('Exiting...')


		self.image_iterator += 1

		if self.image_iterator > len(self.images_fnames) - 1:
			sys.exit('Final image reached, ending program...')

		#loop
		self.root.after(1, self.nextImage)


	def update_image(self):
		if self.display == self.image1:
			self.panel1.configure(image = self.image2)
			self.display = self.image2
		else:
			self.panel1.configure(image = self.image1)
			self.display = self.image1
		self.root.after(3000, self.update_image)	   # Set to call again in 30 seconds


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

	#obtain the filenames of the images.
	images_fnames = makeFileList(images_path)

	#open the image window
	img_window = ImageWindow(images_fnames, moveto_path)

parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('--devmode', help = 'Do not ask for file paths but use default values. Used for quick code testing.', default = 'false')
args = parser.parse_args()

main(args.devmode.lower() == 'true')
