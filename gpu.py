from renderer import renderer

class gpu:
    def __init__(self):
        self.bus = 0
        self.renderer = 0
        self.page_base_x = 0
        self.page_base_y = 0
        self.semi_transparency = 0
        self.texture_depth = 0
        self.dithering = 0
        self.draw_to_display = 0
        self.force_set_mask_bit = 0
        self.preserve_masked_pixels = 0
        self.field = 1
        self.texture_disable = 0
        self.hres = 0
        self.vres = 0
        self.vmode = 0
        self.display_depth = 0
        self.interlaced = 0
        self.display_disabled = 1
        self.interrupt = 0
        self.dma_direction = 0

        self.rectangle_texture_x_flip = 0
        self.rectangle_texture_y_flip = 0

        self.texture_window_x_mask = 0
        self.texture_window_y_mask = 0
        self.texture_window_x_offset = 0
        self.texture_window_y_offset = 0
        self.drawing_area_left = 0
        self.drawing_area_top = 0
        self.drawing_area_right = 0
        self.drawing_area_bottom = 0
        self.drawing_x_offset = 0
        self.drawing_y_offset = 0
        self.display_vram_x_start = 0
        self.display_vram_y_start = 0
        self.display_horiz_start = 0x200
        self.display_horiz_end = 0xC00
        self.display_line_start = 0x10
        self.display_line_end = 0x100

        self.gp0_opcodes = {0: (1, self.gp0_nop), 1: (1, self.gp0_clear_cache), 40: (5, self.gp0_quad_mono_opaque), 44: (9, self.gp0_quad_texture_blend_opaque), 48: (6, self.gp0_triangle_shaded_opaque), 56: (8, self.gp0_quad_shaded_opaque), 160: (3, self.gp0_image_load), 192: (3, self.gp0_image_store), 225: (1, self.gp0_draw_mode), 226: (1, self.gp0_texture_window), 227: (1, self.gp0_drawing_area_top_left), 228: (1, self.gp0_drawing_area_bottom_right), 229: (1, self.gp0_drawing_offset), 230: (1, self.gp0_mask_bit_setting)}
        self.gp0_mode = 0 # 0 is Command, 1 is ImageLoad

        self.gp0_command = [0] * 12
        self.gp0_command_method = None
        self.gp0_words_remaining = 0
        self.gp0_command_len = 0

    def link_bus_renderer(self, bus, renderer):
        self.bus = bus
        self.renderer = renderer

    def gp0_clear(self):
        self.gp0_command_len = 0

    def gp0_push_word(self, word):
        if self.gp0_command_len < 12:
            self.gp0_command[self.gp0_command_len] = word
            self.gp0_command_len += 1

    def read(self):
        return 0

    def status(self):
        r = 0
        r |= self.page_base_x << 0
        r |= self.page_base_y << 4
        r |= self.semi_transparency << 5
        r |= self.texture_depth << 7
        r |= self.dithering << 9
        r |= self.draw_to_display << 10
        r |= self.force_set_mask_bit << 11
        r |= self.preserve_masked_pixels << 12
        r |= self.field << 13
        r |= self.texture_disable << 15
        r |= self.hr << 16
        #r |= self.vres << 19
        r |= self.vmode << 20
        r |= self.display_depth << 21
        r |= self.interlaced << 22
        r |= self.display_disabled << 23
        r |= self.interrupt << 24
        r |= 1 << 26
        r |= 1 << 27
        r |= 1 << 28
        r |= self.dma_direction << 29
        r |= 0 << 31
        if self.dma_direction == 0:
            dma_request = 0
        elif self.dma_direction == 1:
            dma_request = 1
        elif self.dma_direction == 2:
            dma_request = (r >> 28) & 1
        elif self.dma_direction == 3:
            dma_request = (r >> 27) & 1
        r |= dma_request << 25
        return r

    def gp0(self, value):
        if self.gp0_words_remaining == 0:
            opcode = (value >> 24) & 0xFF
            if opcode in self.gp0_opcodes:
                self.gp0_words_remaining, self.gp0_command_method = self.gp0_opcodes[opcode]
                print("HANDLED GP0 COMMAND", hex(value))
            else:
                self.gp0_words_remaining = 1
                self.gp0_command_method = self.gp0_nop
                print("UNHANDLED GP0 COMMAND", hex(value))
            self.gp0_clear()
        self.gp0_words_remaining -= 1
        if self.gp0_mode == 0:
            self.gp0_push_word(value)
            if self.gp0_words_remaining == 0:
                self.gp0_command_method()
        else:
            if self.gp0_words_remaining == 0:
                self.gp0_mode = 0


    def gp1(self, value):
        opcode = (value >> 24) & 0xFF
        if opcode == 0x00:
            self.gp1_reset(value)
        elif opcode == 0x01:
            self.gp1_reset_command_buffer()
        elif opcode == 0x02:
            self.gp1_acknowledge_irq()
        elif opcode == 0x03:
            self.gp1_display_enable(value)
        elif opcode == 0x04:
            self.gp1_dma_direction(value)
        elif opcode == 0x05:
            self.gp1_display_vram_start(value)
        elif opcode == 0x06:
            self.gp1_display_horizontal_range(value)
        elif opcode == 0x07:
            self.gp1_display_vertical_range(value)
        elif opcode == 0x08:
            self.gp1_display_mode(value)
        else:
            print("UNHANDLED GP1 COMMAND", hex(value))

    def gp0_nop(self):
        pass

    def gp0_clear_cache(self):
        pass

    def gp0_quad_mono_opaque(self):
        print(self.gp0_command)
        positions = [self.renderer.position_from_gp0(self.gp0_command[1]), self.renderer.position_from_gp0(self.gp0_command[2]), self.renderer.position_from_gp0(self.gp0_command[3]), self.renderer.position_from_gp0(self.gp0_command[4])]
        color = self.renderer.color_from_gp0(self.gp0_command[0])
        colors = [color]*4
        self.renderer.push_quad(positions, colors)
        print(positions, colors)
        print("DRAWING QUAD")

    def gp0_quad_texture_blend_opaque(self):
        #print(self.gp0_command)
        #positions = [self.renderer.position_from_gp0(self.gp0_command[1]), self.renderer.position_from_gp0(self.gp0_command[3]), self.renderer.position_from_gp0(self.gp0_command[5]), self.renderer.position_from_gp0(self.gp0_command[7])]
        #colors = [(0x80, 0x00, 0x00), (0x80, 0x00, 0x00), (0x80, 0x00, 0x00), (0x80, 0x00, 0x00)]
        #self.renderer.push_quad(positions, colors)
        #print(positions, colors)
        print("DRAW QUAD TEXTURE BLENDING")

    def gp0_triangle_shaded_opaque(self):
        print(self.gp0_command)
        positions = [self.renderer.position_from_gp0(self.gp0_command[1]), self.renderer.position_from_gp0(self.gp0_command[3]), self.renderer.position_from_gp0(self.gp0_command[5])]
        colors = [self.renderer.color_from_gp0(self.gp0_command[0]), self.renderer.color_from_gp0(self.gp0_command[2]), self.renderer.color_from_gp0(self.gp0_command[4])]
        self.renderer.push_triangle(positions, colors)
        print(positions, colors)
        print("DRAWING TRIANGLE")


    def gp0_quad_shaded_opaque(self):
        #print(self.gp0_command)
        #positions = [self.renderer.position_from_gp0(self.gp0_command[1]), self.renderer.position_from_gp0(self.gp0_command[3]), self.renderer.position_from_gp0(self.gp0_command[5]), self.renderer.position_from_gp0(self.gp0_command[7])]
        #colors = [self.renderer.color_from_gp0(self.gp0_command[0]), self.renderer.color_from_gp0(self.gp0_command[2]), self.renderer.color_from_gp0(self.gp0_command[4]), self.renderer.color_from_gp0(self.gp0_command[6])]
        #self.renderer.push_quad(positions, colors)
        #print(positions, colors)
        print("DRAW QUAD SHADED")

    def gp0_image_load(self):
        res = self.gp0_command[2]
        width = res & 0xFFFF
        height = (res >> 16) & 0xFFFF
        imgsize = width * height
        imgsize = (imgsize + 1) & ~1
        self.gp0_words_remaining = imgsize // 2
        print("IMG LOAD", self.gp0_words_remaining)
        self.gp0_mode = 1 # Image load mode

    def gp0_image_store(self):
        res = self.gp0_command[2]
        width = res & 0xFFFF
        height = res >> 16
        print("UNHANDLED IMAGE STORE", width, height)

    def gp0_draw_mode(self):
        value = self.gp0_command[0]
        self.page_base_x = value & 0xF
        self.page_base_y = (value >> 4) & 1
        self.semi_transparency = (value >> 5) & 3
        self.texture_depth = (value >> 7) & 3
        self.dithering = (value >> 9) & 1
        self.draw_to_display = (value >> 10) & 1
        self.texture_disable = (value >> 11) & 1
        self.rectangle_texture_x_flip = (value >> 12) & 1
        self.rectangle_texture_y_flip = (value >> 13) & 1

    def gp0_texture_window(self):
        value = self.gp0_command[0]
        self.texture_window_x_mask = value & 0x1F
        self.texture_window_y_mask = (value >> 5) & 0x1F
        self.texture_window_x_offset = (value >> 10) & 0x1F
        self.texture_window_y_offset = (value >> 15) & 0x1F

    def gp0_drawing_area_top_left(self):
        value = self.gp0_command[0]
        self.drawing_area_top = (value >> 10) & 0x3FF
        self.drawing_area_left = value & 0x3FF

    def gp0_drawing_area_bottom_right(self):
        value = self.gp0_command[0]
        self.drawing_area_bottom = (value >> 10) & 0x3FF
        self.drawing_area_right = value & 0x3FF

    def gp0_drawing_offset(self):
        value = self.gp0_command[0]
        self.drawing_x_offset = (((((value & 0x7FF) << 5) & 0xFFFF) ^ 0x8000) - 0x8000) >> 5
        self.drawing_y_offset = ((((((value >> 11) & 0x7FF) << 5) & 0xFFFF) ^ 0x8000) - 0x8000) >> 5
        self.renderer.display()

    def gp0_mask_bit_setting(self):
        value = self.gp0_command[0]
        self.force_set_mask_bit = value & 1
        self.preserve_masked_pixels = value & 2

    def gp1_reset(self, value):
        self.page_base_x = 0
        self.page_base_y = 0
        self.semi_transparency = 0
        self.texture_depth = 0
        self.texture_window_x_mask = 0
        self.texture_window_y_mask = 0
        self.texture_window_x_offset = 0
        self.texture_window_y_offset = 0
        self.dithering = 0
        self.draw_to_display = 0
        self.texture_disable = 0
        self.rectangle_texture_x_flip = 0
        self.rectangle_texture_y_flip = 0
        self.drawing_area_left = 0
        self.drawing_area_top = 0
        self.drawing_area_right = 0
        self.drawing_area_bottom = 0
        self.drawing_x_offset = 0
        self.drawing_y_offset = 0
        self.force_set_mask_bit = 0
        self.preserve_masked_pixels = 0
        self.dma_direction = 0
        self.display_disabled = 1
        self.display_vram_x_start = 0
        self.display_vram_y_start = 0
        self.hres = 0
        self.vres = 0
        self.vmode = 0
        self.interlaced = 0
        self.display_horiz_start = 0x200
        self.display_horiz_end = 0xC00
        self.display_line_start = 0x10
        self.display_line_end = 0x100
        self.display_depth = 0
        self.gp1_reset_command_buffer()

    def gp1_reset_command_buffer(self):
        self.gp0_clear()
        self.gp0_words_remaining = 0
        self.gp0_mode = 0

    def gp1_acknowledge_irq(self):
        self.interrupt = 0

    def gp1_display_enable(self, value):
        self.display_disabled = value & 1

    def gp1_dma_direction(self, value):
        self.dma_direction = value & 3

    def gp1_display_vram_start(self, value):
        self.display_vram_x_start = value & 0x3FE
        self.display_vram_y_start = (value >> 10) & 0x1FF

    def gp1_display_horizontal_range(self, value):
        self.display_horiz_start = value & 0xFFF
        self.display_horiz_end = (value >> 12) & 0xFFF

    def gp1_display_vertical_range(self, value):
        self.display_line_start = value & 0x3FF
        self.display_line_end = (value >> 10) & 0x3FF

    def gp1_display_mode(self, value):
        self.hres = ((value >> 6) & 1) | ((value & 3) << 1)
        self.vres = (value >> 2) & 1
        self.vmode = (value >> 3) & 1
        self.display_depth = (value >> 4) & 1
        self.interlaced = (value >> 5) & 1
        if value & 0x80:
            print("UNSUPPORTED DISPLAY MODE", hex(value))
