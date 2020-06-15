from channel import channel

class dma:
    def __init__(self):
        self.control = 0x07654321
        self.irq_en = 0 # 0 or 1
        self.channel_irq_en = 0
        self.channel_irq_flags = 0
        self.force_irq = 0 # 0 or 1
        self.irq_dummy = 0

        self.channels = [channel(), channel(), channel(), channel(), channel(), channel(), channel()]


    def set_control(self, value):
        self.control = value

    def irq(self):
        return 1 if (self.force_irq or (self.irq_en and (self.channel_irq_flags & self.channel_irq_en))) else 0

    def channel(self, port):
        return self.channels[port]

    def interrupt(self):
        r = 0
        r |= self.irq_dummy
        r |= self.force_irq << 15
        r |= self.channel_irq_en << 16
        r |= self.irq_en << 23
        r |= self.channel_irq_flags << 24
        r |= self.irq() << 31
        return r

    def set_interrupt(self, value):
        self.irq_dummy = value & 0x3F
        self.force_irq = (value >> 15) & 1
        self.channel_irq_en = (value >> 16) & 0x7F
        self.irq_en = (value >> 23) & 1
        self.channel_irq_flags &= ~((value >> 24) & 0x3F)
