#+
# My ctypes-based interface to libmtp.
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
# Copyright 2012 by Lawrence D'Oliveiro <ldo@geek-central.gen.nz>.
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2 of the License, or (at your option) any later version.
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
mtp.LIBMTP_Get_String_From_Object.restype = ct.c_void_p # c_char_p
mtp.LIBMTP_Get_u64_From_Object.restype = ct.c_uint64
mtp.LIBMTP_Get_u32_From_Object.restype = ct.c_uint32
mtp.LIBMTP_Get_u16_From_Object.restype = ct.c_uint16
mtp.LIBMTP_Get_u8_From_Object.restype = ct.c_uint8
mtp.LIBMTP_Get_Property_Description.restype = ct.c_char_p # I don't need to dispose of result
mtp.LIBMTP_destroy_allowed_values_t.restype = None
mtp.LIBMTP_Create_Folder.restype = ct.c_uint32
mtp.LIBMTP_destroy_track_t.restype = None
mtp.LIBMTP_destroy_playlist_t.restype = None
mtp.LIBMTP_destroy_album_t.restype = None
libc = ct.cdll.LoadLibrary("libc.so.6")
libc.malloc.restype = ct.c_void_p
libc.free.argtypes = [ct.c_void_p]
libc.free.restype = None
libc.strdup.restype = ct.c_void_p
  # cannot use ct.c_char_p because ctypes insists on converting it to a bytes object
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

# The properties defined here are the external types used
# by the libmtp library interface.
PROPERTY_StorageID = 0
PROPERTY_ObjectFormat = 1
PROPERTY_ProtectionStatus = 2
PROPERTY_ObjectSize = 3
PROPERTY_AssociationType = 4
PROPERTY_AssociationDesc = 5
PROPERTY_ObjectFileName = 6
PROPERTY_DateCreated = 7
PROPERTY_DateModified = 8
PROPERTY_Keywords = 9
PROPERTY_ParentObject = 10
PROPERTY_AllowedFolderContents = 11
PROPERTY_Hidden = 12
PROPERTY_SystemObject = 13
PROPERTY_PersistantUniqueObjectIdentifier = 14
PROPERTY_SyncID = 15
PROPERTY_PropertyBag = 16
PROPERTY_Name = 17
PROPERTY_CreatedBy = 18
PROPERTY_Artist = 19
PROPERTY_DateAuthored = 20
PROPERTY_Description = 21
PROPERTY_URLReference = 22
PROPERTY_LanguageLocale = 23
PROPERTY_CopyrightInformation = 24
PROPERTY_Source = 25
PROPERTY_OriginLocation = 26
PROPERTY_DateAdded = 27
PROPERTY_NonConsumable = 28
PROPERTY_CorruptOrUnplayable = 29
PROPERTY_ProducerSerialNumber = 30
PROPERTY_RepresentativeSampleFormat = 31
PROPERTY_RepresentativeSampleSize = 32
PROPERTY_RepresentativeSampleHeight = 33
PROPERTY_RepresentativeSampleWidth = 34
PROPERTY_RepresentativeSampleDuration = 35
PROPERTY_RepresentativeSampleData = 36
PROPERTY_Width = 37
PROPERTY_Height = 38
PROPERTY_Duration = 39
PROPERTY_Rating = 40
PROPERTY_Track = 41
PROPERTY_Genre = 42
PROPERTY_Credits = 43
PROPERTY_Lyrics = 44
PROPERTY_SubscriptionContentID = 45
PROPERTY_ProducedBy = 46
PROPERTY_UseCount = 47
PROPERTY_SkipCount = 48
PROPERTY_LastAccessed = 49
PROPERTY_ParentalRating = 50
PROPERTY_MetaGenre = 51
PROPERTY_Composer = 52
PROPERTY_EffectiveRating = 53
PROPERTY_Subtitle = 54
PROPERTY_OriginalReleaseDate = 55
PROPERTY_AlbumName = 56
PROPERTY_AlbumArtist = 57
PROPERTY_Mood = 58
PROPERTY_DRMStatus = 59
PROPERTY_SubDescription = 60
PROPERTY_IsCropped = 61
PROPERTY_IsColorCorrected = 62
PROPERTY_ImageBitDepth = 63
PROPERTY_Fnumber = 64
PROPERTY_ExposureTime = 65
PROPERTY_ExposureIndex = 66
PROPERTY_DisplayName = 67
PROPERTY_BodyText = 68
PROPERTY_Subject = 69
PROPERTY_Priority = 70
PROPERTY_GivenName = 71
PROPERTY_MiddleNames = 72
PROPERTY_FamilyName = 73
PROPERTY_Prefix = 74
PROPERTY_Suffix = 75
PROPERTY_PhoneticGivenName = 76
PROPERTY_PhoneticFamilyName = 77
PROPERTY_EmailPrimary = 78
PROPERTY_EmailPersonal1 = 79
PROPERTY_EmailPersonal2 = 80
PROPERTY_EmailBusiness1 = 81
PROPERTY_EmailBusiness2 = 82
PROPERTY_EmailOthers = 83
PROPERTY_PhoneNumberPrimary = 84
PROPERTY_PhoneNumberPersonal = 85
PROPERTY_PhoneNumberPersonal2 = 86
PROPERTY_PhoneNumberBusiness = 87
PROPERTY_PhoneNumberBusiness2 = 88
PROPERTY_PhoneNumberMobile = 89
PROPERTY_PhoneNumberMobile2 = 90
PROPERTY_FaxNumberPrimary = 91
PROPERTY_FaxNumberPersonal = 92
PROPERTY_FaxNumberBusiness = 93
PROPERTY_PagerNumber = 94
PROPERTY_PhoneNumberOthers = 95
PROPERTY_PrimaryWebAddress = 96
PROPERTY_PersonalWebAddress = 97
PROPERTY_BusinessWebAddress = 98
PROPERTY_InstantMessengerAddress = 99
PROPERTY_InstantMessengerAddress2 = 100
PROPERTY_InstantMessengerAddress3 = 101
PROPERTY_PostalAddressPersonalFull = 102
PROPERTY_PostalAddressPersonalFullLine1 = 103
PROPERTY_PostalAddressPersonalFullLine2 = 104
PROPERTY_PostalAddressPersonalFullCity = 105
PROPERTY_PostalAddressPersonalFullRegion = 106
PROPERTY_PostalAddressPersonalFullPostalCode = 107
PROPERTY_PostalAddressPersonalFullCountry = 108
PROPERTY_PostalAddressBusinessFull = 109
PROPERTY_PostalAddressBusinessLine1 = 110
PROPERTY_PostalAddressBusinessLine2 = 111
PROPERTY_PostalAddressBusinessCity = 112
PROPERTY_PostalAddressBusinessRegion = 113
PROPERTY_PostalAddressBusinessPostalCode = 114
PROPERTY_PostalAddressBusinessCountry = 115
PROPERTY_PostalAddressOtherFull = 116
PROPERTY_PostalAddressOtherLine1 = 117
PROPERTY_PostalAddressOtherLine2 = 118
PROPERTY_PostalAddressOtherCity = 119
PROPERTY_PostalAddressOtherRegion = 120
PROPERTY_PostalAddressOtherPostalCode = 121
PROPERTY_PostalAddressOtherCountry = 122
PROPERTY_OrganizationName = 123
PROPERTY_PhoneticOrganizationName = 124
PROPERTY_Role = 125
PROPERTY_Birthdate = 126
PROPERTY_MessageTo = 127
PROPERTY_MessageCC = 128
PROPERTY_MessageBCC = 129
PROPERTY_MessageRead = 130
PROPERTY_MessageReceivedTime = 131
PROPERTY_MessageSender = 132
PROPERTY_ActivityBeginTime = 133
PROPERTY_ActivityEndTime = 134
PROPERTY_ActivityLocation = 135
PROPERTY_ActivityRequiredAttendees = 136
PROPERTY_ActivityOptionalAttendees = 137
PROPERTY_ActivityResources = 138
PROPERTY_ActivityAccepted = 139
PROPERTY_Owner = 140
PROPERTY_Editor = 141
PROPERTY_Webmaster = 142
PROPERTY_URLSource = 143
PROPERTY_URLDestination = 144
PROPERTY_TimeBookmark = 145
PROPERTY_ObjectBookmark = 146
PROPERTY_ByteBookmark = 147
PROPERTY_LastBuildDate = 148
PROPERTY_TimetoLive = 149
PROPERTY_MediaGUID = 150
PROPERTY_TotalBitRate = 151
PROPERTY_BitRateType = 152
PROPERTY_SampleRate = 153
PROPERTY_NumberOfChannels = 154
PROPERTY_AudioBitDepth = 155
PROPERTY_ScanDepth = 156
PROPERTY_AudioWAVECodec = 157
PROPERTY_AudioBitRate = 158
PROPERTY_VideoFourCCCodec = 159
PROPERTY_VideoBitRate = 160
PROPERTY_FramesPerThousandSeconds = 161
PROPERTY_KeyFrameDistance = 162
PROPERTY_BufferSize = 163
PROPERTY_EncodingQuality = 164
PROPERTY_EncodingProfile = 165
PROPERTY_BuyFlag = 166
PROPERTY_UNKNOWN = 167
property_t = ct.c_uint

# These are the data types
DATATYPE_INT8 = 0
DATATYPE_UINT8 = 1
DATATYPE_INT16 = 2
DATATYPE_UINT16 = 3
DATATYPE_INT32 = 4
DATATYPE_UINT32 = 5
DATATYPE_INT64 = 6
DATATYPE_UINT64 = 7
datatype_t = ct.c_uint

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
mtp.LIBMTP_new_folder_t.restype = ct.POINTER(folder_t)

class track_t(ct.Structure) :
    pass
#end track_t
track_t._fields_ = \
    [
        ("item_id", ct.c_uint32), # Unique item ID
        ("parent_id", ct.c_uint32), # ID of parent folder
        ("storage_id", ct.c_uint32), # ID of storage holding this track
        ("title", ct.c_char_p), # Track title
        ("artist", ct.c_char_p), # Name of recording artist
        ("composer", ct.c_char_p), # Name of recording composer
        ("genre", ct.c_char_p), # Genre name for track
        ("album", ct.c_char_p), # Album name for track
        ("date", ct.c_char_p), # Date of original recording as a string
        ("filename", ct.c_char_p), # Original filename of this track
        ("tracknumber", ct.c_uint16), # Track number (in sequence on recording)
        ("duration", ct.c_uint32), # Duration in milliseconds
        ("samplerate", ct.c_uint32), # Sample rate of original file, min 0x1f80 max 0xbb80
        ("nochannels", ct.c_uint16), # Number of channels in this recording 0 = unknown, 1 or 2
        ("wavecodec", ct.c_uint32), # FourCC wave codec name
        ("bitrate", ct.c_uint32), # (Average) bitrate for this file min=1 max=0x16e360
        ("bitratetype", ct.c_uint16), # 0 = unused, 1 = constant, 2 = VBR, 3 = free
        ("rating", ct.c_uint16), # User rating 0-100 (0x00-0x64)
        ("usecount", ct.c_uint32), # Number of times used/played
        ("filesize", ct.c_uint64), # Size of track file in bytes
        ("modificationdate", time_t), # Date of last alteration of the track
        ("filetype", filetype_t), # Filetype used for the current track
        ("next", ct.POINTER(track_t)), # Next track in list or NULL if last track
    ]

class playlist_t(ct.Structure) :
    pass
#end playlist_t
playlist_t._fields_ = \
    [
        ("playlist_id", ct.c_uint32), # Unique playlist ID
        ("parent_id", ct.c_uint32), # ID of parent folder
        ("storage_id", ct.c_uint32), # ID of storage holding this playlist
        ("name", ct.c_char_p), # Name of playlist
        ("tracks", ct.POINTER(ct.c_uint32)), # The tracks in this playlist
        ("no_tracks", ct.c_uint32), # The number of tracks in this playlist
        ("next", ct.POINTER(playlist_t)), # Next playlist or NULL if last playlist
    ]

class album_t(ct.Structure) :
    pass
#end album_t
album_t._fields_ = \
    [
        ("album_id", ct.c_uint32), # Unique playlist ID
        ("parent_id", ct.c_uint32), # ID of parent folder
        ("storage_id", ct.c_uint32), # ID of storage holding this album
        ("name", ct.c_char_p), # Name of album
        ("artist", ct.c_char_p), # Name of album artist
        ("composer", ct.c_char_p), # Name of recording composer
        ("genre", ct.c_char_p), # Genre of album
        ("tracks", ct.POINTER(ct.c_uint32)), # The tracks in this album
        ("no_tracks", ct.c_uint32), # The number of tracks in this album
        ("next", ct.POINTER(album_t)), # Next album or NULL if last album
    ]

mtp.LIBMTP_new_track_t.restype = ct.POINTER(track_t)
mtp.LIBMTP_Get_Tracklisting_With_Callback.restype = ct.POINTER(track_t)
mtp.LIBMTP_Get_Trackmetadata.restype = ct.POINTER(track_t)
mtp.LIBMTP_new_playlist_t.restype = ct.POINTER(playlist_t)
mtp.LIBMTP_Get_Playlist_List.restype = ct.POINTER(playlist_t)
mtp.LIBMTP_Get_Playlist.restype = ct.POINTER(playlist_t)
mtp.LIBMTP_new_album_t.restype = ct.POINTER(album_t)
mtp.LIBMTP_Get_Album_List.restype = ct.POINTER(album_t)
mtp.LIBMTP_Get_Album.restype = ct.POINTER(album_t)

class allowed_values_t(ct.Structure) :
    # A data structure to hold allowed ranges of values
    _fields_ = \
        [
            ("u8max", ct.c_uint8),
            ("u8min", ct.c_uint8),
            ("u8step", ct.c_uint8),
            ("u8vals", ct.POINTER(ct.c_uint8)),
            ("i8max", ct.c_int8),
            ("i8min", ct.c_int8),
            ("i8step", ct.c_int8),
            ("i8vals", ct.POINTER(ct.c_int8)),
            ("u16max", ct.c_uint16),
            ("u16min", ct.c_uint16),
            ("u16step", ct.c_uint16),
            ("u16vals", ct.POINTER(ct.c_uint16)),
            ("16max", ct.c_int16),
            ("16min", ct.c_int16),
            ("16step", ct.c_int16),
            ("16vals", ct.POINTER(ct.c_int16)),
            ("u32max", ct.c_uint32),
            ("u32min", ct.c_uint32),
            ("u32step", ct.c_uint32),
            ("u32vals", ct.POINTER(ct.c_uint32)),
            ("i32max", ct.c_int32),
            ("i32min", ct.c_int32),
            ("i32step", ct.c_int32),
            ("i32vals", ct.POINTER(ct.c_int32)),
            ("u64max", ct.c_uint64),
            ("u64min", ct.c_uint64),
            ("u64step", ct.c_uint64),
            ("u64vals", ct.POINTER(ct.c_uint64)),
            ("i64max", ct.c_int64),
            ("i64min", ct.c_int64),
            ("i64step", ct.c_int64),
            ("i64vals", ct.POINTER(ct.c_int64)),
            ("num_entries", ct.c_uint16), # Number of entries in the vals array
            ("datatype", datatype_t), # The datatype specifying which of the above is used
            ("is_range", ct.c_int), # Non zero for range, 0 for enum
        ]
    use_fields = {}
    for \
        (datatype, bitsize, signed) \
    in \
        (
            (DATATYPE_INT8, 8, True),
            (DATATYPE_UINT8, 8, False),
            (DATATYPE_INT16, 16, True),
            (DATATYPE_UINT16, 16, False),
            (DATATYPE_INT32, 32, True),
            (DATATYPE_UINT32, 32, False),
            (DATATYPE_INT64, 64, True),
            (DATATYPE_UINT64, 64, False),
        ) \
    :
        use_fields[datatype] = {}
        for suffix in ("min", "max", "step", "vals") :
            use_fields[datatype][suffix] = "%s%d%s" % (("u", "i")[signed], bitsize, suffix)
        #end for
    #end for
    del datatype, bitsize, signed
#end allowed_values_t

#+
# Internal useful stuff
#-

class LeakProtect :
    # try to guard against memory leaks.

    def __init__(self, obj, free) :
        self.obj = obj
        self.free = free
    #end __init__

    def __enter__(self) :
        return self.obj
    #end __enter__

    def __exit__(self, exception_type, exception_value, traceback) :
        self.free(self.obj)
    #end __exit__

#end LeakProtect

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
    with LeakProtect(mtp.LIBMTP_new_file_t(), mtp.LIBMTP_destroy_file_t) as newfile :
        newfile.contents.filesize = os.stat(src).st_size
        newfile.contents.name = libc.strdup(destname.encode("utf-8"))
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
    #end with
    return result
#end common_send_file

def common_retrieve_to_folder(self, dest) :
    """retrieves the entire contents of this Device/Folder (and recursively of all
    its subfolders) into the specified destination directory on the host filesystem."""
    try :
        # only create leaf dir on demand, rest must already exist
        os.mkdir(dest)
    except OSError as Err :
        if Err.errno == errno.EEXIST :
            pass
        else :
            raise
        #end if
    #end try
    for item in self.get_children() :
        if isinstance(item, File) :
            item.retrieve_to_file(os.path.join(dest, item.name))
        elif isinstance(item, Folder) :
            item.retrieve_to_folder(os.path.join(dest, item.name))
        #end if
    #end for
#end common_retrieve_to_folder

def common_send_track \
  (
    device,
    src,
    parentid,
    destname,
    filetype,
    storageid = 0,
    title = None,
    artist = None,
    composer = None,
    genre = None,
    album = None,
    date = None,
    duration = 0, # seconds
    rating = 0,
  ) :
    with LeakProtect(mtp.LIBMTP_new_track_t(), mtp.LIBMTP_destroy_track_t) as track :
        track.contents.parent_id = parentid
        track.contents.storage_id = storageid
        for \
            (attr, value) \
        in \
            (
                ("title", title),
                ("artist", artist),
                ("composer", composer),
                ("genre", genre),
                ("album", album),
                ("date", date),
            ) \
        :
            if value != None :
                setattr(track.contents, attr, libc.strdup(value.encode("utf-8")))
                  # will be disposed by libmtp
            #end if
        #end for
        track.contents.duration = round(duration * 1000) # convert to milliseconds
        # tracknumber? samplerate? nochannels? wavecodec? bitrate? bitratetype?
        track.contents.filetype = filetype
        stat = os.stat(src)
        track.contents.filesize = stat.st_size
        track.contents.filename = libc.strdup(destname.encode("utf-8"))
        track.contents.modificationdate = round(stat.st_mtime) # I like to preserve this
        track.contents.rating = rating
        check_status \
          (
            mtp.LIBMTP_Send_Track_From_File
              (
                device.device,
                src.encode("utf-8"),
                track,
                None, # progress
                None # progress arg
              )
          )
        result = track.contents.item_id
    #end with
    return result
#end common_send_track

def common_create_playlist(device, parentid, name, storageid) :
    with LeakProtect(mtp.LIBMTP_new_playlist_t(), mtp.LIBMTP_destroy_playlist_t) as playlist :
        playlist.contents.parent_id = parentid
        playlist.contents.storage_id = storageid
        playlist.name = libc.strdup(name.encode("utf-8"))
        # initially no tracks
        check_status \
          (
            mtp.LIBMTP_Create_New_Playlist(device.device, playlist)
          )
        result = playlist.contents.playlist_id
    #end with
    return result
#end common_create_playlist

def common_create_album(device, parentid, name, storageid, artist = None, composer = None, genre = None) :
    with LeakProtect(mtp.LIBMTP_new_album_t(), mtp.LIBMTP_destroy_album_t) as album :
        album.contents.parent_id = parentid
        album.contents.storage_id = storageid
        album.contents.name = libc.strdup(name.encode("utf-8"))
        for \
            (attr, value) \
        in \
            (
                ("artist", artist),
                ("composer", composer),
                ("genre", genre),
            ) \
        :
            if value != None :
                setattr(album.contents, attr, libc.strdup(value.encode("utf-8")))
                  # will be disposed by libmtp
            #end if
        #end for
        # initially no tracks
        check_status \
          (
            mtp.LIBMTP_Create_New_Album(device.device, album)
          )
        result = album.contents.album_id
    #end with
    return result
#end common_create_album

def common_delete_object(device, objectid) :
    check_status \
      (
        mtp.LIBMTP_Delete_Object(device.device, objectid)
      )
    device.set_contents_changed()
#end common_delete_object

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
        self.update_seq = 1 # cache coherence check
        self.children_by_name = None
        self.descendants_by_id = None
        self.tracks_by_id = None
        self.playlists_by_id = None
        self.albums_by_id = None
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
        self.children_by_name = None
        self.descendants_by_id = None
        self.tracks_by_id = None
        self.playlists_by_id = None
        self.albums_by_id = None
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
        if self.descendants_by_id == None :
            self._cache_contents(common_get_files_and_folders(self, 0, 0))
        #end if
    #end _ensure_got_descendants

    def _ensure_got_children(self) :
        self._ensure_got_descendants()
    #end _ensure_got_children

    def _ensure_got_tracks(self) :
        self._ensure_got_descendants() # doesn't seem to work otherwise
        if self.tracks_by_id == None :
            self.tracks_by_id = {}
            track = mtp.LIBMTP_Get_Tracklisting_With_Callback(self.device, None, None)
            while bool(track) :
                self.tracks_by_id[track.contents.item_id] = Track(track.contents, self)
                next = track.contents.next
                mtp.LIBMTP_destroy_track_t(track)
                track = next
            #end while
        #end if
    #end _ensure_got_tracks

    def _ensure_got_playlists(self) :
        self._ensure_got_descendants() # doesn't seem to work otherwise
        if self.playlists_by_id == None :
            self.playlists_by_id = {}
            playlist = mtp.LIBMTP_Get_Playlist_List(self.device)
            while bool(playlist) :
                self.playlists_by_id[playlist.contents.playlist_id] = Playlist(playlist.contents, self)
                next = playlist.contents.next
                mtp.LIBMTP_destroy_playlist_t(playlist)
                playlist = next
            #end while
        #end if
    #end _ensure_got_playlists

    def _ensure_got_albums(self) :
        self._ensure_got_descendants() # doesn't seem to work otherwise
        if self.albums_by_id == None :
            self.albums_by_id = {}
            album = mtp.LIBMTP_Get_Album_List(self.device)
            while bool(album) :
                self.albums_by_id[album.contents.album_id] = Album(album.contents, self)
                next = album.contents.next
                mtp.LIBMTP_destroy_album_t(album)
                album = next
            #end while
        #end if
    #end _ensure_got_albums

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

    def get_tracks(self) :
        self._ensure_got_tracks()
        return list(self.tracks_by_id.values())
    #end get_tracks

    def get_track_by_id(self, id) :
        """returns a track on the device identified by device-wide ID,
        or None if not found."""
        self._ensure_got_tracks()
        return self.tracks_by_id.get(id)
    #end get_track_by_id

    def get_playlists(self) :
        self._ensure_got_playlists()
        return list(self.playlists_by_id.values())
    #end get_playlists

    def get_playlist_by_id(self, id) :
        """returns a playlist on the device identified by device-wide ID,
        or None if not found."""
        self._ensure_got_playlists()
        return self.playlists_by_id.get(id)
    #end get_playlist_by_id

    def get_albums(self) :
        self._ensure_got_albums()
        return list(self.albums_by_id.values())
    #end get_albumss

    def get_album_by_id(self, id) :
        """returns an album on the device identified by device-wide ID,
        or None if not found."""
        self._ensure_got_albums()
        return self.albums_by_id.get(id)
    #end get_album_by_id

    def send_file(self, src, destname) :
        """sends the specified file to the device under the specified name
        at the top level, and returns a new File object for it."""
        # should I allow default destname here as well?
        return common_send_file(self, src, 0, destname)
    #end send_file

    def retrieve_to_folder(self, dest) :
        common_retrieve_to_folder(self, dest)
    #end retrieve_to_folder

    def create_folder(self, name, storageid = 0) :
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
    #end create_folder

    def get_string_from_object(self, objectid, propertyid) :
        resultstr = mtp.LIBMTP_Get_String_From_Object(self.device, objectid, propertyid)
        if bool(resultstr) :
            result = bytes(ct.cast(resultstr, ct.c_char_p)).decode("utf-8")
            libc.free(resultstr)
        else :
            result = None
        #end if
        return result
    #end get_string_from_object

    def get_int_from_object(self, objectid, propertyid, bitsize, default) :
        return \
            (
                {
                    8 : mtp.LIBMTP_Get_u8_From_Object,
                    16 : mtp.LIBMTP_Get_u16_From_Object,
                    32 : mtp.LIBMTP_Get_u32_From_Object,
                    64 : mtp.LIBMTP_Get_u64_From_Object,
                }[bitsize]
                  (
                    self.device,
                    objectid,
                    propertyid,
                    default
                  )
            )
    #end get_int_from_object

    def set_object_int(self, objectid, propertyid, bitsize, newvalue) :
        check_status \
          (
                {
                    8 : mtp.LIBMTP_Set_Object_u8,
                    16 : mtp.LIBMTP_Set_Object_u16,
                    32 : mtp.LIBMTP_Set_Object_u32,
                    # 64 : mtp.LIBMTP_Set_Object_u64, # doesn't exist!?
                }[bitsize]
                  (
                    self.device,
                    objectid,
                    propertyid,
                    newvalue
                  )
          )
    #end set_object_int

    def get_string_property(self, propertyid) :
        return self.get_string_from_object(0, propertyid)
    #end get_string_property

    def get_int_property(self, propertyid, bitsize, default) :
        return self.get_int_from_object(0, propertyid, bitsize, default)
    #end get_int_property

    def set_object_string(self, objectid, propertyid, newvalue) :
        check_status \
          (
            mtp.LIBMTP_Set_Object_String
              (
                self.device,
                objectid,
                propertyid,
                newvalue.encode("utf-8")
              )
          )
    #end set_object_string

    def set_string_property(self, propertyid, newvalue) :
        self.set_object_string(0, propertyid, newvalue)
    #end set_string_property

    def set_int_property(self, propertyid, bitsize, newvalue) :
        self.set_object_int(0, propertyid, bitsize, newvalue)
    #end set_int_property

    def is_property_supported(self, propid, filetypeid) :
        return \
            (
                mtp.LIBMTP_Is_Property_Supported(self.device, propid, filetypeid)
            !=
                0
            )
    #end is_property_supported

    def get_allowed_property_values(self, propid, filetypeid) :
        with LeakProtect(ct.pointer(allowed_values_t()), mtp.LIBMTP_destroy_allowed_values_t) as allowed :
            check_status \
              (
                mtp.LIBMTP_Get_Allowed_Property_Values
                  (
                    self.device,
                    propid,
                    filetypeid,
                    allowed
                  )
              )
            result = {"datatype" : allowed.contents.datatype, "is_range" : allowed.contents.is_range != 0}
            use_fields = allowed.contents.use_fields[allowed.contents.datatype]
            if result["is_range"]  :
                result["min"] = getattr(allowed.contents, use_fields["min"])
                result["max"] = getattr(allowed.contents, use_fields["max"])
                result["step"] = getattr(allowed.contents, use_fields["step"])
            else :
                vals = getattr(allowed.contents, use_fields["vals"])
                result["vals"] = tuple(vals[i] for i in range(0, allowed.contents.num_entries))
            #end if
        #end with
        return result
    #end get_allowed_property_values

    def send_track \
      (
        self,
        src,
        destpath,
        filetype,
        storageid = 0,
        title = None,
        artist = None,
        composer = None,
        genre = None,
        album = None,
        date = None,
        duration = 0,
        rating = 0,
      ) :
        parentname, childname = os.path.split(destpath)
        parent = self.get_descendant_by_path(parentname)
        if parent == None :
            raise RuntimeError("cannot find parent folder %s" % parentname)
        #end if
        if len(childname) != 0 :
            child = parent.find_child_by_name(childname)
        else :
            child = None
        #end if
        if child != None :
            if not isinstance(child, Folder) and not isinstance(child, Device) :
                raise RuntimeError("destination track parent must be Folder")
            #end if
            parent = child
            destname = os.path.basename(src)
        elif len(childname) == 0 :
            destname = os.path.basename(src)
        else :
            destname = childname
        #end if
        trackid = common_send_track \
          (
            device = self,
            src = src,
            parentid = parent.item_id,
            destname = destname,
            filetype = filetype,
            storageid = storageid,
            title = title,
            artist = artist,
            composer = composer,
            genre = genre,
            album = album,
            date = date,
            duration = duration,
            rating = rating,
          )
        self.set_contents_changed()
        return self.get_track_by_id(trackid)
    #end send_track

    def create_playlist(self, name, storageid = 0) :
        playlistid = common_create_playlist(self, 0, name, storageid)
        self.set_contents_changed()
        return self.get_playlist_by_id(playlistid)
    #end create_playlist

    def create_album(self, name, storageid = 0, artist = None, composer = None, genre = None) :
        albumid = common_create_album(self, 0, name, storageid, artist, composer, genre)
        self.set_contents_changed()
        return self.get_album_by_id(albumid)
    #end create_album

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

    def set_name(self, newname) :
        """changes the name of the file."""
        with LeakProtect(mtp.LIBMTP_new_file_t(), mtp.LIBMTP_destroy_file_t) as item :
            item.contents.item_id = self.item_id
            item.contents.parent_id = self.parent_id
            check_status \
              (
                mtp.LIBMTP_Set_File_Name
                  (
                    self.device.device,
                    item,
                    newname.encode("utf-8")
                  )
              )
        #end with
        self.name = newname
        self.device.set_contents_changed()
    #end set_name

    def get_string_property(self, propertyid) :
        return self.device.get_string_from_object(self.item_id, propertyid)
    #end get_string_property

    def set_string_property(self, propertyid, newvalue) :
        self.device.set_object_string(self.item_id, propertyid, newvalue)
    #end set_string_property

    def get_int_property(self, propertyid, bitsize, default) :
        return self.device.get_int_from_object(self.item_id, propertyid, bitsize, default)
    #end get_int_property

    def set_int_property(self, propertyid, bitsize, newvalue) :
        self.device.set_object_int(self.item_id, propertyid, bitsize, newvalue)
    #end set_int_property

    def delete(self, delete_descendants = False) :
        """deletes the file on the device. You must not make any further use
        of this File object after this call."""
        # delete_descendants ignored, allowed for compatibility with Folder.delete
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

    def retrieve_to_folder(self, dest) :
        common_retrieve_to_folder(self, dest)
    #end retrieve_to_folder

    def send_file(self, src, destname = None) :
        """sends the specified file to the device under the specified name within
        this Folder, and returns a new File object for it."""
        if destname == None :
            destname = os.path.basename(src)
        #end if
        return common_send_file(self.device, src, self.item_id, destname)
    #end send_file

    def create_folder(self, name, storageid = 0) :
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
    #end create_folder

    def set_name(self, newname) :
        """changes the name of the folder."""
        with LeakProtect(mtp.LIBMTP_new_folder_t(), mtp.LIBMTP_destroy_folder_t) as item :
            item.contents.item_id = self.item_id
            item.contents.parent_id = self.parent_id
            check_status \
              (
                mtp.LIBMTP_Set_Folder_Name
                  (
                    self.device.device,
                    item,
                    newname.encode("utf-8")
                  )
              )
        #end with
        self.name = newname
        self.device.set_contents_changed()
    #end set_name

    def get_string_property(self, propertyid) :
        return self.device.get_string_from_object(self.item_id, propertyid)
    #end get_string_property

    def set_string_property(self, propertyid, newvalue) :
        self.device.set_object_string(self.item_id, propertyid, newvalue)
    #end set_string_property

    def get_int_property(self, propertyid, bitsize, default) :
        return self.device.get_int_from_object(self.item_id, propertyid, bitsize, default)
    #end get_int_property

    def set_int_property(self, propertyid, bitsize, newvalue) :
        self.device.set_object_int(self.item_id, propertyid, bitsize, newvalue)
    #end set_int_property

    def delete(self, delete_descendants = False) :
        """deletes the folder on the device. You must not make any further use
        of this Folder object (or any of its descendant File or Folder objects)
        after this call."""
        children = self.get_children()
        if len(children) != 0 and not delete_descendants :
            raise RuntimeError("folder is not empty")
        #end if
        if delete_descendants :
            for child in children :
                child.delete(delete_descendants)
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

    def send_track \
      (
        self,
        src,
        destname,
        filetype,
        storageid = 0,
        title = None,
        artist = None,
        composer = None,
        genre = None,
        album = None,
        date = None,
        duration = 0,
        rating = 0,
      ) :
        trackid = common_send_track \
          (
            device = self.device,
            src = src,
            parentid = self.item_id,
            destname = destname,
            filetype = filetype,
            storageid = storageid,
            title = title,
            artist = artist,
            composer = composer,
            genre = genre,
            album = album,
            date = date,
            duration = duration,
            rating = rating,
          )
        self.device.set_contents_changed()
        return self.device.get_track_by_id(trackid)
      #end send_track

    def create_playlist(self, name, storageid = 0) :
        playlistid = common_create_playlist(self.device, self.item_id, name, storageid)
        self.device.set_contents_changed()
        return self.device.get_playlist_by_id(playlistid)
    #end create_playlist

    def create_album(self, name, storageid = 0, artist = None, composer = None, genre = None) :
        albumid = common_create_album(self.device, self.item_id, name, storageid, artist, composer, genre)
        self.device.set_contents_changed()
        return self.device.get_album_by_id(albumid)
    #end create_album

#end Folder

class Track :
    """representation of a track on the device. Don't create these objects yourself,
    always get them from lookup or creation methods."""

    def __init__(self, t, device) :
        self.device = device
        for fieldname, fieldtype in track_t._fields_ :
            if fieldname != "next" :
                if fieldtype == ct.c_char_p :
                    fieldvalue = getattr(t, fieldname)
                    if fieldvalue != None :
                        setattr(self, fieldname, fieldvalue.decode("utf-8"))
                    #end if
                else :
                    setattr(self, fieldname, getattr(t, fieldname))
                #end if
            #end if
        #end for
    #end __init__

    def set_name(self, newname) :
        with \
            LeakProtect \
              (
                mtp.LIBMTP_Get_Trackmetadata(self.device.device, self.item_id),
                mtp.LIBMTP_destroy_track_t
              ) \
        as \
            track \
        :
            check_status \
              (
                mtp.LIBMTP_Set_Track_Name(self.device.device, track, newname.encode("utf-8"))
              )
        #end with
        self.name = newname
    #end set_name

    def delete(self) :
        common_delete_object(self.device, self.item_id)
        # make myself unusable:
        del self.name
        del self.item_id
    #end delete

    def __repr__(self) :
        return "<Track “%s”>" % self.filename
    #end __repr__

#end Track

class Playlist :
    """representation of a playlist on the device. Don't create these objects yourself,
    always get them from lookup or creation methods."""

    def __init__(self, p, device) :
        self.device = device
        self.item_id = p.playlist_id # consistent name
        self.name = p.name.decode("utf-8")
        for attr in ("parent_id", "storage_id", ) :
            setattr(self, attr, getattr(p, attr))
        #end for
        self.tracks = tuple(p.tracks[i] for i in range(0, p.no_tracks))
    #end __init__

    def _update_tracks(self, new_tracks) :
        with \
            LeakProtect \
              (
                mtp.LIBMTP_Get_Playlist(self.device.device, self.item_id),
                mtp.LIBMTP_destroy_playlist_t
              ) \
        as \
            p \
        :
            libc.free(p.contents.tracks)
            p.contents.no_tracks = len(new_tracks)
            p.contents.tracks = ct.cast(libc.malloc(p.contents.no_tracks * ct.sizeof(ct.c_uint32)), ct.POINTER(ct.c_uint32))
            for i in range(0, p.contents.no_tracks) :
                p.contents.tracks[i] = new_tracks[i]
            #end for
            check_status \
              (
                mtp.LIBMTP_Update_Playlist(self.device.device, p)
              )
        #end with
        self.tracks = new_tracks
    #end _update_tracks

    def get_tracks(self) :
        """returns a list of Track objects for the contents of this playlist."""
        return list(self.device.get_track_by_id(t) for t in self.tracks)
    #end get_tracks

    def set_tracks(self, new_tracks) :
        """sets the specified list of Track objects as the new contents of this playlist."""
        self._update_tracks(tuple(t.item_id for t in new_tracks))
    #end set_tracks

    def delete(self) :
        common_delete_object(self.device, self.item_id)
        # make myself unusable:
        del self.name
        del self.item_id
    #end delete

    def __repr__(self) :
        return "<Playlist “%s”>" % self.name
    #end __repr__

#end Playlist

class Album :
    """representation of an album on the device. Don't create these objects yourself,
    always get them from lookup or creation methods."""

    def __init__(self, a, device) :
        self.device = device
        self.item_id = a.album_id # consistent name
        for attr in ("parent_id", "storage_id", "name", "artist", "composer", "genre") :
            setattr(self, attr, getattr(a, attr).decode("utf-8"))
        #end for
        self.tracks = tuple(a.tracks[i] for i in range(0, a.no_tracks))
    #end __init__

    def _update_tracks(self, new_tracks) :
        with \
            LeakProtect \
              (
                mtp.LIBMTP_Get_Album(self.device.device, self.item_id),
                mtp.LIBMTP_destroy_album_t
              ) \
        as \
            p \
        :
            libc.free(p.contents.tracks)
            p.contents.no_tracks = len(new_tracks)
            p.contents.tracks = ct.cast(libc.malloc(p.contents.no_tracks * ct.sizeof(ct.c_uint32)), ct.POINTER(ct.c_uint32))
            for i in range(0, p.contents.no_tracks) :
                p.contents.tracks[i] = new_tracks[i]
            #end for
            check_status \
              (
                mtp.LIBMTP_Update_Album(self.device.device, p)
              )
        #end with
        self.tracks = new_tracks
    #end _update_tracks

    def get_tracks(self) :
        """returns a list of Track objects for the contents of this album."""
        return list(self.device.get_track_by_id(t) for t in self.tracks)
    #end get_tracks

    def set_tracks(self, new_tracks) :
        """sets the specified list of Track objects as the new contents of this album."""
        self._update_tracks(tuple(t.item_id for t in new_tracks))
    #end set_tracks

    def delete(self) :
        common_delete_object(self.device, self.item_id)
        # make myself unusable:
        del self.name
        del self.item_id
    #end delete

    def __repr__(self) :
        return "<Album “%s”>" % self.name
    #end __repr__

#end Album

def get_raw_devices() :
    """returns a list of all MTP devices detected on the system."""
    with LeakProtect(ct.POINTER(raw_device_t)(), libc.free) as devices :
        nr_devices = ct.c_int(0)
        check_status(mtp.LIBMTP_Detect_Raw_Devices(ct.byref(devices), ct.byref(nr_devices)))
        result = []
        for i in range(0, nr_devices.value) :
            result.append(RawDevice(devices[i]))
        #end for
    #end with
    return result
#end get_raw_devices

def get_property_description(propertyid) :
    return bytes(mtp.LIBMTP_Get_Property_Description(propertyid)).decode("utf-8")
#end get_property_description
