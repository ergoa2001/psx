class bios:
    def __init__(self, data):
        self.data = data

    def load32(self, offset):
        b0 = self.data[offset + 0]
        b1 = self.data[offset + 1]
        b2 = self.data[offset + 2]
        b3 = self.data[offset + 3]
        return b0 | (b1 << 8) | (b2 << 16) | (b3 << 24)

    def load8(self, offset):
        return self.data[offset]
