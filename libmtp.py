#+
# My ctypes-based interface to libmtp.
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2 of the License, or (at your option) any later version.
#
# Overview: use get_raw_devices() to get a list of RawDevice objects
# representing MTP-speaking devices connected to your host system.
# Use the open() method on any of these to obtain a Device object.
# This has methods to look up File and Folder objects for its contents,
# and all of these also have methods for various manipulations
# as appropriate: upload a file from the host, download a file to the
# host, create a folder, and delete a file or folder.
#
# Not implemented: track, album, playlist and file-sample-data parts
# of the API. The only MTP-speaking device I have is an Android phone
# (Samsung Galaxy Nexus) which only uses MTP for file-transfer
# purposes, not for its media-player functions.
#
# Written by Lawrence D'Oliveiro <ldo@geek-central.gen.nz>.
#-

import ctypes as ct
import os
import errno

mtp = ct.cdll.LoadLibrary("libmtp.so")
mtp.LIBMTP_Init()
mtp.LIBMTP_Release_Device.restype = None
mtp.LIBMTP_Clear_Errorstack.restype = None
mtp.LIBMTP_Dump_Errorstack.restype = None
mtp.LIBMTP_Get_Manufacturername.restype = ct.c_char_p
mtp.LIBMTP_Get_Modelname.restype = ct.c_char_p
mtp.LIBMTP_Get_Serialnumber.restype = ct.c_char_p
mtp.LIBMTP_Get_Deviceversion.restype = ct.c_char_p
mtp.LIBMTP_Get_Friendlyname.restype = ct.c_char_p
mtp.LIBMTP_Get_Syncpartner.restype = ct.c_char_p
mtp.LIBMTP_Get_Filetype_Description.restype = ct.c_char_p
mtp.LIBMTP_destroy_file_t.restype = None
mtp.LIBMTP_destroy_folder_t.restype = None
mtp.LIBMTP_Create_Folder.restype = ct.c_uint32
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

def check_status(status, device = None) :
    if status != ERROR_NONE :
        if device != None :
            mtp.LIBMTP_Dump_Errorstack(device)
            mtp.LIBMTP_Clear_Errorstack(device)
        #end if
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

#+
# Internal low-level structs
# (if in doubt, stay away from these)
#-

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
mtp.LIBMTP_new_file_t.restype = ct.POINTER(file_t)

#+
# Internal useful stuff
#-

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

def common_send_file(device, src, parentid, destname) :
    newfile = mtp.LIBMTP_new_file_t()
    newfile.contents.filesize = os.stat(src).st_size
    newfile.contents.name = ct.cast(libc.strdup(destname.encode("utf-8")), ct.c_char_p)
    newfile.contents.parent_id = parentid
    check_status \
      (
        mtp.LIBMTP_Send_File_From_File
          (
            device.device,
            src.encode("utf-8"),
            newfile,
            None, # progress
            None # progress arg
          ),
        device.device
      )
    device.set_contents_changed()
    result = device.get_descendant_by_id(newfile.contents.item_id)
    mtp.LIBMTP_destroy_file_t(newfile)
    return result
#end common_send_file

#+
# User-visible high-level classes
#-

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

class Device() :
    """wraps an opened MTP device connection, as returned from RawDevice.open."""

    def __init__(self, device, rawdev) :
        self.device = device
        self.vendor = rawdev.vendor
        self.product = rawdev.product
        check_status(mtp.LIBMTP_Get_Storage(device, STORAGE_SORTBY_NOTSORTED), device)
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
        self.update_seq = 1 # cache coherence check
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
        check_status(mtp.LIBMTP_Set_Friendlyname(self.device, new_name.encode("utf-8")), self.device)
    #end set_friendly_name

    def get_sync_parner(self) :
        return bytes(mtp.LIBMTP_Get_Syncpartner(self.device)).decode("utf-8")
    #end get_sync_parner

    def set_sync_partner(self, new_name) :
        check_status(mtp.LIBMTP_Set_Syncpartner(self.device, new_name.encode("utf-8")), self.device)
    #end set_sync_partner

    def get_battery_level(self) :
        # fixme: lots of devices fail to implement this. Should follow libmtp detect.c
        # example and clear device error stack without failing.
        maxlevel = ct.c_int(0)
        curlevel = ct.c_int(0)
        check_status(mtp.LIBMTP_Get_Batterylevel(self.device, ct.byref(maxlevel), ct.byref(curlevel)), self.device)
        return maxlevel.value, curlevel.value
    #end get_battery_level

    def get_secure_time(self) :
        result = ct.c_char_p()
        check_status(mtp.LIBMTP_Get_Secure_Time(self.device, ct.byref(result)), self.device)
        return bytes(result)
    #end get_secure_time

    def get_device_certificate(self) :
        result = ct.c_char_p()
        check_status(mtp.LIBMTP_Get_Device_Certificate(self.device, ct.byref(result)), self.device)
        return bytes(result)
    #end get_device_certificate

    def get_supported_filetypes(self) :
        types = ct.POINTER(ct.c_uint16)()
        nrtypes = ct.c_uint16(0)
        check_status(mtp.LIBMTP_Get_Supported_Filetypes(self.device, ct.byref(types), ct.byref(nrtypes)), self.device)
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
        """returns the fully-qualified pathname of the root directory."""
        return "/" # I'm always root
    #end fullpath

    def set_contents_changed(self) :
        """Call this on any creation/deletion of files/folders, to force refetch
        of all files/folders."""
        self.got_descendants = 0
        self.children_by_name = None
        self.descendants_by_id = None
        self.update_seq += 1
    #def set_contents_changed

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
        """returns all the files and folders at the root level of the device."""
        self._ensure_got_descendants()
        return list(self.children_by_name.values())
    #end get_children

    def get_descendants(self) :
        """returns all the files and folders on the device."""
        self._ensure_got_descendants()
        return list(self.descendants_by_id.values())
    #end get_descendants

    def get_child_by_name(self, name) :
        """returns a named file or folder at the root level of the device, or None
        if not found."""
        self._ensure_got_descendants()
        return self.children_by_name.get(name)
    #end get_child_by_name

    def get_descendant_by_id(self, id) :
        """returns a file or folder on the device identified by device-wide ID,
        or None if not found."""
        self._ensure_got_descendants()
        return self.descendants_by_id.get(id)
    #end get_descendant_by_id

    def get_descendant_by_path(self, path) :
        """returns a file or folder corresponding to the specified path spec
        in usual *nix form, or None if not found."""
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

    # end don't-use stuff

    def send_file(self, src, destname) :
        """sends the specified file to the device under the specified name
        at the top level, and returns a new File object for it."""
        # should I allow default destname here as well?
        return common_send_file(self, src, 0, destname)
    #end send_file

    def create_subfolder(self, name, storageid = 0) :
        """creates a folder with the specified name at the root level of the
        device, and returns a Folder object representing it."""
        folderid = mtp.LIBMTP_Create_Folder \
          (
            self.device,
            name.encode("utf-8"),
            0,
            storageid
          )
        if folderid == 0 :
            mtp.LIBMTP_Dump_Errorstack(self.device)
            mtp.LIBMTP_Clear_Errorstack(self.device)
            raise Error(ERROR_GENERAL)
        #end if
        self.set_contents_changed()
        return self.get_descendant_by_id(folderid)
    #end create_subfolder

#end Device

class File :
    """representation of a file on the device. Don't create these objects yourself,
    always get them from lookup or creation methods."""

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
        """returns the fully-qualified pathname of the file."""
        return "%s%s" % (self.device.get_descendant_by_id(self.parent_id).fullpath(), self.name)
    #end fullpath

    def __repr__(self) :
        return "<File “%s”>" % self.fullpath()
    #end __repr__

    def get_parent(self) :
        """returns the immediately-containing parent Folder or Device object."""
        return self.device.get_descendant_by_id(self.parent_id)
    #end get_parent

    def retrieve_to_file(self, destname) :
        """copies the contents of the file to the host filesystem under the
        specified name."""
        if os.path.isdir(destname) :
            destname = os.path.join(destname, self.name)
        #end if
        check_status \
          (
            mtp.LIBMTP_Get_File_To_File
              (
                self.device.device,
                self.item_id,
                destname.encode("utf-8"),
                None, # progress
                None # progress arg
              ),
            self.device.device
          )
        os.utime(destname, 2 * (self.modificationdate,))
    #end retrieve_to_file

    def delete(self, delete_contents = False) :
        """deletes the file on the device. You must not make any further use
        of this File object after this call."""
        # delete_contents ignored, allowed for compatibility with Folder.delete
        check_status \
          (
            mtp.LIBMTP_Delete_Object
              (
                self.device.device,
                self.item_id
              ),
            self.device.device
          )
        self.device.set_contents_changed()
        # make myself unusable:
        del self.name
        del self.item_id
    #end delete

#end File

class Folder :
    """representation of a folder on the device. Don't create these objects yourself,
    always get them from lookup or creation methods."""

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
        self.update_seq = 0 # cache coherence check
    #end __init__

    def fullpath(self) :
        """returns the fully-qualified pathname of the folder."""
        return "%s%s/" % (self.device.get_descendant_by_id(self.parent_id).fullpath(), self.name)
    #end fullpath

    def __repr__(self) :
        return "<Folder “%s”>" % self.fullpath()
    #end __repr__

    def _ensure_got_children(self) :
        if self.children_by_name == None or self.update_seq != self.device.update_seq :
            self.device._ensure_got_descendants()
            self.children_by_name = dict \
              (
                (item.name, item) for item in self.device.descendants_by_id.values()
                if item.parent_id == self.item_id
              )
            self.update_seq = self.device.update_seq
        #end if
    #end _ensure_got_children

    def get_parent(self) :
        """returns the immediately-containing parent Folder or Device."""
        return self.device.get_descendant_by_id(self.parent_id)
    #end get_parent

    def set_contents_changed(self) :
        """Call this on any creation/deletion of file/folder contents."""
        self.device.set_contents_changed()
    #def set_contents_changed

    # higher-level access to device contents

    def get_children(self) :
        """returns all the immediate child files and folders of this folder."""
        self._ensure_got_children()
        return list(self.children_by_name.values())
    #end get_children

    def get_child_by_name(self, name) :
        """returns the immediate child file/folder with the specified name,
        or None if not found."""
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

    # end don't-use stuff

    def retrieve_to_folder(self, dest) :
        """retrieves the entire contents of this Folder (and recursively of all
        its subfolders) into the specified destination directory on the host filesystem."""
        try :
            # only create leaf dir on demand, rest must already exist
            os.mkdir(dest)
        except OSError as Err :
            if Err.errno == errno.EXIST :
                pass
            else :
                raise
            #end if
        #end try
        for item in self.children_by_name.values() :
            if isinstance(item, File) :
                item.retrieve_to_file(os.path.join(dest, item.name))
            elif isinstance(item, Folder) :
                item.retrieve_to_folder(os.path.join(dest, item.name))
            #end if
        #end for
    #end retrieve_to_folder

    def send_file(self, src, destname = None) :
        """sends the specified file to the device under the specified name within
        this Folder, and returns a new File object for it."""
        if destname == None :
            destname = os.path.basename(src)
        #end if
        return common_send_file(self.device, src, self.item_id, destname)
    #end send_file

    def create_subfolder(self, name, storageid = 0) :
        """creates a folder with the specified name at the top level of this
        Folder, and returns a Folder object representing it."""
        folderid = mtp.LIBMTP_Create_Folder \
          (
            self.device.device,
            name.encode("utf-8"),
            self.item_id,
            storageid
          )
        if folderid == 0 :
            mtp.LIBMTP_Dump_Errorstack(self.device.device)
            mtp.LIBMTP_Clear_Errorstack(self.device.device)
            raise Error(ERROR_GENERAL)
        #end if
        self.device.set_contents_changed()
        return self.device.get_descendant_by_id(folderid)
    #end create_subfolder

    def delete(self, delete_contents = False) :
        """deletes the folder on the device. You must not make any further use
        of this Folder object (or any of its descendant File or Folder objects)
        after this call."""
        children = self.get_children()
        if len(children) != 0 and not delete_contents :
            raise RuntimeError("folder is not empty")
        #end if
        if delete_contents :
            for child in children :
                child.delete(delete_contents)
            #end for
        #end if
        check_status \
          (
            mtp.LIBMTP_Delete_Object
              (
                self.device.device,
                self.item_id
              ),
            self.device.device
          )
        self.set_contents_changed()
        # make myself unusable:
        del self.name
        del self.item_id
        del self.children_by_name
    #end delete

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
