"""Minimal late-bound COM Automation (IDispatch) client built on ctypes.

Sublime Text's embedded Python ships without pywin32. This covers what the
plugin needs from Stata Automation: create an object from its ProgID and call
methods with string/number arguments. Windows only.
"""

import ctypes
from ctypes import POINTER, byref, c_long, c_uint, c_ulong, c_ushort, c_void_p, c_wchar_p

# Private library instances so argtypes set here never clash with other
# plugins sharing the same plugin_host (ctypes.windll caches functions).
_ole32 = ctypes.WinDLL("ole32")
_oleaut32 = ctypes.WinDLL("oleaut32")

COINIT_APARTMENTTHREADED = 0x2
CLSCTX_INPROC_SERVER = 0x1
CLSCTX_LOCAL_SERVER = 0x4
LOCALE_USER_DEFAULT = 0x0400
DISPATCH_METHOD = 0x1
DISPATCH_PROPERTYGET = 0x2

DISP_E_EXCEPTION = 0x80020009
RPC_E_CHANGED_MODE = 0x80010106
RPC_E_CALL_REJECTED = 0x80010001
# The object is not registered: `StataXX.exe /Register` has not been run.
NOT_REGISTERED = frozenset((0x80040154, 0x800401F3))  # REGDB_E_CLASSNOTREG, CO_E_CLASSSTRING
# The server process has gone away, typically because Stata was closed.
DISCONNECTED = frozenset((
	0x80010108,  # RPC_E_DISCONNECTED
	0x800706BA,  # RPC_S_SERVER_UNAVAILABLE
	0x800706BE,  # RPC_S_CALL_FAILED
	0x80010105,  # RPC_E_SERVERFAULT
	0x800401FD,  # CO_E_OBJNOTCONNECTED
))

VT_EMPTY, VT_NULL, VT_I2, VT_I4, VT_R4, VT_R8 = 0, 1, 2, 3, 4, 5
VT_BSTR, VT_ERROR, VT_BOOL = 8, 10, 11
VT_I1, VT_UI1, VT_UI2, VT_UI4, VT_I8, VT_UI8, VT_INT, VT_UINT = 16, 17, 18, 19, 20, 21, 22, 23


class GUID(ctypes.Structure):
	_fields_ = [("Data1", c_ulong), ("Data2", c_ushort), ("Data3", c_ushort), ("Data4", ctypes.c_ubyte * 8)]


class _VariantValue(ctypes.Union):
	_fields_ = [
		("llVal", ctypes.c_longlong), ("lVal", c_long), ("iVal", ctypes.c_short),
		("cVal", ctypes.c_byte), ("bVal", ctypes.c_ubyte), ("boolVal", ctypes.c_short),
		("fltVal", ctypes.c_float), ("dblVal", ctypes.c_double), ("bstrVal", c_void_p),
		("_record", c_void_p * 2),  # largest member (BRECORD); fixes the union size
	]


class VARIANT(ctypes.Structure):
	_fields_ = [("vt", c_ushort), ("wReserved1", c_ushort), ("wReserved2", c_ushort),
		("wReserved3", c_ushort), ("value", _VariantValue)]


class DISPPARAMS(ctypes.Structure):
	_fields_ = [("rgvarg", POINTER(VARIANT)), ("rgdispidNamedArgs", POINTER(c_long)),
		("cArgs", c_uint), ("cNamedArgs", c_uint)]


class EXCEPINFO(ctypes.Structure):
	_fields_ = [("wCode", c_ushort), ("wReserved", c_ushort), ("bstrSource", c_void_p),
		("bstrDescription", c_void_p), ("bstrHelpFile", c_void_p), ("dwHelpContext", c_ulong),
		("pvReserved", c_void_p), ("pfnDeferredFillIn", c_void_p), ("scode", c_long)]


_ole32.CoInitializeEx.argtypes = [c_void_p, c_ulong]
_ole32.CoInitializeEx.restype = c_long
_ole32.CoUninitialize.argtypes = []
_ole32.CoUninitialize.restype = None
_ole32.CLSIDFromProgID.argtypes = [c_wchar_p, POINTER(GUID)]
_ole32.CLSIDFromProgID.restype = c_long
_ole32.CLSIDFromString.argtypes = [c_wchar_p, POINTER(GUID)]
_ole32.CLSIDFromString.restype = c_long
_ole32.CoCreateInstance.argtypes = [POINTER(GUID), c_void_p, c_ulong, POINTER(GUID), POINTER(c_void_p)]
_ole32.CoCreateInstance.restype = c_long
_oleaut32.SysAllocString.argtypes = [c_wchar_p]
_oleaut32.SysAllocString.restype = c_void_p
_oleaut32.SysFreeString.argtypes = [c_void_p]
_oleaut32.SysFreeString.restype = None
_oleaut32.SysStringLen.argtypes = [c_void_p]
_oleaut32.SysStringLen.restype = c_uint
_oleaut32.VariantClear.argtypes = [POINTER(VARIANT)]
_oleaut32.VariantClear.restype = c_long


class COMError(Exception):
	def __init__(self, hresult, message):
		self.hresult = hresult & 0xFFFFFFFF
		Exception.__init__(self, "%s (0x%08X)" % (message, self.hresult))


def _describe(hresult):
	signed = hresult & 0xFFFFFFFF
	if signed >= 0x80000000:
		signed -= 0x100000000
	return ctypes.FormatError(signed).strip()


def _check(hresult, what):
	if hresult < 0:
		raise COMError(hresult, "%s failed: %s" % (what, _describe(hresult)))
	return hresult


def _guid(text):
	guid = GUID()
	_check(_ole32.CLSIDFromString(text, byref(guid)), "CLSIDFromString")
	return guid


_IID_NULL = GUID()
_IID_IDispatch = _guid("{00020400-0000-0000-C000-000000000046}")


def initialize():
	"""Initialize COM (single-threaded apartment) on the calling thread.

	Returns True if the caller must balance this with uninitialize().
	"""
	hresult = _ole32.CoInitializeEx(None, COINIT_APARTMENTTHREADED)
	if hresult & 0xFFFFFFFF == RPC_E_CHANGED_MODE:
		return False  # already initialized in another mode; COM is usable
	_check(hresult, "CoInitializeEx")
	return True


def uninitialize():
	_ole32.CoUninitialize()


def is_registered(progid):
	return _ole32.CLSIDFromProgID(progid, byref(GUID())) >= 0


def _vtable_call(pointer, index, restype, argtypes, *args):
	vtable = ctypes.cast(c_void_p(pointer), POINTER(POINTER(c_void_p)))[0]
	function = ctypes.WINFUNCTYPE(restype, c_void_p, *argtypes)(vtable[index])
	return function(pointer, *args)


def _to_variant(value, variant):
	if isinstance(value, bool):
		variant.vt = VT_BOOL
		variant.value.boolVal = -1 if value else 0
	elif isinstance(value, int):
		variant.vt = VT_I4
		variant.value.lVal = value
	elif isinstance(value, float):
		variant.vt = VT_R8
		variant.value.dblVal = value
	elif isinstance(value, str):
		bstr = _oleaut32.SysAllocString(value)
		if not bstr:
			raise MemoryError("SysAllocString")
		variant.vt = VT_BSTR
		variant.value.bstrVal = bstr
	else:
		raise TypeError("unsupported COM argument type: %s" % type(value).__name__)


def _from_variant(variant):
	vt, value = variant.vt, variant.value
	if vt in (VT_EMPTY, VT_NULL):
		return None
	if vt == VT_BOOL:
		return value.boolVal != 0
	if vt in (VT_I4, VT_INT, VT_ERROR):
		return value.lVal
	if vt in (VT_UI4, VT_UINT):
		return value.lVal & 0xFFFFFFFF
	if vt == VT_I2:
		return value.iVal
	if vt == VT_UI2:
		return value.iVal & 0xFFFF
	if vt == VT_I1:
		return value.cVal
	if vt == VT_UI1:
		return value.bVal
	if vt == VT_I8:
		return value.llVal
	if vt == VT_UI8:
		return value.llVal & 0xFFFFFFFFFFFFFFFF
	if vt == VT_R8:
		return value.dblVal
	if vt == VT_R4:
		return value.fltVal
	if vt == VT_BSTR:
		if not value.bstrVal:
			return ""
		return ctypes.wstring_at(value.bstrVal, _oleaut32.SysStringLen(value.bstrVal))
	raise TypeError("unsupported COM result type: VARIANT type %d" % vt)


def _take_bstr(pointer):
	if not pointer:
		return ""
	text = ctypes.wstring_at(pointer, _oleaut32.SysStringLen(pointer))
	_oleaut32.SysFreeString(pointer)
	return text


class Dispatch(object):
	"""A late-bound Automation object, e.g. Dispatch("stata.StataOLEApp")."""

	def __init__(self, progid, context=CLSCTX_INPROC_SERVER | CLSCTX_LOCAL_SERVER):
		clsid = GUID()
		_check(_ole32.CLSIDFromProgID(progid, byref(clsid)), "CLSIDFromProgID(%s)" % progid)
		pointer = c_void_p()
		_check(_ole32.CoCreateInstance(byref(clsid), None, context, byref(_IID_IDispatch), byref(pointer)),
			"CoCreateInstance(%s)" % progid)
		self._pointer = pointer.value
		self._dispids = {}

	def _dispid(self, name):
		if name not in self._dispids:
			names = (c_wchar_p * 1)(name)
			dispid = c_long()
			_check(_vtable_call(self._pointer, 5, c_long,
				[POINTER(GUID), POINTER(c_wchar_p), c_uint, c_ulong, POINTER(c_long)],
				byref(_IID_NULL), names, 1, LOCALE_USER_DEFAULT, byref(dispid)), "GetIDsOfNames(%s)" % name)
			self._dispids[name] = dispid.value
		return self._dispids[name]

	def call(self, name, *args):
		"""Call a method (or read a property) and return its result."""
		if not self._pointer:
			raise ValueError("COM object has been released")
		dispid = self._dispid(name)
		count = len(args)
		variants = (VARIANT * max(count, 1))()
		try:
			# IDispatch::Invoke takes positional arguments in reverse order.
			for i, arg in enumerate(reversed(args)):
				_to_variant(arg, variants[i])
			params = DISPPARAMS(ctypes.cast(variants, POINTER(VARIANT)), None, count, 0)
			result = VARIANT()
			excepinfo = EXCEPINFO()
			arg_error = c_uint()
			hresult = _vtable_call(self._pointer, 6, c_long,
				[c_long, POINTER(GUID), c_ulong, c_ushort, POINTER(DISPPARAMS), POINTER(VARIANT),
					POINTER(EXCEPINFO), POINTER(c_uint)],
				dispid, byref(_IID_NULL), LOCALE_USER_DEFAULT, DISPATCH_METHOD | DISPATCH_PROPERTYGET,
				byref(params), byref(result), byref(excepinfo), byref(arg_error))
			if hresult & 0xFFFFFFFF == DISP_E_EXCEPTION:
				_take_bstr(excepinfo.bstrSource)
				_take_bstr(excepinfo.bstrHelpFile)
				description = _take_bstr(excepinfo.bstrDescription) or _describe(excepinfo.scode or hresult)
				raise COMError(excepinfo.scode or hresult, "%s: %s" % (name, description))
			_check(hresult, name)
			try:
				return _from_variant(result)
			finally:
				_oleaut32.VariantClear(byref(result))
		finally:
			for i in range(count):
				_oleaut32.VariantClear(byref(variants[i]))

	def release(self):
		if self._pointer:
			pointer, self._pointer = self._pointer, None
			_vtable_call(pointer, 2, c_ulong, [])
