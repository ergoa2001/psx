class ram:
    def __init__(self):
        self.data = [0xca]*2*1024*1024 #0xca 

    def load32(self, offset):
        b0 = self.data[offset + 0]
        b1 = self.data[offset + 1]
        b2 = self.data[offset + 2]
        b3 = self.data[offset + 3]
        return b0 | (b1 << 8) | (b2 << 16) | (b3 << 24)

    def load16(self, offset):
        return self.data[offset + 0] | (self.data[offset + 1] << 8)

    def load8(self, offset):
        return self.data[offset]

    def store32(self, offset, value):
        self.data[offset + 0] = value & 0xFF
        self.data[offset + 1] = (value >> 8) & 0xFF
        self.data[offset + 2] = (value >> 16) & 0xFF
        self.data[offset + 3] = (value >> 24) & 0xFF

    def store16(self, offset, value):
        self.data[offset + 0] = value & 0xFF
        self.data[offset + 1] = (value >> 8) & 0xFF

    def store8(self, offset, value):
        self.data[offset] = value & 0xFF
