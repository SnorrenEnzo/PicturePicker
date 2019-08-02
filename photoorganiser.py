
from PIL import Image




def main(devmode):
	"""
	This script allows one to easily sort images manually. The path of a folder
	containing a list of images is given, as well as a folder path where selected
	images are moved to. The images which were not selected, remain in the original
	folder and can be moved later manually.
	"""
	if not devmode:
		#obtain file path
		imagepath = input('Please: insert path of folder containing images to be organized:\n')

		#obtain path of folder where good images should be moved to
	else:
		imagepath = './testimages/'

	print(imagepath)

#this parameter causes user input to be ignored for quicker code testing
devmode = True

main(devmode)
