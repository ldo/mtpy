#+
# My ctypes-based interface to libmtp.
#
# Written by Lawrence D'Oliveiro <ldo@geek-central.gen.nz>.
#-

import ctypes as ct
import os

mtp = ct.cdll.LoadLibrary("libmtp.so")
mtp.LIBMTP_Init()
mtp.LIBMTP_Release_Device.restype = None
mtp.LIBMTP_Get_Manufacturername.restype = ct.c_char_p
mtp.LIBMTP_Get_Modelname.restype = ct.c_char_p
mtp.LIBMTP_Get_Serialnumber.restype = ct.c_char_p
mtp.LIBMTP_Get_Deviceversion.restype = ct.c_char_p
mtp.LIBMTP_Get_Friendlyname.restype = ct.c_char_p
mtp.LIBMTP_Get_Syncpartner.restype = ct.c_char_p
mtp.LIBMTP_Get_Filetype_Description.restype = ct.c_char_p
mtp.LIBMTP_destroy_file_t.restype = None
mtp.LIBMTP_destroy_folder_t.restype = None
libc = ct.cdll.LoadLibrary("libc.so.6")
free = libc.free
free.restype = None
if ct.sizeof(ct.c_void_p) == 8 : # hopefully this will always be correct...
    time_t = ct.c_int64
else :
    time_t = ct.c_int32
#end if

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

# The filetypes defined here are the external types used
# by the libmtp library interface. The types used internally
# as PTP-defined enumerator types is something different.
FILETYPE_FOLDER = 0
FILETYPE_WAV = 1
FILETYPE_MP3 = 2
FILETYPE_WMA = 3
FILETYPE_OGG = 4
FILETYPE_AUDIBLE = 5
FILETYPE_MP4 = 6
FILETYPE_UNDEF_AUDIO = 7
FILETYPE_WMV = 8
FILETYPE_AVI = 9
FILETYPE_MPEG = 10
FILETYPE_ASF = 11
FILETYPE_QT = 12
FILETYPE_UNDEF_VIDEO = 13
FILETYPE_JPEG = 14
FILETYPE_JFIF = 15
FILETYPE_TIFF = 16
FILETYPE_BMP = 17
FILETYPE_GIF = 18
FILETYPE_PICT = 19
FILETYPE_PNG = 20
FILETYPE_VCALENDAR1 = 21
FILETYPE_VCALENDAR2 = 22
FILETYPE_VCARD2 = 23
FILETYPE_VCARD3 = 24
FILETYPE_WINDOWSIMAGEFORMAT = 25
FILETYPE_WINEXEC = 26
FILETYPE_TEXT = 27
FILETYPE_HTML = 28
FILETYPE_FIRMWARE = 29
FILETYPE_AAC = 30
FILETYPE_MEDIACARD = 31
FILETYPE_FLAC = 32
FILETYPE_MP2 = 33
FILETYPE_M4A = 34
FILETYPE_DOC = 35
FILETYPE_XML = 36
FILETYPE_XLS = 37
FILETYPE_PPT = 38
FILETYPE_MHT = 39
FILETYPE_JP2 = 40
FILETYPE_JPX = 41
FILETYPE_ALBUM = 42
FILETYPE_PLAYLIST = 43
FILETYPE_UNKNOWN = 44
filetype_t = ct.c_uint

def FILETYPE_IS_AUDIO(a) :
    return \
        (
            a == FILETYPE_WAV
        or
            a == FILETYPE_MP3
        or
            a == FILETYPE_MP2
        or
            a == FILETYPE_WMA
        or
            a == FILETYPE_OGG
        or
            a == FILETYPE_FLAC
        or
            a == FILETYPE_AAC
        or
            a == FILETYPE_M4A
        or
            a == FILETYPE_AUDIBLE
        or
            a == FILETYPE_UNDEF_AUDIO
        )
#end FILETYPE_IS_AUDIO

def FILETYPE_IS_VIDEO(a) :
    return \
        (
            a == FILETYPE_WMV
        or
            a == FILETYPE_AVI
        or
            a == FILETYPE_MPEG
        or
            a == FILETYPE_UNDEF_VIDEO
        )
 #end FILETYPE_IS_VIDEO

def FILETYPE_IS_AUDIOVIDEO(a) :
    return \
        (
            a == FILETYPE_MP4
        or
            a == FILETYPE_ASF
        or
            a == FILETYPE_QT
        )
#end FILETYPE_IS_AUDIOVIDEO

def FILETYPE_IS_TRACK(a) :
    """Use this to determine if the File API or Track API
    should be used to upload or download an object."""
    return \
        (
            FILETYPE_IS_AUDIO(a)
        or
            FILETYPE_IS_VIDEO(a)
        or
            FILETYPE_IS_AUDIOVIDEO(a)
        )
#end FILETYPE_IS_TRACK

def FILETYPE_IS_IMAGE(a) :
    return \
        (
            a == FILETYPE_JPEG
        or
            a == FILETYPE_JFIF
        or
            a == FILETYPE_TIFF
        or
            a == FILETYPE_BMP
        or
            a == FILETYPE_GIF
        or
            a == FILETYPE_PICT
        or
            a == FILETYPE_PNG
        or
            a == FILETYPE_JP2
        or
            a == FILETYPE_JPX
        or
            a == FILETYPE_WINDOWSIMAGEFORMAT
        )
#end FILETYPE_IS_IMAGE

def FILETYPE_IS_ADDRESSBOOK(a) :
    """Addressbook and Business card filetype test."""
    return \
        (
            a == FILETYPE_VCARD2
        or
            a == FILETYPE_VCARD2
        )
#end FILETYPE_IS_ADDRESSBOOK

def FILETYPE_IS_CALENDAR(a) :
    """Calendar and Appointment filetype test."""
    return \
        (
            a == FILETYPE_VCALENDAR1
        or
            a == FILETYPE_VCALENDAR2
        )
#end FILETYPE_IS_CALENDAR

class device_entry_t(ct.Structure) :
    _fields_ = \
        [
            ("vendor", ct.c_char_p),
            ("vendor_id", ct.c_uint16),
            ("product", ct.c_char_p),
            ("product_id", ct.c_uint16),
            ("device_flags", ct.c_uint32), # Bugs, device specifics etc
        ]
#end device_entry_t

class raw_device_t(ct.Structure) :
    _fields_ = \
        [
            ("device_entry", device_entry_t),
            ("bus_location", ct.c_uint32), # if device available
            ("devnum", ct.c_uint8), # Device number on the bus, if device available
        ]
#end raw_device_t

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

STORAGE_SORTBY_NOTSORTED = 0
STORAGE_SORTBY_FREESPACE = 1
STORAGE_SORTBY_MAXSPACE =  2

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

class file_t(ct.Structure) :
    pass
#end file_t
file_t._fields_ = \
    [
        ("item_id", ct.c_uint32), # Unique item ID
        ("parent_id", ct.c_uint32), # ID of parent folder
        ("storage_id", ct.c_uint32), # ID of storage holding this file
        ("name", ct.c_char_p), # Name of this file
          # (libmtp.h uses "filename", I use "name" for consistency with folder_t)
        ("filesize", ct.c_uint64), # Size of file in bytes
        ("modificationdate", time_t), # Date of last alteration of the file
        ("filetype", filetype_t), # Filetype used for the current file
        ("next", ct.POINTER(file_t)), # Next file in list or NULL if last file
    ]

class folder_t(ct.Structure) :
    pass
#end folder_t
folder_t._fields_ = \
    [
        ("item_id", ct.c_uint32), # Unique folder ID
          # (libmtp.h uses "folder_id", I use "item_id" for consistency with file_t)
        ("parent_id", ct.c_uint32), # ID of parent folder
        ("storage_id", ct.c_uint32), # ID of storage holding this file
        ("name", ct.c_char_p), # Name of folder
        ("sibling", ct.POINTER(folder_t)), # Next folder at same level or NULL if no more
        ("child", ct.POINTER(folder_t)), # Child folder or NULL if no children
    ]

mtp.LIBMTP_Open_Raw_Device.restype = ct.POINTER(mtpdevice_t)
mtp.LIBMTP_Open_Raw_Device_Uncached.restype = ct.POINTER(mtpdevice_t)
mtp.LIBMTP_Get_Files_And_Folders.restype = ct.POINTER(file_t)
mtp.LIBMTP_Get_Filelisting.restype = ct.POINTER(file_t)
mtp.LIBMTP_Get_Folder_List.restype = ct.POINTER(folder_t)

class RawDevice() :
    """representation of an available MTP device, as returned by get_raw_devices."""

    def __init__(self, device) :
        self.device = raw_device_t(device.device_entry, device.bus_location, device.devnum)
        for attr in ("vendor", "product") :
            setattr \
              ( # make separate copy of pointer fields
                self.device.device_entry,
                attr,
                bytes(getattr(device.device_entry, attr))
              )
            setattr(self, attr, getattr(device.device_entry, attr).decode("utf-8"))
        #end for
    #end __init__

    def open(self) :
        cached = False # Get_Files_And_Folders won't work otherwise
        return Device \
          (
            (mtp.LIBMTP_Open_Raw_Device_Uncached, mtp.LIBMTP_Open_Raw_Device)[cached]
                (ct.byref(self.device)),
            self
          )
    #end open

    def __repr__(self) :
        return "<RawDevice “%s %s”>" % (self.vendor, self.product)
    #end __repr__

#end RawDevice

def common_return_files_and_folders(items, device) :
    result = []
    while bool(items) :
        initem = items.contents
        is_folder = initem.filetype == FILETYPE_FOLDER
        outitem = (File, Folder)[is_folder](initem, device)
        result.append(outitem)
        # mtp.LIBMTP_destroy_file_t(items) # causes crash
        items = initem.next # even for folder!
    #end while
    return result
#end common_return_files_and_folders

def common_get_files_and_folders(device, storageid, root) :
    return \
        common_return_files_and_folders(mtp.LIBMTP_Get_Files_And_Folders(device.device, storageid, root), device)
#end common_get_files_and_folders

class Device() :
    """wraps an opened MTP device connection, as returned from RawDevice.open."""

    def __init__(self, device, rawdev) :
        self.device = device
        self.vendor = rawdev.vendor
        self.product = rawdev.product
        check_status(mtp.LIBMTP_Get_Storage(device, STORAGE_SORTBY_NOTSORTED))
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
        self.item_id = 0
        self.parent_id = 0
        self.got_descendants = False
        self.children_by_name = None
        self.descendants_by_id = None
    #end __init__

    def close(self) :
        """closes the connection. Must be the last operation on this Device object."""
        mtp.LIBMTP_Release_Device(self.device)
        del self.device
    #end close

    def __repr__(self) :
        return "<Device “%s %s”>" % (self.vendor, self.product)
    #end __repr__

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
        # fixme: lots of devices fail to implement this. Should follow libmtp detect.c
        # example and clear device error stack without failing.
        maxlevel = ct.c_int(0)
        curlevel = ct.c_int(0)
        check_status(mtp.LIBMTP_Get_Batterylevel(self.device, ct.byref(maxlevel), ct.byref(curlevel)))
        return maxlevel.value, curlevel.value
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

    def fullpath(self) :
        return "/" # I'm always root
    #end fullpath

    def _cache_contents(self, contents) :
        if self.children_by_name == None :
            self.children_by_name = {}
        if self.descendants_by_id == None :
            self.descendants_by_id = {0 : self}
        #end if
        for item in contents :
            if item.parent_id == 0 :
                self.children_by_name[item.name] = item
            #end if
            self.descendants_by_id[item.item_id] = item
        #end for
    #end _cache_contents

    def _ensure_got_descendants(self) :
        if not self.got_descendants :
            self._cache_contents(self.get_files_and_folders(0))
            self.got_descendants = True
        #end if
    #end _ensure_got_descendants

    def _ensure_got_children(self) :
        self._ensure_got_descendants()
    #end _ensure_got_children

    # higher-level access to device contents

    def get_children(self) :
        self._ensure_got_descendants()
        return list(self.children_by_name.values())
    #end get_children

    def get_descendants(self) :
        self._ensure_got_descendants()
        return list(self.descendants_by_id.values())
    #end get_descendants

    def get_child_by_name(self, name) :
        self._ensure_got_descendants()
        return self.children_by_name.get(name)
    #end get_child_by_name

    def get_descendant_by_id(self, id) :
        self._ensure_got_descendants()
        return self.descendants_by_id.get(id)
    #end get_descendant_by_id

    def get_descendant_by_path(self, path) :
        if path.startswith("/") :
            path = path[1:] # don't care relative or absolute
        #end if
        if path.endswith("/") :
            path = path[:-1]
            # don't bother requiring that result must be a folder
        #end if
        item = self
        if len(path) != 0 :
            segments = iter(path.split("/"))
        else :
            segments = iter([])
        #end if
        while True :
            seg = next(segments, None)
            if seg == None :
                break
            item._ensure_got_children()
            children = item.children_by_name
            item = children.get(seg)
            if item == None :
                break
        #end while
        return item
    #end get_descendant_by_path

    # don't use following directly, use above higher-level methods instead

    def get_files_and_folders(self, storageid = 0) :
        return common_get_files_and_folders(self, storageid, 0)
    #end get_files_and_folders

    def get_all_files(self) :
        return \
            common_return_files_and_folders(mtp.LIBMTP_Get_Filelisting(self.device), self)
    #end get_all_files

    def get_all_folders(self) :
        items = mtp.LIBMTP_Get_Folder_List(self.device)
        result = []
        while bool(items) :
            initem = items.contents
            outitem = Folder(initem, self)
            result.append(outitem)
            # mtp.LIBMTP_destroy_folder_t(items) # causes heap corruption?
            items = initem.sibling
        #end while
        return result
    #end get_all_folders

#end Device

class File :

    def __init__(self, f, device) :
        self.device = device
        for attr in ("item_id", "parent_id", "storage_id", "filesize", "modificationdate", "filetype") :
            setattr(self, attr, getattr(f, attr))
        #end for
        for attr in ("name",) :
            setattr(self, attr, getattr(f, attr).decode("utf-8"))
        #end for
    #end __init__

    def fullpath(self) :
        return "%s%s" % (self.device.get_descendant_by_id(self.parent_id).fullpath(), self.name)
    #end fullpath

    def __repr__(self) :
        return "<File “%s”>" % self.fullpath()
    #end __repr__

    def retrieve_to_file(self, destname) :
        if os.path.isdir(destname) :
            destname = os.path.join(destname, self.name)
        #end if
        check_status(mtp.LIBMTP_Get_File_To_File
          (
            self.device.device,
            self.item_id,
            destname.encode("utf-8"),
            None, # progress
            None # progress arg
          ))
        os.utime(destname, 2 * (self.modificationdate,))
    #end retrieve_to_file

#end File

class Folder :

    def __init__(self, f, device) :
        # f might be file_t or folder_t object
        self.device = device
        for attr in ("item_id", "parent_id", "storage_id") :
            setattr(self, attr, getattr(f, attr))
        #end for
        self.filetype = FILETYPE_FOLDER
        for attr in ("name",) :
            setattr(self, attr, getattr(f, attr).decode("utf-8"))
        #end for
        self.children_by_name = None
    #end __init__

    def fullpath(self) :
        return "%s%s/" % (self.device.get_descendant_by_id(self.parent_id).fullpath(), self.name)
    #end fullpath

    def __repr__(self) :
        return "<Folder “%s”>" % self.fullpath()
    #end __repr__

    def _ensure_got_children(self) :
        if self.children_by_name == None :
            self.device._ensure_got_descendants()
            self.children_by_name = dict \
              (
                (item.name, item) for item in self.device.descendants_by_id.values()
                if item.parent_id == self.item_id
              )
        #end if
    #end _ensure_got_children

    # higher-level access to device contents

    def get_children(self) :
        self._ensure_got_children()
        return list(self.children_by_name.values())
    #end get_children

    def get_child_by_name(self, name) :
        self._ensure_got_children()
        return self.children_by_name.get(name)
    #end get_child_by_name

    # don't use following directly, use above higher-level methods instead

    def get_files_and_folders(self, storageid = None) :
        if storageid != None :
            # look on specified storage
            storageids = (storageid,)
        else :
            # look on all available storage
            storageids = tuple(s["id"] for s in self.device.storage)
        #end if
        result = []
        for storageid in storageids :
            result.extend(common_get_files_and_folders(self.device, storageid, self.item_id))
        #end for
        return result
    #end get_files_and_folders

#end Folder

def get_raw_devices() :
    """returns a list of all MTP devices detected on the system."""
    devices = ct.POINTER(raw_device_t)()
    nr_devices = ct.c_int(0)
    check_status(mtp.LIBMTP_Detect_Raw_Devices(ct.byref(devices), ct.byref(nr_devices)))
    result = []
    for i in range(0, nr_devices.value) :
        result.append(RawDevice(devices[i]))
    #end for
    free(devices)
    return result
#end get_raw_devices
