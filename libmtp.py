import ctypes as ct

mtp = ct.cdll.LoadLibrary("libmtp.so")

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

def Get_Connected_Devices() :
    devices = ct.POINTER(mtpdevice_t)()
    status = mtp.LIBMTP_Get_Connected_Devices(ct.byref(devices))
    if status != ERROR_NONE :
        raise Error(status)
    #end if
    dev = devices
    result = []
    while bool(dev) :
        status = mtp.LIBMTP_Get_Storage(dev, LIBMTP_STORAGE_SORTBY_NOTSORTED)
        if status != ERROR_NONE :
            raise Error(status)
        #end if
        dev = dev.contents
        item = dict \
          (
            (k, getattr(dev, k))
            for k in
                (
                    "object_bitsize", "maximum_battery_level", "default_music_folder",
                    "default_playlist_folder", "default_picture_folder",
                    "default_video_folder", "default_organizer_folder",
                    "default_zencast_folder", "default_album_folder", "default_text_folder",
                )
          )
        storage = []
        sto = dev.storage
        while bool(sto) :
            sto = sto.contents
            storage.append \
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
        item["storage"] = storage
        extensions = []
        ext = dev.extensions
        while bool(ext) :
            ext = ext.contents
            extensions.append \
              (
                dict
                  (
                    (k, getattr(ext, k))
                    for k in ("name", "major", "minor")
                  )
              )
            ext = ext.next
        #end while
        item["extensions"] = extensions
        result.append(item)
        dev = dev.next
    #end while
    mtp.LIBMTP_Release_Device_List(devices)
    return result
#end Get_Connected_Devices
