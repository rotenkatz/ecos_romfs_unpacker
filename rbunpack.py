#!/usr/bin/python

import sys, os

filename = sys.argv[1]
'''
typedef struct romfs_dirent {
    LONG    node;       // 4
    LONG    next;       // 8
    char    name[0];    // 8 + strlen(name) + 1
} romfs_dirent;         // Aligns to next 32 byte boundary
'''
class romfs_dirent():
    node = ""
    next = ""
    name = ""
    name_cl = ""

    def __init__(self, filep):
        node = filep.read(32)
        self.node = cInt(node[:4])
        self.next = cInt(node[4:8])
        self.name = node[8:32]
        self.name_cl = self.name.decode("ascii").rstrip(' \t\r\n\0')
        if self.name_cl == "..":
            self.name_cl = "__root"
        if self.name_cl == ".":
            self.name_cl = "__roota"

    def __str__(self):
        return "<fn %s node %s next %s>"%(self.name_cl, self.node, self.next)
'''
typedef struct romfs_node {
    LONG    mode;       // 4
    LONG    nlink;      // 8
    SHORT   uid;        // 10
    SHORT   gid;        // 12
    LONG    size;       // 16
    LONG    ctime;      // 20
    LONG    data_offset;    // 24
    char    pad[8];     // 32
} romfs_node;           // Next node begins here
'''

def cInt(a):
    return int.from_bytes(a, byteorder="little")

class romfs_node:
    mode = ""
    nlink = ""
    uid = ""
    gid = ""
    size = ""
    ctime= ""
    data_offset = ""
    pad = ""

    def __init__(self, filep):
        node = filep.read(32)
        self.mode = cInt(node[:4])
        self.nlink = cInt(node[4:8])
        self.uid = cInt(node[8:10])
        self.gid = cInt(node[10:12])
        self.size = cInt(node[12:16])
        self.ctime = cInt(node[16:20])
        self.data_offset = cInt(node[20:24])
        self.pad = str(node[24:32])

    def __str__(self):
        return "<node: %s,%s,%i,%i,%i,%i offset %s, pad %s>"\
               %(self.mode, self.nlink, self.uid, self.gid, self.size, self.ctime, self.data_offset, self.pad)
'''
typedef struct romfs_disk {
    LONG    magic;      // 4
    LONG    nodecount;  // 8
    LONG    disksize;   // 12
    LONG    dev_id;     // 16
    char    name[16];   // 32
} romfs_disk;           // Nodes start here
'''
class romfs_disk:
    magic = ""
    nodecount = ""
    disksize = ""
    dev_id = ""
    name = ""
    size = 32

    def __init__(self, filep):
        header = filep.read(32)
        self.magic = header[:4]
        self.nodecount = int.from_bytes(header[4:8], byteorder="little")
        self.disksize = int.from_bytes(header[8:12], byteorder="little")
        self.dev_id = header[12:16]
        self.name = header[16:32]


def read_data(input_file, offset, size):
    fb = open(input_file, 'rb')
    fb.seek(offset)
    buffer = fb.read(size)
    return buffer

if __name__ == "__main__":
    print("open file: %s"%filename)
    f = open(filename, "rb")

    romfs = romfs_disk(f)

    nodes={}
    lastnode = None
    for i in range(0, romfs.nodecount):
        lastnode = romfs_node(f)
        nodes[i] = lastnode

    namesDict = {}

    i=0
    while i < romfs.nodecount:
        name = romfs_dirent(f)
        i += 1
        #dirty hack for actual name entities counting. A . and .. shouldn't be counted.
        if name.node == 0:
            i -= 1
        namesDict[name.node] = name

    #unpack
    dirname = ""
    i=1
    while i:
        dirname = "_%s%s"%(i, filename)
        if not os.path.exists(dirname):
            os.makedirs(dirname)
            break
        if i > 1000:
            print("really?")
            break
        i += 1

    for key, val in nodes.items():
        data = read_data(filename, val.data_offset, val.size)
        savename = namesDict[key].name_cl
        with open(dirname+"/"+savename, 'wb') as f:
            f.write(data)


    savename = "deviation.bin"
    data = read_data(filename, lastnode.data_offset + lastnode.size, romfs.disksize)
    with open(dirname+"/"+savename, 'wb') as f:
            f.write(data)
    #binary
