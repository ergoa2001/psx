class ram:
    def __init__(self):
        self.data = [0xca]*2*1024*1024

    def load32(self, offset):
        return self.data[offset + 0] | (self.data[offset + 1] << 8) | (self.data[offset + 2] << 16) | (self.data[offset + 3] << 24)

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
