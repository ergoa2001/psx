from bus import bus
import time
import argparse

#parser = argparse.ArgumentParser()
#parser.add_argument('filename')
#args = parser.parse_args()
filename = "SCPH1001.BIN"
biossize = 512 * 1024

with open(filename, "rb") as fp:
    data = fp.read()
    if len(data) == biossize:
        print("BIOS read OK!")
    else:
        print("INVALID BIOS size")

bus = bus(data)
while bus.cpu.running:
    bus.clock()
