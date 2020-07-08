from cpu import cpu
from bios import bios
from ram import ram
from dma import dma
from gpu import gpu
from renderer import renderer

class bus:
    def __init__(self, data):
        self.data = bytearray(data)
        self.dma = dma()
        self.gpu = gpu()
        self.debug = False
        self.cpu = cpu(self, self.data)
        self.ramrange = (0x00000000, 2*1024*1024)
        self.expansion1 = (0x1F000000, 512*1024)
        self.biosrange = (0x1FC00000, 512*1024)
        self.memcontrol = (0x1F801000, 36)
        self.ramsize = (0x1F801060, 4)
        self.irqcontrol = (0x1F801070, 8)
        self.spurange = (0x1F801C00, 640)
        self.expansion2 = (0x1F802000, 66)
        self.cachecontrol = (0xFFFE0130, 4)
        self.timerrange = (0x1F801100, 0x30)
        self.dmarange = (0x1F801080, 0x80)
        self.gpurange = (0x1F801810, 8)
        self.timerrange = (0x1F801100, 0x30)
        self.regionmask = [0xFFFFFFFF, 0xFFFFFFFF, 0xFFFFFFFF, 0xFFFFFFFF, 0x7FFFFFFF, 0x1FFFFFFF, 0xFFFFFFFF, 0xFFFFFFFF]
        self.bios = bios(self.data)
        self.ram = ram()
        self.renderer = renderer()
        self.gpu.link_bus_renderer(self, self.renderer)
        self.renderer.link_bus(self)




    def clock(self):
        self.cpu.clock()

    def map_addr(self, addr, srange):
        if addr >= srange[0] and addr < (srange[0] + srange[1]):
            return addr - srange[0]
        else:
            return None

    def mask_region(self, addr):
        return addr & self.regionmask[addr >> 29]

    def dma_reg(self, offset):
        major = (offset & 0x70) >> 4
        minor = offset & 0xF

        if major in (0, 1, 2, 3, 4, 5, 6):
            channel = self.dma.channel(major)
            if minor == 0:
                return channel.base
            elif minor == 4:
                return channel.block_control()
            elif minor == 8:
                return channel.control()
            else:
                print("UNHANDLED DMA READ AT", hex(offset))
                return
        elif major == 7:
            if minor == 0:
                return self.dma.control
            elif minor == 4:
                return self.dma.interrupt()
            print("UNHANDLED DMA READ AT", hex(offset))
            return
        print("UNHANDLED DMA READ AT", hex(offset))

    def set_dma_reg(self, offset, value):
        major = (offset & 0x70) >> 4
        minor = offset & 0xF
        active_port = None
        if major in (0, 1, 2, 3, 4, 5, 6):
            channel = self.dma.channel(major)
            if minor == 0:
                channel.set_base(value)
            elif minor == 4:
                channel.set_block_control(value)
            elif minor == 8:
                channel.set_control(value)
            else:
                print("UNHANDLED DMA WRITE", hex(offset), hex(value))
            if channel.active():
                active_port = major
            else:
                active_port = None
        elif major == 7:
            if minor == 0:
                self.dma.set_control(value)
            elif minor == 4:
                self.dma.set_interrupt(value)
            else:
                print("UNHANDLED DMA WRITE", hex(offset), hex(value))
        if major == active_port:
            self.do_dma(major)

    def do_dma(self, port):
        if self.dma.channel(port).sync == 2:
            self.do_dma_linked_list(port)
        else:
            self.do_dma_block(port)

    def do_dma_linked_list(self, port):
        channel = self.dma.channel(port)
        addr = channel.base & 0x1FFFFC
        print("DMA" + str(port), "chcr=" + str(hex(channel.control())), "madr=" + str(hex(channel.base)), "bcr=")
        if channel.direction == 0:
            print("INVALID DMA DIRECTION FOR LINKED LIST MODE")
            quit()
        else:
            print("LINKED LIST", hex(addr), port, "FromRam")
        if port != 2:
            print("ATTEMPTED LINKED LIST DMA ON PORT", port)
            quit()

        doingdma = True
        while doingdma:
            header = self.ram.load32(addr)
            remsz = header >> 24
            while remsz > 0:
                addr = (addr + 4) & 0x1FFFFC
                command = self.ram.load32(addr)
                self.gpu.gp0(command)
                remsz -= 1
            if header & 0x800000:
                doingdma = False
            addr = header & 0x1FFFFC
        channel.done()

    def do_dma_block(self, port):
        channel = self.dma.channel(port)
        increment = 4 if (channel.step == 0) else -4
        addr = channel.base
        remsz = channel.transfer_size()
        print("DMA" + str(port), "chcr=" + str(hex(channel.control())), "madr=" + str(hex(channel.base)), "bcr=")
        print("BLOCK", hex(addr), remsz, port, "ToRam" if (channel.direction == 0) else "FromRam")
        while remsz > 0:
            cur_addr = addr & 0x1FFFFC
            if channel.direction == 0: #1
                if port == 6:
                    if remsz == 1:
                        src_word = 0xFFFFFF
                    else:
                        src_word = ((addr - 4) & 0xFFFFFFFF) & 0x1FFFFF
                else:
                    print("UNHANDLED DMA SOURCE PORT", hex(port))
                    quit()
                self.ram.store32(cur_addr, src_word)
            else:
                src_word = self.ram.load32(cur_addr)
                if port == 2:
                    self.gpu.gp0(src_word)
                else:
                    print("UNHANDLED DMA DESTINATION PORT", hex(port))
            addr = (addr + increment) & 0xFFFFFFFF
            remsz -= 1
        channel.done()


    def load32(self, addr):
        addr_abs = self.mask_region(addr)
        if addr_abs % 4 != 0:
            print("UNALIGNED LOAD32 ADDRESS", hex(addr_abs))
            return
        if self.map_addr(addr_abs, self.biosrange) != None:
            offset = self.map_addr(addr_abs, self.biosrange)
            return self.bios.load32(offset)
        elif self.map_addr(addr_abs, self.ramrange) != None:
            offset = self.map_addr(addr_abs, self.ramrange)
            return self.ram.load32(offset)
        elif self.map_addr(addr_abs, self.irqcontrol) != None:
            offset = self.map_addr(addr_abs, self.irqcontrol)
            print("IRQ CONTROL READ", hex(offset))
            return 0
        elif self.map_addr(addr_abs, self.dmarange) != None:
            offset = self.map_addr(addr_abs, self.dmarange)
            return self.dma_reg(offset)
        elif self.map_addr(addr_abs, self.gpurange) != None:
            offset = self.map_addr(addr_abs, self.gpurange)
            if offset == 0:
                return self.gpu.read()
            elif offset == 4:
                return 0x1C000000
            else:
                return 0
        elif self.map_addr(addr_abs, self.timerrange) != None:
            offset = self.map_addr(addr_abs, self.timerrange)
            return 0
        else:
            print("UNHANDLED FETCH32 AT ADDRESS", hex(addr))

    def load16(self, addr):
        addr_abs = self.mask_region(addr)
        if self.map_addr(addr_abs, self.spurange) != None:
            offset = self.map_addr(addr_abs, self.spurange)
            print("UNHANDLED READ FROM SPU REGISTER", hex(offset))
            return 0
        elif self.map_addr(addr_abs, self.ramrange) != None:
            offset = self.map_addr(addr_abs, self.ramrange)
            return self.ram.load16(offset)
        elif self.map_addr(addr_abs, self.irqcontrol) != None:
            offset = self.map_addr(addr_abs, self.irqcontrol)
            print("IRQ CONTROL READ", hex(offset))
            return 0
        print("UNHANDLED LOAD16 AT ADDRESS", hex(addr))

    def load8(self, addr):
        addr_abs = self.mask_region(addr)
        if self.map_addr(addr_abs, self.biosrange) != None:
            offset = self.map_addr(addr_abs, self.biosrange)
            return self.bios.load8(offset)
        elif self.map_addr(addr_abs, self.expansion1) != None:
            return 0xFF
        elif self.map_addr(addr_abs, self.ramrange) != None:
            offset = self.map_addr(addr_abs, self.ramrange)
            return self.ram.load8(offset)
        print("UNHANDLED LOAD8 AT ADDRESS", hex(addr_abs))


    def store32(self, addr, value):
        addr_abs = self.mask_region(addr)
        value &= 0xFFFFFFFF
        if addr_abs % 4 != 0:
            print("UNALIGNED STORE32 ADDRESS", hex(addr_abs))
            return
        if self.map_addr(addr_abs, self.memcontrol) != None:
            offset = self.map_addr(addr_abs, self.memcontrol)
            if offset == 0:
                if value != 0x1F000000:
                    print("BAD EXPANSION 1 BASE ADDRESS", hex(value))
            elif offset == 4:
                if value != 0x1F802000:
                    print("BAD EXPANSION 2 BASE ADDRESS", hex(value))
            else:
                print("UNHANDLED WRITE TO MEMCONTROL REGISTER")
            return
        elif self.map_addr(addr_abs, self.ramsize) != None:
            offset = self.map_addr(addr_abs, self.ramsize)
            return # ram_size
        elif self.map_addr(addr_abs, self.cachecontrol) != None:
            offset = self.map_addr(addr_abs, self.cachecontrol)
            return # cache control
        elif self.map_addr(addr_abs, self.ramrange) != None:
            offset = self.map_addr(addr_abs, self.ramrange)
            self.ram.store32(offset, value)
            return
        elif self.map_addr(addr_abs, self.irqcontrol) != None:
            offset = self.map_addr(addr_abs, self.irqcontrol)
            print("IRQ CONTROL", hex(offset), hex(value))
            return
        elif self.map_addr(addr_abs, self.dmarange) != None:
            offset = self.map_addr(addr_abs, self.dmarange)
            self.set_dma_reg(offset, value)
            return
        elif self.map_addr(addr_abs, self.gpurange) != None:
            offset = self.map_addr(addr_abs, self.gpurange)
            if offset == 0:
                self.gpu.gp0(value)
                if value == 0xe5000800:
                    self.debug = True
            elif offset == 4:
                self.gpu.gp1(value)
            else:
                print("GPU WRITE", hex(offset), hex(value))
            return
        elif self.map_addr(addr_abs, self.timerrange) != None:
            offset = self.map_addr(addr_abs, self.timerrange)
            print("UNHANDLED WRITE TO TIMER REGISTER", hex(offset), hex(value))
            return
        else:
            print("UNHANDLED STORE32 INTO ADDRESS", hex(addr), hex(value))
            return

    def store16(self, addr, value):
        if addr % 2 != 0:
            print("UNALIGNED STORE16 ADDRESS", hex(addr))
            return
        addr_abs = self.mask_region(addr)
        #value &= 0xFFFF
        if self.map_addr(addr_abs, self.spurange) != None:
            offset = self.map_addr(addr_abs, self.spurange)
            print("UNHANDLED WRITE TO SPU REGISTER", hex(addr))
            return
        elif self.map_addr(addr_abs, self.timerrange) != None:
            offset = self.map_addr(addr_abs, self.timerrange)
            print("UNHANDLED WRITE TO TIMER REGISTER", hex(offset))
            return
        elif self.map_addr(addr_abs, self.ramrange) != None:
            offset = self.map_addr(addr_abs, self.ramrange)
            self.ram.store16(offset, value)
            return
        elif self.map_addr(addr_abs, self.irqcontrol) != None:
            offset = self.map_addr(addr_abs, self.irqcontrol)
            print("IRQ CONTROL WRITE", hex(offset), hex(value))
            return
        print("UNHANDLED STORE16 INTO ADDRESS", hex(addr))

    def store8(self, addr, value):
        addr_abs = self.mask_region(addr)
        value &= 0xFF
        if self.map_addr(addr_abs, self.expansion2) != None:
            offset = self.map_addr(addr_abs, self.expansion2)
            print("UNHANDLED WRITE TO EXPANSION2 REGISTER", hex(offset))
            return
        elif self.map_addr(addr_abs, self.ramrange) != None:
            offset = self.map_addr(addr_abs, self.ramrange)
            self.ram.store8(offset, value)
            return
        print("UNHANDLED STORE8 INTO ADDRESS", hex(addr_abs))
