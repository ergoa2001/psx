class channel:
    def __init__(self):
        self.enable = 0
        self.direction = 0
        self.step = 0
        self.sync = 0
        self.trigger = 0
        self.chop = 0
        self.chop_dma_sz = 0
        self.chop_cpu_sz = 0
        self.sync = 0
        self.dummy = 0
        self.base = 0
        self.block_size = 0
        self.block_count = 0

    def transfer_size(self):
        if self.sync == 0:
            return self.block_size
        elif self.sync == 1:
            return self.block_count * self.block_size
        else:
            return 0

    def done(self):
        self.enable = 0
        self.trigger = 0

    def active(self):
        trigger = self.trigger if (self.sync == 0) else 1
        return True if ((self.enable != 0) and (trigger != 0)) else False

    def block_control(self):
        return (self.block_count << 16) | self.block_size

    def set_block_control(self, value):
        self.block_size = value & 0xFFFF
        self.block_count = (value >> 16) & 0xFFFF

    def set_base(self, value):
        self.base = value & 0xFFFFFF

    def control(self):
        r = 0
        r |= self.direction
        r |= self.step << 1
        r |= self.chop << 8
        r |= self.sync << 9
        r |= self.chop_dma_sz << 16
        r |= self.chop_cpu_sz << 20
        r |= self.enable << 24
        r |= self.trigger << 28
        r |= self.dummy << 29
        return r

    def set_control(self, value):
        self.direction = value & 1
        self.step = (value >> 1) & 1
        self.chop = (value >> 8) & 1
        self.sync = (value >> 9) & 3
        self.chop_dma_sz = (value >> 16) & 7
        self.chop_cpu_sz = (value >> 20) & 7
        self.enable = (value >> 24) & 1
        self.trigger = (value >> 28) & 1
        self.dummy = (value >> 29) & 3
