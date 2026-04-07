
import os
import sys
import time
from datetime import datetime

import ctypes
import ctypes.wintypes


# Constants for Windows API
HWND_TOPMOST = -1
SWP_NOMOVE = 0x0002
SWP_NOSIZE = 0x0001
SWP_SHOWWINDOW = 0x0040

# cmd window size
k_windowSize_width=512
k_windowSize_height=128


def set_cmd_on_top():
	# Get the handle for the current console window
	hwnd = ctypes.windll.kernel32.GetConsoleWindow()
	
	if hwnd:
		# Set window position to topmost
		# Arguments: (hWnd, hWndInsertAfter, X, Y, cx, cy, uFlags)
		ctypes.windll.user32.SetWindowPos(
			hwnd, 
			HWND_TOPMOST, 
			0,
			0,
			k_windowSize_width,
			k_windowSize_height,
			SWP_NOMOVE | SWP_SHOWWINDOW
		)
		#print("Console window is now on top.")
		pass
	else:
		#print("Could not find console window handle.")
		pass
	pass


def set_console_size(cols,lines):
	return
	# -11 is the constant for STDOUT
	kernel32 = ctypes.windll.kernel32
	hdl = kernel32.GetStdHandle(-11)
	
	# Define the rectangle (Left, Top, Right, Bottom)
	# Right and Bottom are the desired dimensions minus 1
	rect = ctypes.wintypes.SMALL_RECT(0, 0, cols - 1, lines - 1)
	
	# Set the window size
	kernel32.SetConsoleWindowInfo(hdl, True, ctypes.byref(rect))
	pass


def getTimeText():
	return datetime.now().isoformat()


def loop_showTime():
	os.system('')
	try:
		print('')
		while True:
			print('\r \033[1;37m',getTimeText(),end=' '*4)
			time.sleep(0.5)
			pass
	except:
		print('\033[0m',end='')


def main(argv):
	set_console_size(
		k_windowSize_width,
		k_windowSize_height,
	)
	set_cmd_on_top()
	loop_showTime()
	pass


if __name__ == "__main__":
	main(sys.argv)

