#!/usr/bin/env python3
"""
web_rdp.py - A dependency-free Python 3 "web RDP" for Windows.

Features
--------
* Serves a browser page that mirrors the live GUI desktop of the machine
  running this script (captured through the Windows GDI screen).
* Real-time image streaming using the classic MJPEG technique
  (multipart/x-mixed-replace with PNG frames). No external libraries and
  no WebSocket code are required - only the standard library + ctypes.
* Forward mouse and keyboard events from the browser back to the desktop
  using user32.SendInput, so the real OS input receives the events.

Usage
-----
	python web_rdp.py [port] [ip]

	port	bind port		 (default 54321)
	ip	  bind address	  (default 0.0.0.0)

Only Python 3 standard library modules are used, plus the native
user32 / gdi32 DLLs accessed through ctypes.
"""

import sys
import struct
import zlib
import time
import threading
import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import ctypes
from ctypes import c_void_p, c_ulong, c_long, c_int, c_ushort, c_uint, c_byte, byref

# --------------------------------------------------------------------------
#  Windows API declarations (via ctypes)
# --------------------------------------------------------------------------
user32 = ctypes.windll.user32
gdi32 = ctypes.windll.gdi32

SRCCOPY = 0x00CC0020
CAPTUREBLT = 0x40000000
DIB_RGB_COLORS = 0

# System metrics indices
SM_XVIRTUALSCREEN = 76
SM_YVIRTUALSCREEN = 77
SM_CXVIRTUALSCREEN = 78
SM_CYVIRTUALSCREEN = 79

# SendInput event flags
MOUSEEVENTF_MOVE = 0x0001
MOUSEEVENTF_ABSOLUTE = 0x8000
MOUSEEVENTF_DOWN = 0x0002
MOUSEEVENTF_UP = 0x0004
MOUSEEVENTF_MIDDLEBUTTON = 0x0020
MOUSEEVENTF_RIGHTBUTTON = 0x0008
MOUSEEVENTF_WHEEL = 0x0080
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_SCANCODE = 0x0008


class BITMAPINFOHEADER(ctypes.Structure):
	_fields_ = [
		("biSize", c_ulong),
		("biWidth", c_long),
		("biHeight", c_long),
		("biPlanes", c_ushort),
		("biBitCount", c_ushort),
		("biCompression", c_ulong),
		("biSizeImage", c_ulong),
		("biXPelsPerMeter", c_long),
		("biYPelsPerMeter", c_long),
		("biClrUsed", c_ulong),
		("biClrImportant", c_ulong),
	]


class BITMAPINFO(ctypes.Structure):
	_fields_ = [("bmih", BITMAPINFOHEADER), ("rgbquad", c_byte * 12)]


class _MOUSEINPUT(ctypes.Structure):
	_fields_ = [
		("dx", c_long),
		("dy", c_long),
		("mouseData", c_ulong),
		("dwFlags", c_uint),
		("dwExtraInfo", c_void_p),
	]


class _KEYBDINPUT(ctypes.Structure):
	_fields_ = [
		("wVk", c_ushort),
		("wScan", c_ushort),
		("dwFlags", c_uint),
		("dwExtraInfo", c_void_p),
	]


class _INPUT(ctypes.Structure):
	_fields_ = [
		("type", c_ulong),
		("mi", _MOUSEINPUT),
		("ki", _KEYBDINPUT),
	]


def _decl_gdi(name, restype, argtypes):
	fn = getattr(gdi32, name)
	fn.restype = restype
	fn.argtypes = argtypes
	return fn


def _decl_user32(name, restype, argtypes):
	fn = getattr(user32, name)
	fn.restype = restype
	fn.argtypes = argtypes
	return fn


_CreateCompatibleDC = _decl_gdi("CreateCompatibleDC", c_void_p, [c_void_p])
_CreateCompatibleBitmap = _decl_gdi(
	"CreateCompatibleBitmap", c_void_p, [c_void_p, c_int, c_int]
)
_SelectObject = _decl_gdi("SelectObject", c_void_p, [c_void_p, c_void_p])
_BitBlt = _decl_gdi(
	"BitBlt", c_int, [c_void_p, c_int, c_int, c_int, c_int, c_void_p, c_int, c_int, c_uint]
)
_CreateDIBSection = _decl_gdi(
	"CreateDIBSection",
	c_void_p,
	[c_void_p, c_void_p, c_uint, c_void_p, c_void_p, c_uint],
)
_DeleteObject = _decl_gdi("DeleteObject", c_int, [c_void_p])
_ReleaseDC = _decl_user32("ReleaseDC", c_int, [c_void_p, c_void_p])

_SendInput = _decl_user32(
	"SendInput", c_uint, [c_uint, ctypes.POINTER(_INPUT), c_int]
)
_GetForegroundWindow = _decl_user32("GetForegroundWindow", c_void_p, [])
_PostMessageW = _decl_user32("PostMessageW", c_int, [c_void_p, c_uint, c_void_p, c_void_p])

WM_MOUSEWHEEL = 0x020A
WM_KEYDOWN = 0x0100
WM_KEYUP = 0x0101

try:
	# 適用於 Windows 10 (1703) 或更新版本（傳入 -4 代表 PerMonitorV2）
	ctypes.windll.user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))
except AttributeError:
	try:
		# 備用方案：適用於較舊版本的 Windows 8.1 / 10
		ctypes.windll.shcore.SetProcessDpiAwareness(2) # 2 代表 PROCESS_PER_MONITOR_DPI_AWARE
	except AttributeError:
		# 最終備用方案：適用於 Windows 7
		ctypes.windll.user32.SetProcessDPIAware()

# --------------------------------------------------------------------------
#  Screen capture
# --------------------------------------------------------------------------
test_output_ed=False
def _png_from_rgb(rgb: bytes, width: int, height: int) -> bytes:
	"""Encode an unpadded top-down RGB24 buffer as a PNG blob."""
	global test_output_ed

	def chunk(typ: bytes, data: bytes) -> bytes:
		body = typ + data
		return struct.pack(">I", len(data)) + body + struct.pack(
			">I", zlib.crc32(body) & 0xFFFFFFFF
		)

	stride = width * 3
	raw = bytearray()
	append = raw.append
	for y in range(height):
		append(0)  # filter type 0 (None)
		start = y * stride
		raw += rgb[start:start + stride]
	idat = zlib.compress(bytes(raw), 6)

	sig = b"\x89PNG\r\n\x1a\n"
	ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
	rtv=sig + chunk(b"IHDR", ihdr) + chunk(b"IDAT", idat) + chunk(b"IEND", b"")
	'''{
	if not test_output_ed:
		test_output_ed=True
		with open('.dbg-cap-out.png','wb') as f: f.write(rtv)
	}'''
	return rtv
def _png_from_idat(idat: bytes, width: int, height: int) -> bytes:
	"""Encode an unpadded top-down RGB24 buffer as a PNG blob."""
	global test_output_ed

	def chunk(typ: bytes, data: bytes) -> bytes:
		body = typ + data
		return struct.pack(">I", len(data)) + body + struct.pack(
			">I", zlib.crc32(body) & 0xFFFFFFFF
		)

	idat = zlib.compress(bytes(idat), 1)

	sig = b"\x89PNG\r\n\x1a\n"
	ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
	rtv=sig + chunk(b"IHDR", ihdr) + chunk(b"IDAT", idat) + chunk(b"IEND", b"")
	'''{
	if not test_output_ed:
		test_output_ed=True
		with open('.dbg-cap-out.png','wb') as f: f.write(rtv)
	}'''
	return rtv


class ScreenCapture:
	"""Captures the full virtual screen as an RGB24 buffer using GDI."""
	
	def updateGeo(self,w,h,forceUpdate=False):
		if not (forceUpdate or w!=self.width or h!=self.height): return
		self.width=w
		self.height=h
		
		self.stride = ((self.width * 24 + 31) // 32) * 4
		self.row_bytes = self.width * 3
		self._size = self.stride * self.height
		
		self.rgb_buffer_row=ctypes.create_string_buffer(self.row_bytes) # can be gc by python
		self.rgb_buffer_cache_geo={
			"stride":-1,
		}
		self.rgb_buffer_cache_cmp={}
		self.rgb_buffer_cache_val={}
		
		#self._hbm = _CreateCompatibleBitmap(self._hdc, self.width, self.height)
		self._buf = ctypes.create_string_buffer(self._size) # can be gc by python

		# Prepare a top-down, 24bpp DIB header.
		self._bmi.bmih.biWidth = self.width
		self._bmi.bmih.biHeight = -self.height  # negative => top-down
		
		# Create the DIB section once; each frame is BitBlt'd into it.
		if self._hbm: gdi32.DeleteObject(self._hbm)
		self._hbm = _CreateDIBSection(
			self._hdc, byref(self._bmi), DIB_RGB_COLORS,
			byref(self._bits), None, DIB_RGB_COLORS,
		)
		if not self._hbm:
			raise RuntimeError("CreateDIBSection failed")
		_SelectObject(self._hmem, self._hbm)
		
		pass
	
	def __init__(self):
		self.width = user32.GetSystemMetrics(SM_CXVIRTUALSCREEN)
		self.height = user32.GetSystemMetrics(SM_CYVIRTUALSCREEN)
		self.vxo = user32.GetSystemMetrics(SM_XVIRTUALSCREEN)
		self.vyo = user32.GetSystemMetrics(SM_YVIRTUALSCREEN)
		
		#self.rgb_buffer=None
		
		self._hdc = user32.GetDC(0)  # HWND_DESKTOP DC covers the whole screen
		self._hmem = _CreateCompatibleDC(self._hdc)
		self._prev = None
		self._lock = threading.Lock()
		
		# Prepare a top-down, 24bpp DIB header.
		self._bmi = BITMAPINFO()
		self._bmi.bmih.biSize = 40
		self._bmi.bmih.biPlanes = 1
		self._bmi.bmih.biBitCount = 24
		self._bmi.bmih.biCompression = BI_RGB
		
		# Create the DIB section once; each frame is BitBlt'd into it.
		self._bits = ctypes.c_void_p()
		self._hbm = None # init member name
		
		self.updateGeo(self.width,self.height,True)
		
		pass

	'''{
	def capture(self):
		"""Return (rgb_bytes, changed) where changed reflects screen update."""
		with self._lock:
			_BitBlt(
				self._hmem, 0, 0, self.width, self.height,
				self._hdc, 0, 0, SRCCOPY | CAPTUREBLT,
			)

			ctypes.memmove(ctypes.addressof(self._buf), self._bits.value, self._size)

			# Unpad rows that are aligned to 4 bytes (stride may exceed width*3).
			if not self.rgb_buffer: self.rgb_buffer=ctypes.create_string_buffer(self.row_bytes * self.height)
			rgb=self.rgb_buffer
			dst=0
			for src in range(0, self._size, self.stride):
				ctypes.memmove(
					ctypes.addressof(rgb) + dst,
					#self._bits.value+src,
					ctypes.addressof(self._buf) + src,
					self.row_bytes,
				)
				dst += self.row_bytes

			#for i in range(0,len(data),3): rgb[i],rgb[i+2]=rgb[i+2],rgb[i]
			rgb[0::3],rgb[2::3]=rgb[2::3],rgb[0::3]
			data = bytes(rgb)
			#changed = data != self._prev
			changed=True
			self._prev = data
			return data, changed
	}'''
	def capture_png_idat(self):
		with self._lock:
			self.updateGeo(
				user32.GetSystemMetrics(SM_CXVIRTUALSCREEN),
				user32.GetSystemMetrics(SM_CYVIRTUALSCREEN),
			)
			_BitBlt(
				self._hmem, 0, 0, self.width, self.height,
				self._hdc, 0, 0, SRCCOPY | CAPTUREBLT,
			)
			
			if not self.rgb_buffer_row: self.rgb_buffer_row=ctypes.create_string_buffer(self.row_bytes)
			rgb_row=self.rgb_buffer_row
			
			# cache
			if True:
				c=self.rgb_buffer_cache_geo
				if c["stride"]!=self.stride:
					c["stride"]=self.stride
					self.rgb_buffer_cache_cmp.clear()
					self.rgb_buffer_cache_val.clear()
			
			buf=bytearray()
			#ms=0
			#mm=0
			#mc=0
			#L=0
			#cacheHitCnt=0
			#t0=time.time()
			for src in range(0, self._size, self.stride):
				buf.append(0)
				#mm0=time.time()
				ctypes.memmove(
					ctypes.addressof(rgb_row),
					self._bits.value+src, #ctypes.addressof(self._buf) + src,
					self.row_bytes,
				)
				#mm+=time.time()-mm0
				#mc0=time.time()
				row=bytearray(rgb_row)
				if True:
					if not (src in self.rgb_buffer_cache_cmp) or self.rgb_buffer_cache_cmp[src]!=row:
						self.rgb_buffer_cache_cmp[src]=row
						tmp=bytearray(row)
						#L+=len(tmp)
						#ms0=time.time()
						tmp[0::3],tmp[2::3]=tmp[2::3],tmp[0::3]
						#ms+=time.time()-ms0
						self.rgb_buffer_cache_val[src]=tmp
					else:
						#cacheHitCnt+=1
						pass
					#mc+=time.time()-mc0
					row=self.rgb_buffer_cache_val[src]
				else:
					row[0::3],row[2::3]=row[2::3],row[0::3]
				buf+=row
			#print('copy time',time.time()-t0)
			#print('memswap time',ms)
			#print('memmove time',mm)
			#print('memcmp time',mc)
			#print('L',L)
			#print('cacheHitCnt',cacheHitCnt)
			return buf
		pass
		


# BI_RGB compression type (uncompressed RGB).
BI_RGB = 0

# --------------------------------------------------------------------------
#  Input forwarding
# --------------------------------------------------------------------------

# Common key name -> virtual key code
_VK = {
	"enter": 0x0D, "return": 0x0D, "tab": 0x09, "backspace": 0x08,
	"escape": 0x1B, "esc": 0x1B, "space": 0x20, " ": 0x20, "delete": 0x2E, "del": 0x2E,
	"up": 0x26, "down": 0x28, "left": 0x25, "right": 0x27,
	"arrowup": 0x26, "arrowdown": 0x28, "arrowleft": 0x25, "arrowright": 0x27,
	"home": 0x24, "end": 0x23, "pageup": 0x21, "pagedown": 0x22,
	"capslock": 0x14, "shift": 0x10, "ctrl": 0x11, "control": 0x11, "alt": 0x12,
	"printscreen": 0x2C, "scrolllock": 0x91,
}


def _vk_for_key(ev):
	"""Resolve a browser key description to a VK code."""
	name = ev.get("key", "").lower()
	if not name:
		return None
	if name in _VK:
		return _VK[name]
	if len(name) == 1:
		# letter / digit / symbol via single char
		return ord(name.upper())
	return None


def _map_coord(px, size):
	"""Map a pixel coordinate onto SendInput's normalized [-32768, 32767]."""
	if size <= 0:
		return 0
	return int((px - 0) * 65535 // size)


def _send_mouse(dx, dy, flags, data=0):
	user32.mouse_event(
		flags,
		dx,dy,
		data,
		0,
	)
	return


def _send_key(vk, keyup=True):
	user32.keybd_event(
		vk,
		0,
		KEYEVENTF_KEYUP if keyup else 0,
		0,
	)


def handle_input(payload):
	"""Apply an incoming JSON input payload to the real desktop."""
	print('handle_input',payload,time.time())
	etype = payload.get("type")
	width = CAP.width
	height = CAP.height

	if etype == "mousemove":
		x = max(0, min(payload.get("x", 0), width))
		y = max(0, min(payload.get("y", 0), height))
		_send_mouse(_map_coord(x, width), _map_coord(y, height), MOUSEEVENTF_MOVE | MOUSEEVENTF_ABSOLUTE)

	elif etype in ("mousedown", "mouseup"):
		x = max(0, min(payload.get("x", 0), width))
		y = max(0, min(payload.get("y", 0), height))
		flags = MOUSEEVENTF_ABSOLUTE | (MOUSEEVENTF_DOWN if etype[5] == "d" else MOUSEEVENTF_UP)
		button = payload.get("button", 0)
		if button == 1:
			flags |= MOUSEEVENTF_MIDDLEBUTTON
		elif button == 2:
			flags |= MOUSEEVENTF_RIGHTBUTTON
		_send_mouse(_map_coord(x, width), _map_coord(y, height), flags)

	elif etype == "wheel":
		dy = int(payload.get("deltaY", 0))
		x = max(0, min(payload.get("x", 0), width))
		y = max(0, min(payload.get("y", 0), height))
		_send_mouse(_map_coord(x, width), _map_coord(y, height), MOUSEEVENTF_WHEEL | MOUSEEVENTF_ABSOLUTE, dy * 120)

	elif etype in ("keydown", "keyup"):
		vk = _vk_for_key(payload)
		if vk is not None:
			_send_key(vk, keyup=(etype[3] != "d"))
	print('errcode',ctypes.get_last_error())
	print('handle_input end',payload,time.time())
	return True


# --------------------------------------------------------------------------
#  HTTP handler
# --------------------------------------------------------------------------
STREAM_BOUNDARY = b"stream-sep"


class Handler(BaseHTTPRequestHandler):
	protocol_version = "HTTP/1.1"
	server_version = "web_rdp/1.0"
	
	def is_from_white_list_ip(self):
		ip=self.client_address[0]
		print('ip',ip)
		rtv=False
		try:
			if ip.count('.')==3:
				cmp=tuple([x.rjust(3,' ') for x in ip.split('.')])
				print('cmp',cmp)
				if   cmp>=('127','  0','  0','  0') and cmp<=('127','255','255','255'): rtv|=True
				elif cmp>=(' 10','  0','  0','  0') and cmp<=(' 10','255','255','255'): rtv|=True
				elif cmp>=('192','168','  0','  0') and cmp<=('192','168','255','255'): rtv|=True
				elif cmp>=('172',' 16','  0','  0') and cmp<=('172',' 31','255','255'): rtv|=True
		except:
			pass
		return rtv

	# -- root page ----------------------------------------------------------
	def do_GET(self):
		print("GET",self.path,)
		if not self.is_from_white_list_ip():
			self.send_error(404, "Not Found")
			self.close_connection=True
			return
		cc=True
		if self.path in ("/", "/index.html"):
			self._send_html(PAGE_HTML)
		elif self.path == "/stream":
			self._serve_stream()
			cc=False
		elif self.path == "/meta":
			self._send_json({
				"width":CAP.width,
				"height":CAP.height,
			})
		else:
			self.send_error(404, "Not Found")
		if cc: self.close_connection=True

	def do_POST(self):
		print("POST",self.path,)
		#return self.send_error(404, "Not Found")
		if not self.is_from_white_list_ip():
			self.send_error(404, "Not Found")
			self.close_connection=True
			return
		cc=True
		if self.path == "/input":
			try:
				length = int(self.headers.get("Content-Length", 0))
				raw = self.rfile.read(length) if length else b""
				payload = json.loads(raw.decode("utf-8")) if raw else {}
				handle_input(payload)
				self.send_response(200)
				self.send_header("Content-Type", "application/json")
				self.end_headers()
				self.wfile.write(b'{"ok":true}')
			except Exception as exc:  # noqa: BLE001
				self.send_error(400, str(exc))
		else:
			self.send_error(404, "Not Found")
		if cc: self.close_connection=True

	# -- helpers ------------------------------------------------------------
	def _send_json(self, obj):
		body = json.dumps(obj).encode("utf-8")
		self.send_response(200)
		self.send_header("Content-Type", "application/json")
		self.send_header("Content-Length", str(len(body)))
		self.end_headers()
		self.wfile.write(body)

	def _send_html(self, html):
		body = html.encode("utf-8")
		self.send_response(200)
		self.send_header("Content-Type", "text/html; charset=utf-8")
		self.send_header("Content-Length", str(len(body)))
		self.send_header("Cache-Control", "no-store")
		self.end_headers()
		self.wfile.write(body)

	def _serve_stream(self):
		"""Stream PNG frames as multipart/x-mixed-replace (MJPEG)."""
		print('_serve_stream')
		self.send_response(200)
		self.send_header(
			"Content-Type",
			"multipart/x-mixed-replace; boundary=" + STREAM_BOUNDARY.decode(),
		)
		#self.send_header("Content-Encoding","deflate")
		self.send_header("Cache-Control", "no-cache, no-store")
		self.end_headers()

		wfile = self.wfile
		frame = None
		try:
			u0=0
			t0=0
			while not self.close_connection:
				'''if u0:
					u1=time.time()
					print('update time',u1-u0)
					u0=u1
				else: u0=time.time()'''
				#t0=time.time()
				if False:
					data, changed = CAP.capture()
					#print('capture time taken',time.time()-t0)
					if not changed:
						# Re-use previous frame so the browser keeps the last image.
						if frame:
							wfile.write(frame)
							wfile.flush()
							#time.sleep(0.03)
							continue
					#t0=time.time()
					png = _png_from_rgb(data, CAP.width, CAP.height)
				else:
					idat=CAP.capture_png_idat()
					#print('capture time taken',time.time()-t0)
					#t0=time.time()
					png=_png_from_idat(idat, CAP.width, CAP.height)
				#print('rgb->png time taken',time.time()-t0)
				#t0=time.time()
				frame = bytearray()
				frame.extend(b"--")
				frame.extend(STREAM_BOUNDARY)
				frame.extend(b"\r\n")
				frame.extend(b"Content-Type: image/png\r\n")
				#frame.extend(b"Content-Length: "+str(len(png)).encode()+b"\r\n")
				frame.extend(b"\r\n")
				#print(type(png))
				#print(len(png))
				frame.extend(png)
				frame.extend(b"\r\n")
				wfile.write(frame)
				wfile.flush()
				#print('flush time taken',time.time()-t0)
		except (BrokenPipeError, ConnectionResetError):
			print('BrokenPipeError || ConnectionResetError')
			pass
		except Exception as exc:  # noqa: BLE001
			print('other exceptions')
			sys.stderr.write("stream error: %r\n" % (exc,))
			pass

	# silence the default noisy logging (optional)
	def log_message(self, fmt, *args):  # noqa: A003
		sys.stderr.write("[web_rdp] %s\n" % (fmt % args,))


PAGE_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Web RDP - Desktop</title>
<style>
html, body {
	margin: 0;
	padding: 0;
	height: 100%;
	background: #111;
	overflow: hidden;
	font-family: system-ui, sans-serif;
}
#wrap {
	position: relative;
	width: 100%;
	height: 100%;
	display:flex;
	//align-items:center;
	//justify-content:center;
	overflow:scroll;
}
img#screen {
	//max-width: 100%;
	//max-height: 100%;
	cursor: crosshair;
	user-select: none;
	-webkit-user-drag: none;
}
#hint {
	position: absolute;
	top: 8px;
	left: 10px;
	color: #9fd;
	font-size: 12px;
	opacity: .7;
	pointer-events:none;
}
</style>
</head>
<body>
<div id="wrap">
	<div id="hint">Web RDP &middot; drag/scroll/typewhere</div>
	<div><img id="screen" alt="desktop"></div>
</div>
<script>
(function () {
	const img = document.getElementById('screen');
	const src = new (window.ReadableStream || window.getStream)();
	// Point the img at the MJPEG stream endpoint.

	let metaLoaded=false,vW=1920,vH=1080; // updated below from a metadata call

const task_afterMetaLoaded=()=>{
	function send(ev){
		fetch('/input', {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify(ev),
		}).catch(function () {});
	}

	// Convert a page (img) coordinate into the captured virtual-screen coord.
	function toScreen(clientX, clientY) {
		const rect=img.getBoundingClientRect();
		console.log('clientX,clientY',clientX,clientY);
		const rx=(clientX-rect.left)/rect.width;
		const ry=(clientY-rect.top)/rect.height;
		return {
			x:Math.round(rx*vW),
			y:Math.round(ry*vH),
		};
	}

	img.addEventListener('mousedown', function (e) {
		e.preventDefault();
		const s=toScreen(e.clientX, e.clientY);
		send({
			type:'mousemove',
			x:s.x,
			y:s.y,
		});
		send({
			type:'mousedown',
			x:s.x,
			y:s.y,
			button:e.button,
		});
	});
	let s_last={
		x:0,
		y:0,
	};
	window.addEventListener('mouseup', function (e) {
		e.preventDefault();
		send({
			type:'mouseup',
			x:s_last.x,
			y:s_last.y,
			button:e.button,
		});
	});
	img.addEventListener('mousemove', function (e) {
		const s=toScreen(e.clientX,e.clientY);
		s_last=s;
		send({
			type:'mousemove',
			x:s.x,
			y:s.y,
		});
	});
	img.addEventListener('wheel', function (e) {
		e.preventDefault();
		const s=toScreen(e.clientX, e.clientY);
		send({
			type:'wheel',
			x:s.x,
			y:s.y,
			deltaY:Math.sign(e.deltaY),
		});
 	},{
		passive:false,
	});

	// Keyboard
	window.addEventListener('keydown', function (e) {
		if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
		e.preventDefault();
		console.log('keyd',e.key);
		send({
			type:'keydown',
			key:e.key,
		});
	},{
		passive:false,
	});
	window.addEventListener('keyup', function (e) {
		if(e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
		console.log('keyu',e.key);
		send({
			type:'keyup',
			key:e.key,
		});
	});
};

	fetch('/meta').then(function(r){ return r.json(); }).
	then(function(m){
		vW=m.width; vH=m.height;
		metaLoaded=true;
		console.log('m',m,);
		console.log('vW,vH',vW,vH,);
		img.width=vW;
		img.height=vH;
		img.src='/stream';
		task_afterMetaLoaded();
	}).
	catch(function(){});
})();
</script>
</body>
</html>
"""

# --------------------------------------------------------------------------
#  Main
# --------------------------------------------------------------------------
CAP = None


def main():
	global CAP

	parser = argparse.ArgumentParser(description="Python web RDP for Windows.")
	parser.add_argument("port", nargs="?", type=int, default=54321, help="bind port (default 54321)")
	parser.add_argument("ip", nargs="?", default="0.0.0.0", help="bind address (default 0.0.0.0)")
	args = parser.parse_args()

	try:
		CAP = ScreenCapture()
	except Exception as exc:  # noqa: BLE001
		sys.stderr.write("Failed to initialise screen capture: %r\n" % (exc,))
		sys.exit(1)

	sys.stderr.write(
		"Capturing virtual screen %dx%d\n" % (CAP.width, CAP.height)
	)

	server = ThreadingHTTPServer((args.ip, args.port), Handler)
	sys.stderr.write(
		"web_rdp listening on http://%s:%d/\n" % (
			args.ip if args.ip != "0.0.0.0" else "0.0.0.0", args.port
		)
	)
	sys.stderr.write("Press Ctrl+C to stop.\n")
	try:
		server.serve_forever()
	except KeyboardInterrupt:
		sys.stderr.write("\nshutting down...\n")
	finally:
		server.server_close()
		if CAP:
			with CAP._lock:
				gdi32.DeleteObject(CAP._hbm)
				gdi32.DeleteObject(CAP._hmem)
				user32.ReleaseDC(0, CAP._hdc)


if __name__ == "__main__":
	main()

