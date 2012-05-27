import ctypes as ct

import sys # debug

mtp = ct.cdll.LoadLibrary("libmtp.so")
mtp.LIBMTP_Get_Manufacturername.restype = ct.c_char_p
mtp.LIBMTP_Get_Modelname.restype = ct.c_char_p
mtp.LIBMTP_Get_Serialnumber.restype = ct.c_char_p
mtp.LIBMTP_Get_Deviceversion.restype = ct.c_char_p
mtp.LIBMTP_Get_Friendlyname.restype = ct.c_char_p
mtp.LIBMTP_Get_Syncpartner.restype = ct.c_char_p
mtp.LIBMTP_Get_Filetype_Description.restype = ct.c_char_p

ERROR_NONE = 0
ERROR_GENERAL = 1
ERROR_PTP_LAYER = 2
ERROR_USB_LAYER = 3
ERROR_MEMORY_ALLOCATION = 4
ERROR_NO_DEVICE_ATTACHED = 5
ERROR_STORAGE_FULL = 6
ERROR_CONNECTING = 7
ERROR_CANCELLED = 8
error_number_t = ct.c_uint

class Error(RuntimeError) :
    name = \
        {
            0 : "NONE",
            1 : "GENERAL",
            2 : "PTP_LAYER",
            3 : "USB_LAYER",
            4 : "MEMORY_ALLOCATION",
            5 : "NO_DEVICE_ATTACHED",
            6 : "STORAGE_FULL",
            7 : "CONNECTING",
            8 : "CANCELLED",
        }

    def __init__(self, code) :
        RuntimeError.__init__(self, "libmtp error %d -- %s" % (code, self.name.get(code, "?")))
    #end __init__

#end Error

def check_status(status) :
    if status != ERROR_NONE :
        raise Error(status)
    #end if
#end check_status

class error_t(ct.Structure) :
    pass
#end error_t
error_t._fields_ = \
    [
        ("errornumber", error_number_t),
        ("error_text", ct.c_char_p),
        ("next", ct.POINTER(error_t)),
    ]

class devicestorage_t(ct.Structure) :
    pass
#end devicestorage_t
devicestorage_t._fields_ = \
    [
        ("id", ct.c_uint32), # Unique ID for this storage
        ("StorageType", ct.c_uint16),
        ("FilesystemType", ct.c_uint16),
        ("AccessCapability", ct.c_uint16),
        ("MaxCapacity", ct.c_uint64),
        ("FreeSpaceInBytes", ct.c_uint64),
        ("FreeSpaceInObjects", ct.c_uint64),
        ("StorageDescription", ct.c_char_p),
        ("VolumeIdentifier", ct.c_char_p),
        ("next", ct.POINTER(devicestorage_t)), # Next storage, follow this link until NULL
        ("prev", ct.POINTER(devicestorage_t)),
    ]

LIBMTP_STORAGE_SORTBY_NOTSORTED = 0
LIBMTP_STORAGE_SORTBY_FREESPACE = 1
LIBMTP_STORAGE_SORTBY_MAXSPACE =  2

class device_extension_t(ct.Structure) :
    pass
#end device_extension_t
device_extension_t._fields_ = \
    [
        ("name", ct.c_char_p),
        ("major", ct.c_int), # major revision
        ("minor", ct.c_int), # minor revision
        ("next", ct.POINTER(device_extension_t)), # Pointer to the next extension or NULL if this is the last extension.
    ]

filetype_t = ct.c_uint

class mtpdevice_t(ct.Structure) :
    pass
#end mtpdevice_t
mtpdevice_t._fields_ = \
    [
        ("object_bitsize", ct.c_uint8), # Object bitsize, typically 32 or 64.
        ("params", ct.c_void_p), # Parameters for this device, must be cast into (PTPParams*) before internal use.
        ("usbinfo", ct.c_void_p), # USB device for this device, must be cast into (PTP_USB*) before internal use.
        ("storage", ct.POINTER(devicestorage_t)), # The storage for this device, do not use strings in here without copying them first, and beware that this list may be rebuilt at any time. @see LIBMTP_Get_Storage()
        ("errorstack", ct.POINTER(error_t)), # The error stack. This shall be handled using the error getting and clearing functions, not by dereferencing this list.
        ("maximum_battery_level", ct.c_uint8),
        ("default_music_folder", ct.c_uint32),
        ("default_playlist_folder", ct.c_uint32),
        ("default_picture_folder", ct.c_uint32),
        ("default_video_folder", ct.c_uint32),
        ("default_organizer_folder", ct.c_uint32),
        ("default_zencast_folder", ct.c_uint32), # (only Creative devices...)
        ("default_album_folder", ct.c_uint32),
        ("default_text_folder", ct.c_uint32),
        ("cd", ct.c_void_p), # Per device iconv() converters, only used internally
        ("extensions", ct.POINTER(device_extension_t)),
        ("cached", ct.c_int), # Whether the device uses caching, only used internally
        ("next", ct.POINTER(mtpdevice_t)), # Pointer to next device in linked list; NULL if this is the last device
    ]

connected_devices = ct.POINTER(mtpdevice_t)()

class Device() :

    def __init__(self, device) :
        self.device = device
        check_status(mtp.LIBMTP_Get_Storage(device, LIBMTP_STORAGE_SORTBY_NOTSORTED))
        for \
            k \
        in \
            (
                "object_bitsize", "maximum_battery_level", "default_music_folder",
                "default_playlist_folder", "default_picture_folder",
                "default_video_folder", "default_organizer_folder",
                "default_zencast_folder", "default_album_folder", "default_text_folder",
            ) \
        :
            setattr(self, k, getattr(device.contents, k))
        #end for
        self.storage = []
        sto = device.contents.storage
        while bool(sto) :
            sto = sto.contents
            self.storage.append \
              (
                dict
                  (
                    (k, getattr(sto, k))
                    for k in
                        (
                            "id", "StorageType", "FilesystemType", "AccessCapability",
                            "MaxCapacity", "FreeSpaceInBytes", "FreeSpaceInObjects",
                            "StorageDescription", "VolumeIdentifier",
                        )
                  )
              )
            sto = sto.next
        #end while
        self.extensions = []
        ext = device.contents.extensions
        while bool(ext) :
            ext = ext.contents
            self.extensions.append \
              (
                dict
                  (
                    (k, getattr(ext, k))
                    for k in ("name", "major", "minor")
                  )
              )
            ext = ext.next
        #end while
    #end __init__

    def get_manufacturer_name(self) :
        return bytes(mtp.LIBMTP_Get_Manufacturername(self.device)).decode("utf-8")
    #end get_manufacturer_name

    def get_model_name(self) :
        return bytes(mtp.LIBMTP_Get_Modelname(self.device)).decode("utf-8")
    #end get_model_name

    def get_serial_number(self) :
        return bytes(mtp.LIBMTP_Get_Serialnumber(self.device)).decode("utf-8")
    #end get_serial_number

    def get_device_version(self) :
        return bytes(mtp.LIBMTP_Get_Deviceversion(self.device)).decode("utf-8")
    #end get_device_version

    def get_friendly_name(self) :
        return bytes(mtp.LIBMTP_Get_Friendlyname(self.device)).decode("utf-8")
    #end get_friendly_name

    def set_friendly_name(self, new_name) :
        check_status(mtp.LIBMTP_Set_Friendlyname(self.device, new_name.encode("utf-8")))
    #end set_friendly_name

    def get_sync_parner(self) :
        return bytes(mtp.LIBMTP_Get_Syncpartner(self.device)).decode("utf-8")
    #end get_sync_parner

    def set_sync_partner(self, new_name) :
        check_status(mtp.LIBMTP_Set_Syncpartner(self.device, new_name.encode("utf-8")))
    #end set_sync_partner

    def get_battery_level(self) :
        val1 = ct.c_int(0)
        val2 = ct.c_int(0)
        check_status(mtp.LIBMTP_Get_Batterylevel(self.device, ct.byref(val1), ct.byref(val2)))
        return val1.value, val2.value
    #end get_battery_level

    def get_secure_time(self) :
        result = ct.c_char_p()
        check_status(mtp.LIBMTP_Get_Secure_Time(self.device, ct.byref(result)))
        return bytes(result)
    #end get_secure_time

    def get_device_certificate(self) :
        result = ct.c_char_p()
        check_status(mtp.LIBMTP_Get_Device_Certificate(self.device, ct.byref(result)))
        return bytes(result)
    #end get_device_certificate

    def get_supported_filetypes(self) :
        types = ct.POINTER(ct.c_uint16)()
        nrtypes = ct.c_uint16(0)
        check_status(mtp.LIBMTP_Get_Supported_Filetypes(self.device, ct.byref(types), ct.byref(nrtypes)))
        result = []
        for i in range(0, nrtypes.value) :
            result.append \
              (
                (
                    types[i],
                    bytes(mtp.LIBMTP_Get_Filetype_Description(filetype_t(types[i]))).decode("utf-8")
                )
              )
        #end for
        return result
    #end get_supported_filetypes

#end Device

def get_connected_devices(refresh = True) :
    global connected_devices
    if refresh or not bool(connected_devices) :
        if bool(connected_devices) :
            mtp.LIBMTP_Release_Device_List(connected_devices)
            connected_devices = ct.POINTER(mtpdevice_t)()
        #end if
        check_status(mtp.LIBMTP_Get_Connected_Devices(ct.byref(connected_devices)))
    #end if
    dev = connected_devices
    result = []
    while bool(dev) :
        result.append(Device(dev))
        dev = dev.contents.next
    #end while
    return result
#end get_connected_devices
