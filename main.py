import pygame
import pygame.gfxdraw
import numpy as np
from enum import Enum
import math

class Tool(Enum):
    PENCIL = 0
    BRUSH = 1
    LINE = 2
    RECTANGLE = 3
    CIRCLE = 4
    FILL = 5
    TEXT = 6
    SPRAY = 7
    ERASER = 8
    GRADIENT = 9

class DrawingEngine:
    def __init__(self, width=800, height=600):
        pygame.init()
        self.width = width
        self.height = height
        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption("FreakDraw 2")

        self.canvas = pygame.Surface((width, height))
        self.canvas.fill((255, 255, 255))

        self.layers = [pygame.Surface((width, height), pygame.SRCALPHA)]
        self.active_layer = 0
        
        self.ui_font = pygame.font.SysFont('Arial', 16)
        self.ui_color = (50, 50, 50)
        self.ui_panel_height = 60
        self.ui_panel = pygame.Surface((width, self.ui_panel_height))
        
        self.current_tool = Tool.PENCIL
        self.brush_size = 5
        self.color = (0, 0, 0)
        self.fill_color = None 
        self.alpha = 255
        self.gradient_start = (255, 0, 0)
        self.gradient_end = (0, 0, 255)

        self.start_pos = None
        self.drawing = False
        self.last_pos = None
        self.undo_stack = []
        self.redo_stack = []
        

        self.text_input = ""
        self.font_size = 24
        self.font = pygame.font.SysFont('Arial', self.font_size)
        
        self.clock = pygame.time.Clock()
        self.running = True
    
    def save_state(self):
        layer_copy = self.layers[self.active_layer].copy()
        self.undo_stack.append(layer_copy)
        self.redo_stack = []
    
    def undo(self):
        if len(self.undo_stack) > 0:
            self.redo_stack.append(self.layers[self.active_layer].copy())
            self.layers[self.active_layer] = self.undo_stack.pop()
    
    def redo(self):
        if len(self.redo_stack) > 0:
            self.undo_stack.append(self.layers[self.active_layer].copy())
            self.layers[self.active_layer] = self.redo_stack.pop()
    
    def add_layer(self):
        new_layer = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        self.layers.append(new_layer)
        self.active_layer = len(self.layers) - 1
    
    def remove_layer(self):
        if len(self.layers) > 1:
            self.layers.pop(self.active_layer)
            self.active_layer = min(self.active_layer, len(self.layers) - 1)
    
    def merge_down(self):
        if self.active_layer > 0:
            self.layers[self.active_layer - 1].blit(self.layers[self.active_layer], (0, 0))
            self.layers.pop(self.active_layer)
            self.active_layer -= 1
    
    def draw_ui(self):
        self.ui_panel.fill((220, 220, 220))
        

        tool_text = f"Tool: {self.current_tool.name} | Size: {self.brush_size} | Color: RGB{self.color}"
        tool_surf = self.ui_font.render(tool_text, True, self.ui_color)
        self.ui_panel.blit(tool_surf, (10, 10))
        
        layer_text = f"Layer: {self.active_layer + 1}/{len(self.layers)}"
        layer_surf = self.ui_font.render(layer_text, True, self.ui_color)
        self.ui_panel.blit(layer_surf, (10, 30))
        

        help_text = "Keys: 1-9=Tools, +/-=Size, U=Undo, R=Redo, L=New Layer, D=Delete Layer, M=Merge Down"
        help_surf = self.ui_font.render(help_text, True, self.ui_color)
        self.ui_panel.blit(help_surf, (self.width // 2 - help_surf.get_width() // 2, 30))

        pygame.draw.rect(self.ui_panel, self.color, (self.width - 40, 10, 30, 30))
        pygame.draw.rect(self.ui_panel, (0, 0, 0), (self.width - 40, 10, 30, 30), 1)
        
        self.screen.blit(self.ui_panel, (0, self.height - self.ui_panel_height))
    
    def draw_pencil(self, pos):
        if self.last_pos:
            pygame.draw.line(
                self.layers[self.active_layer],
                self.color + (self.alpha,),
                self.last_pos,
                pos,
                max(1, self.brush_size // 3)
            )
        else:
            pygame.draw.circle(
                self.layers[self.active_layer],
                self.color + (self.alpha,),
                pos,
                max(1, self.brush_size // 3)
            )
        self.last_pos = pos
    
    def draw_brush(self, pos):
        if self.last_pos:
            points = self.get_points_on_line(self.last_pos, pos)
            for point in points:
                pygame.draw.circle(
                    self.layers[self.active_layer],
                    self.color + (self.alpha,),
                    point,
                    self.brush_size // 2
                )
        else:
            pygame.draw.circle(
                self.layers[self.active_layer],
                self.color + (self.alpha,),
                pos,
                self.brush_size // 2
            )
        self.last_pos = pos
    
    def draw_spray(self, pos):
        num_particles = self.brush_size * 2
        for _ in range(num_particles):
            angle = np.random.uniform(0, 2 * np.pi)
            radius = np.random.uniform(0, self.brush_size)
            x = int(pos[0] + radius * np.cos(angle))
            y = int(pos[1] + radius * np.sin(angle))
            if 0 <= x < self.width and 0 <= y < self.height:
                spray_alpha = int(np.random.uniform(100, self.alpha))
                pygame.draw.circle(
                    self.layers[self.active_layer],
                    self.color + (spray_alpha,),
                    (x, y),
                    1
                )
    
    def draw_eraser(self, pos):
        if self.last_pos:
            points = self.get_points_on_line(self.last_pos, pos)
            for point in points:
                pygame.draw.circle(
                    self.layers[self.active_layer],
                    (0, 0, 0, 0),
                    point,
                    self.brush_size
                )
        else:
            pygame.draw.circle(
                self.layers[self.active_layer],
                (0, 0, 0, 0),
                pos,
                self.brush_size
            )
        self.last_pos = pos
    
    def start_shape(self, pos):
        self.start_pos = pos
        self.save_state()
    
    def draw_line_preview(self, pos):
        if self.start_pos:
            preview = self.layers[self.active_layer].copy()
            pygame.draw.line(
                preview,
                self.color + (self.alpha,),
                self.start_pos,
                pos,
                self.brush_size
            )
            return preview
        return None
    
    def draw_rectangle_preview(self, pos):
        if self.start_pos:
            preview = self.layers[self.active_layer].copy()
            rect = self.get_rect_from_points(self.start_pos, pos)
        
            if self.fill_color:
                pygame.draw.rect(
                    preview,
                    self.fill_color + (self.alpha,),
                    rect
                )
            
            pygame.draw.rect(
                preview,
                self.color + (self.alpha,),
                rect,
                max(1, self.brush_size // 2)
            )
            return preview
        return None
    
    def draw_circle_preview(self, pos):
        if self.start_pos:
            preview = self.layers[self.active_layer].copy()
            radius = int(math.hypot(pos[0] - self.start_pos[0], pos[1] - self.start_pos[1]))
        
            if self.fill_color:
                pygame.draw.circle(
                    preview,
                    self.fill_color + (self.alpha,),
                    self.start_pos,
                    radius
                )
            
            pygame.draw.circle(
                preview,
                self.color + (self.alpha,),
                self.start_pos,
                radius,
                max(1, self.brush_size // 2)
            )
            return preview
        return None
    
    def draw_gradient_preview(self, pos):
        if self.start_pos:
            preview = self.layers[self.active_layer].copy()
            dx = pos[0] - self.start_pos[0]
            dy = pos[1] - self.start_pos[1]
            distance = max(1, math.hypot(dx, dy))
            
            for x in range(min(self.start_pos[0], pos[0]), max(self.start_pos[0], pos[0])+1, 2):
                for y in range(min(self.start_pos[1], pos[1]), max(self.start_pos[1], pos[1])+1, 2):
                    t = ((x - self.start_pos[0]) * dx + (y - self.start_pos[1]) * dy) / (distance * distance)
                    t = max(0, min(1, t))

                    r = int(self.gradient_start[0] * (1 - t) + self.gradient_end[0] * t)
                    g = int(self.gradient_start[1] * (1 - t) + self.gradient_end[1] * t)
                    b = int(self.gradient_start[2] * (1 - t) + self.gradient_end[2] * t)
                    
                    pygame.draw.circle(preview, (r, g, b, self.alpha), (x, y), 1)
            
            return preview
        return None
    
    def finish_shape(self, pos):
        if self.start_pos:
            if self.current_tool == Tool.LINE:
                pygame.draw.line(
                    self.layers[self.active_layer],
                    self.color + (self.alpha,),
                    self.start_pos,
                    pos,
                    self.brush_size
                )
            elif self.current_tool == Tool.RECTANGLE:
                rect = self.get_rect_from_points(self.start_pos, pos)
                if self.fill_color:
                    pygame.draw.rect(
                        self.layers[self.active_layer],
                        self.fill_color + (self.alpha,),
                        rect
                    )
                pygame.draw.rect(
                    self.layers[self.active_layer],
                    self.color + (self.alpha,),
                    rect,
                    max(1, self.brush_size // 2)
                )
            elif self.current_tool == Tool.CIRCLE:
                radius = int(math.hypot(pos[0] - self.start_pos[0], pos[1] - self.start_pos[1]))
                if self.fill_color:
                    pygame.draw.circle(
                        self.layers[self.active_layer],
                        self.fill_color + (self.alpha,),
                        self.start_pos,
                        radius
                    )
                pygame.draw.circle(
                    self.layers[self.active_layer],
                    self.color + (self.alpha,),
                    self.start_pos,
                    radius,
                    max(1, self.brush_size // 2)
                )
            elif self.current_tool == Tool.GRADIENT:
                dx = pos[0] - self.start_pos[0]
                dy = pos[1] - self.start_pos[1]
                distance = max(1, math.hypot(dx, dy))
                
                for x in range(min(self.start_pos[0], pos[0]), max(self.start_pos[0], pos[0])+1):
                    for y in range(min(self.start_pos[1], pos[1]), max(self.start_pos[1], pos[1])+1):
                        t = ((x - self.start_pos[0]) * dx + (y - self.start_pos[1]) * dy) / (distance * distance)
                        t = max(0, min(1, t))
                        
                        r = int(self.gradient_start[0] * (1 - t) + self.gradient_end[0] * t)
                        g = int(self.gradient_start[1] * (1 - t) + self.gradient_end[1] * t)
                        b = int(self.gradient_start[2] * (1 - t) + self.gradient_end[2] * t)
                        
                        pygame.draw.circle(self.layers[self.active_layer], (r, g, b, self.alpha), (x, y), 1)
            
            self.start_pos = None
    
    def get_rect_from_points(self, start, end):
        x = min(start[0], end[0])
        y = min(start[1], end[1])
        w = abs(start[0] - end[0])
        h = abs(start[1] - end[1])
        return pygame.Rect(x, y, w, h)
    
    def get_points_on_line(self, start, end):
        points = []
        dx = abs(end[0] - start[0])
        dy = abs(end[1] - start[1])
        
        sx = 1 if start[0] < end[0] else -1
        sy = 1 if start[1] < end[1] else -1
        
        err = dx - dy
        
        x, y = start
        
        while True:
            points.append((x, y))
            if x == end[0] and y == end[1]:
                break
                
            e2 = 2 * err
            if e2 > -dy:
                if x == end[0]:
                    break
                err -= dy
                x += sx
            if e2 < dx:
                if y == end[1]:
                    break
                err += dx
                y += sy
                
        return points
    
    def flood_fill(self, pos):
        x, y = pos
        if not (0 <= x < self.width and 0 <= y < self.height):
            return

        target_color = tuple(self.layers[self.active_layer].get_at((x, y)))
        replacement_color = self.color + (self.alpha,)

        if target_color == replacement_color:
            return
        
        self.save_state()
        
    
        stack = [(x, y)]
        while stack:
            x, y = stack.pop()
            
            if not (0 <= x < self.width and 0 <= y < self.height):
                continue
                
            if tuple(self.layers[self.active_layer].get_at((x, y))) != target_color:
                continue
            
            self.layers[self.active_layer].set_at((x, y), replacement_color)
            
            stack.append((x + 1, y))
            stack.append((x - 1, y))
            stack.append((x, y + 1))
            stack.append((x, y - 1))
    
    def place_text(self, pos):
        if self.text_input:
            text_surf = self.font.render(self.text_input, True, self.color)
            self.layers[self.active_layer].blit(text_surf, pos)
            self.text_input = ""
    
    def handle_tool_selection(self, key):
        tool_map = {
            pygame.K_1: Tool.PENCIL,
            pygame.K_2: Tool.BRUSH,
            pygame.K_3: Tool.LINE,
            pygame.K_4: Tool.RECTANGLE,
            pygame.K_5: Tool.CIRCLE,
            pygame.K_6: Tool.FILL,
            pygame.K_7: Tool.TEXT,
            pygame.K_8: Tool.SPRAY,
            pygame.K_9: Tool.ERASER,
            pygame.K_0: Tool.GRADIENT
        }
        
        if key in tool_map:
            self.current_tool = tool_map[key]

    
    def handle_key_press(self, key):
        if key == pygame.K_u:
            self.undo()
        elif key == pygame.K_r:
            self.redo()
        elif key == pygame.K_l:
            self.add_layer()
        elif key == pygame.K_d:
            self.remove_layer()
        elif key == pygame.K_m:
            self.merge_down()
        elif key == pygame.K_PLUS or key == pygame.K_EQUALS:
            self.brush_size = min(100, self.brush_size + 1)
        elif key == pygame.K_MINUS:
            self.brush_size = max(1, self.brush_size - 1)
        elif key == pygame.K_c:
            colors = [(0, 0, 0), (255, 0, 0), (0, 255, 0), (0, 0, 255), 
                     (255, 255, 0), (255, 0, 255), (0, 255, 255), (255, 255, 255)]
            current_idx = colors.index(self.color) if self.color in colors else 0
            self.color = colors[(current_idx + 1) % len(colors)]
        elif key == pygame.K_f:
            if self.fill_color is None:
                self.fill_color = (255, 255, 255)
            else:
                self.fill_color = None
        elif key == pygame.K_s:
            self.save_drawing()
    
    def save_drawing(self):
        final_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        final_surface.fill((255, 255, 255))
        
        for layer in self.layers:
            final_surface.blit(layer, (0, 0))
        
        filename = f"drawing_{pygame.time.get_ticks()}.png"
        pygame.image.save(final_surface, filename)
        print(f"Drawing saved as {filename}")
    
    def run(self):

        while self.running:
            self.clock.tick(60)
            
            self.screen.fill((200, 200, 200))
            

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                
                elif event.type == pygame.KEYDOWN:
                    self.handle_tool_selection(event.key)

                    self.handle_key_press(event.key)
                    

                    if self.current_tool == Tool.TEXT:
                        if event.key == pygame.K_RETURN:
                            pass 
                        elif event.key == pygame.K_BACKSPACE:
                            self.text_input = self.text_input[:-1]
                        else:
                            if event.unicode.isprintable():
                                self.text_input += event.unicode
                
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        if event.pos[1] < self.height - self.ui_panel_height:
                            self.drawing = True
                            pos = event.pos
                            
                            if self.current_tool in [Tool.LINE, Tool.RECTANGLE, Tool.CIRCLE, Tool.GRADIENT]:
                                self.start_shape(pos)
                            elif self.current_tool == Tool.FILL:
                                self.flood_fill(pos)
                            elif self.current_tool == Tool.TEXT:
                                self.save_state()
                                self.place_text(pos)
                            else:
                                self.save_state()
                                self.last_pos = None
                                if self.current_tool == Tool.PENCIL:
                                    self.draw_pencil(pos)
                                elif self.current_tool == Tool.BRUSH:
                                    self.draw_brush(pos)
                                elif self.current_tool == Tool.SPRAY:
                                    self.draw_spray(pos)
                                elif self.current_tool == Tool.ERASER:
                                    self.draw_eraser(pos)
                
                elif event.type == pygame.MOUSEBUTTONUP:
                    if event.button == 1:
                        self.drawing = False
                        pos = event.pos
                        
    
                        if self.current_tool in [Tool.LINE, Tool.RECTANGLE, Tool.CIRCLE, Tool.GRADIENT]:
                            self.finish_shape(pos)
                        
                        self.last_pos = None
                
                elif event.type == pygame.MOUSEMOTION:
                    if self.drawing and event.pos[1] < self.height - self.ui_panel_height:
                        pos = event.pos
                        
                        if self.current_tool == Tool.PENCIL:
                            self.draw_pencil(pos)
                        elif self.current_tool == Tool.BRUSH:
                            self.draw_brush(pos)
                        elif self.current_tool == Tool.SPRAY:
                            self.draw_spray(pos)
                        elif self.current_tool == Tool.ERASER:
                            self.draw_eraser(pos)
            
            for y in range(0, self.height, 20):
                for x in range(0, self.width, 20):
                    color = (240, 240, 240) if (x // 20 + y // 20) % 2 == 0 else (220, 220, 220)
                    pygame.draw.rect(self.screen, color, (x, y, 20, 20))
            

            for layer in self.layers:
                self.screen.blit(layer, (0, 0))
            
            mouse_pos = pygame.mouse.get_pos()
            if self.drawing and mouse_pos[1] < self.height - self.ui_panel_height:
                preview = None
                if self.current_tool == Tool.LINE:
                    preview = self.draw_line_preview(mouse_pos)
                elif self.current_tool == Tool.RECTANGLE:
                    preview = self.draw_rectangle_preview(mouse_pos)
                elif self.current_tool == Tool.CIRCLE:
                    preview = self.draw_circle_preview(mouse_pos)
                elif self.current_tool == Tool.GRADIENT:
                    preview = self.draw_gradient_preview(mouse_pos)
                
                if preview:
                    self.screen.blit(preview, (0, 0))
            
            self.draw_ui()
            
            if self.current_tool == Tool.TEXT and self.text_input:
                text_surf = self.font.render(self.text_input, True, self.color)
                mouse_pos = pygame.mouse.get_pos()
                if mouse_pos[1] < self.height - self.ui_panel_height:
                    self.screen.blit(text_surf, mouse_pos)
            
            pygame.display.flip()
        
        pygame.quit()

if __name__ == "__main__":
    engine = DrawingEngine(1024, 768)
    engine.run()
