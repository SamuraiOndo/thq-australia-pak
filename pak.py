from ctypes import pointer
from fileinput import filename
from binary_reader import BinaryReader
import sys
from pathlib import Path
import os
import re

Mypath = Path(sys.argv[1])
directory = str(Mypath.resolve().parent)
Myfilename = Mypath.name
w = BinaryReader()
isFile = os.path.isfile(sys.argv[1])
unique_id = 0
stringTable = []
if(Mypath.is_file()):
    path = Mypath.open("rb")
    reader = BinaryReader(path.read())
    magic = reader.read_str(4)
    if (magic == "pack"):
        reader.set_endian(True) # big endian
    else:
        reader.set_endian(False) # little endian
    reader.seek(0x10)
    stringTablePoint = reader.read_uint32()
    filecount = reader.read_uint32()
    reader.seek(stringTablePoint)
    for i in range(filecount):
        stringTable.append(reader.read_str())
    reader.seek(0x18)
    for i in range(filecount):
        ID = reader.read_uint32()
        pointer = reader.read_uint32()
        size = reader.read_uint32()
        stay = reader.pos()
        reader.seek(pointer)
        output_path = directory / Path(Myfilename + ".unpack")
        output_path.mkdir(parents=True, exist_ok=True)
        filename = stringTable[i]
        print(filename)
        if ("/" in filename):
            embeddedfolder = os.path.dirname(filename)
            output_path2 = directory / Path(Myfilename + ".unpack" + "\\" + str(ID) + "_" + embeddedfolder)
            output_path2.mkdir(parents=True, exist_ok=True)
        output_file = output_path / (str(ID) + "_" + (filename))
        fe = open(output_file, "wb")
        fe.write(reader.read_bytes(size))
        fe.close()
        reader.seek(stay)
if (Mypath.is_dir()):
    newarchivename = sys.argv[1].replace('.unpack','')
    newarchive = open(newarchivename, "wb")
    listOfFiles = list()
    for (dirpath, dirnames, filenames) in os.walk(Mypath):
        listOfFiles += [os.path.join(dirpath, file) for file in filenames]
    def extract_int(s):
        return int(re.findall(r"\d+", s)[0])
    listOfFiles.sort(key=extract_int)
    if (sys.argv[2] == "1"):
        w.set_endian(False)
        w.write_str_fixed("kcap",4)
        w.write_uint32(1)
    if (sys.argv[2] == "0"):
        w.set_endian(True)
        w.write_str_fixed("pack",4)
        w.write_uint32(0)
    else:
        print("Not a valid argument")
    stringOffset = (len(listOfFiles) * 12 + 24)
    w.align(stringOffset)
    w.seek(0x10)
    w.write_uint32(stringOffset)
    w.write_uint32(len(listOfFiles))
    w.seek(stringOffset)
    for elem in listOfFiles:
        gettingReadyForNewFileName = elem.split("_", 1)
        newFileName = gettingReadyForNewFileName[1]
        print(newFileName)
        w.write_str(newFileName,True)
    endOfStringTable = w.pos()
    w.seek(8)
    w.write_uint32(endOfStringTable)
    w.seek(24)
    for elem in listOfFiles:
        gettingReadyForNewID = elem.split("_",1)
        ID = gettingReadyForNewID[0].replace((sys.argv[1] + '\\'),"")
        w.write_uint32(int(ID))
        stay = w.pos()
        w.seek(0,2)
        #howMuchPadding = w.pos() % 2048
        #if (howMuchPadding != 0):
            #w.pad(2048 - howMuchPadding)
        w.align(2048)
        newPointer = w.pos()
        file = open(elem, "rb")
        w.write_bytes(file.read())
        w.seek(stay)
        w.write_uint32(newPointer)
        w.write_uint32(os.path.getsize(elem))
        file.close()
    w.seek(0,2)
    newFileSize = w.pos()
    w.seek(12)
    w.write_uint32(newFileSize)
    newarchive.write(w.buffer())