import math
import turtle
import copy

# Escape to pause
# Ctrl + D to enter edit mode
# Ctrl + Z to undo
# Ctrl + S to save a level. 
# Ctrl + I to import a level
# Ctrl + V to visualize pathfinding

# If it's too laggy, change max_dots
max_dots = -1

fps = 60

def wait_for_seconds(t):
    for i in range(0, int(t * 16)):
        yield

def wait_for_input():
    while len(input_manager.keys_down_this_frame) == 0:
        yield

def start_coroutine(coroutine):
    coroutines.append(coroutine)

def stop_coroutine(coroutine):
    coroutines.remove(coroutine)


class Component:
    def __init__(self):
        self.game_object = None

    def update(self):
        pass

    def start(self):
        pass

    def on_delete(self):
        pass


class Vector2:
    def __init__(self, x=0, y=0):
        self.x = x
        self.y = y

    def __add__(self, other):
        if isinstance(other, Vector2):
            return Vector2(self.x + other.x, self.y + other.y)
        else:
            return Vector2(self.x + other, self.y + other)

    def __sub__(self, other):
        if isinstance(other, Vector2):
            return Vector2(self.x - other.x, self.y - other.y)
        else:
            return Vector2(self.x - other, self.y - other)

    def __mul__(self, other):
        if isinstance(other, Vector2):
            return Vector2(self.x * other.x, self.y * other.y)
        else:
            return Vector2(self.x * other, self.y * other)

    def __truediv__(self, other):
        if isinstance(other, Vector2):
            return Vector2(self.x / other.x, self.y / other.y)
        return Vector2(self.x / other, self.y / other)

    def __eq__(self, other):
        if isinstance(other, Vector2):
            return self.x == other.x and self.y == other.y
        else:
            return None

    def __str__(self):
        return "(" + str(self.x) + ", " + str(self.y) + ")"

    def __hash__(self):
        return hash(self.x) + hash(self.y)

    def rotate(self, angle):
        rad = math.radians(angle)
        sin = math.sin(rad)
        cos = math.cos(rad)
        new_x = self.x * cos - self.y * sin
        new_y = self.x * sin + self.y * cos
        self.x = new_x
        self.y = new_y

    def magnitude(self):
        return (self.x ** 2 + self.y ** 2) ** 0.5


class Transform(Component):
    def __init__(self):
        super().__init__()
        self._parent = None
        self.children = []
        self.position = Vector2()
        self.rotation = 0
        self.scale = Vector2(1, 1)
        self.local_position = None
        self.local_scale = None
        self.local_rotation = None
        self.ignore_parent_scale = False

    def update(self):
        if self.parent is not None:
            rotated_pos = Vector2(self.local_position.x, self.local_position.y)
            rotated_pos.rotate(self.parent.rotation)
            self.position = self.parent.position + rotated_pos
            self.rotation = self.parent.rotation + self.local_rotation
            if not self.ignore_parent_scale:
                self.scale = self.parent.scale * self.local_scale

    @property
    def parent(self):
        return self._parent

    @parent.setter
    def parent(self, val: "Transform"):
        self._parent = val
        val.children.append(self)
        self.on_parent()

    @parent.deleter
    def parent(self):
        self._parent.children.remove(self)
        self._parent = None
        self.on_unparent()

    def on_parent(self):
        self.local_position = self.position
        self.local_scale = self.scale
        self.local_rotation = self.rotation

    def on_unparent(self):
        self.local_position = None
        self.local_scale = None
        self.local_rotation = None


class GameObject(Component):
    def __init__(self, position: Vector2 = None, scale: Vector2 = None, starting_comps=None):
        super().__init__()
        self.game_object = self
        self.components = []

        if position is None:
            position = Vector2()
        if scale is None:
            scale = Vector2(1, 1)
        if starting_comps is None:
            starting_comps = []

        self.transform = self.add_component(Transform())
        self.transform.position = position
        self.transform.scale = scale
        game_objects.append(self)

        for comp in starting_comps:
            self.add_component(comp)

    def destroy(self):
        if not (self in game_objects):
            return
        game_objects.remove(self)
        for comp in self.components:
            comp.on_delete()
        self.components.clear()
        for child in self.transform.children:
            child.game_object.destroy()
        self.transform.children.clear()

    def add_component(self, comp):
        self.components.append(comp)
        comp.game_object = self
        comp.start()
        return comp

    def get_component(self, comp_type):
        for comp in self.components:
            if isinstance(comp, comp_type):
                return comp

    def remove_component(self, comp):
        self.components.remove(comp)

    def update(self):
        for comp in self.components:
            comp.update()


class RenderObject(Component):
    def __init__(self):
        super().__init__()
        self.pen = turtle.Turtle()
        self.pen.hideturtle()
        self.pen.penup()
        self.pen.speed(0)
        self.sort_order = 0
        self.visible = True
        render_objects.append(self)

    def toggle_visibility(self):
        if self.visible:
            self.visible = False
        else:
            self.visible = True

    def render(self):
        self.pen.clear()
        if self.visible:
            self.pen.shapesize(stretch_len=self.game_object.transform.scale.x,
                               stretch_wid=self.game_object.transform.scale.y)
            self.pen.setheading(self.game_object.transform.rotation)
            self.pen.goto(self.game_object.transform.position.x, self.game_object.transform.position.y)
            self.stamp_action()

    def on_delete(self):
        super().on_delete()
        self.pen.clear()
        render_objects.remove(self)

    def stamp_action(self):
        pass


class Sprite(RenderObject):
    def __init__(self, shape="square", color="white", sort_order=0):
        super().__init__()
        self.shape = shape
        self.color = color
        self.sort_order = sort_order

    def stamp_action(self):
        super().stamp_action()
        self.pen.shape(self.shape)
        self.pen.color(self.color)
        self.pen.stamp()


class Text(RenderObject):
    def __init__(self, text=" ", color="black", font_size="54", font="arial"):
        self.text = text
        self.color = color
        self.font = font
        self.font_size = font_size
        super().__init__()

    def stamp_action(self):
        super().stamp_action()
        self.pen.color(self.color)
        self.pen.write(self.text, font=(self.font, self.font_size), align="center")


def angle_to_vector(angle):
    radian = math.radians(angle)
    return Vector2(math.cos(radian), math.sin(radian))


class Entity(Component):
    def __init__(self):
        super().__init__()
        self.move_input = Vector2()
        self.move_speed = 5
        self.dead = False
        self.active = True
        self.health = 1
        self.death_effect_color = "white"
        self.death_effect_scale = Vector2(2, 2)

    def collide(self):
        if self.active == False:
            return

    def start(self):
        super().start()

    def die(self):
        self.dead = True
        self.game_object.destroy()

    def update(self):
        if self.active == False:
            return
        self.game_object.transform.position.x += self.move_input.x * self.move_speed
        self.game_object.transform.position.y += self.move_input.y * self.move_speed


class BlackBars(Component):
    def __init__(self, dimensions):
        super().__init__()
        self.dimensions = dimensions

    def start(self):
        for i in range(0, 4):
            bar = GameObject()
            bar_sprite = bar.add_component(Sprite("square", "black"))
            bar_sprite.sort_order = 99
            bar_width = 40

            mult = 1
            if i % 2 == 0:
                mult = -1
            if i < 2:
                bar.transform.scale = Vector2(self.dimensions.x / 2, bar_width)
                bar.transform.position = Vector2(0, ((self.dimensions.y / 2) + bar_width * 10) * mult)
            else:
                bar.transform.scale = Vector2(bar_width, self.dimensions.y / 2)
                bar.transform.position = Vector2(((self.dimensions.x / 2) + bar_width * 10) * mult, 0)


class Lerp:
    def __init__(self, obj, attribute, target, speed):
        for lerp in lerps:
            if lerp.obj == obj and lerp.attribute == attribute:
                lerp.stop()
        lerps.append(self)
        self.timer = 0
        self.lerping = True
        self.target = target
        self.obj = obj
        self.attribute = attribute
        self.speed = speed

    def stop(self):
        self.timer = 0
        self.lerping = False
        lerps.remove(self)

    def update(self):
        if self.lerping:
            self.timer += (fps / 1000) / self.speed / 4
            new_val = getattr(self.obj, self.attribute)
            diff = self.target - new_val
            if "rotation" in self.attribute:
                diff = (diff + 180) % 360 - 180
            new_val += diff * self.timer
            setattr(self.obj, self.attribute, new_val)
            if self.timer >= 1:
                self.stop()


class Input:
    def __init__(self):
        screen.listen()
        self.keys = ["Up", "Down", "Left", "Right",
                     "Control_L", "Shift_L", "Escape"]

        self.keys_down = set()
        self.keys_down_this_frame = set()
        self.keys_up_this_frame = set()

        self.mouse_pos = Vector2()
        screen.getcanvas().bind("<Motion>", self.set_mouse_pos)
        self.mouse_button_left_down = False
        self.mouse_button_right_down = False
        screen.getcanvas().bind('<ButtonPress-1>', self.on_mouse_button_left_down)
        screen.getcanvas().bind('<ButtonRelease-1>', self.on_mouse_button_left_up)
        screen.getcanvas().bind('<ButtonPress-3>', self.on_mouse_button_right_down)
        screen.getcanvas().bind('<ButtonRelease-3>', self.on_mouse_button_right_up)
        screen.getcanvas().bind('<ButtonPress-2>', self.on_mouse_button_right_down)
        screen.getcanvas().bind('<ButtonRelease-2>', self.on_mouse_button_right_up)

        self.keys += collection.keyboard_layout
        self.keys += collection.numbers

        self.bind_keys()

    def on_mouse_button_left_down(self, event):
        self.mouse_button_left_down = True

    def on_mouse_button_left_up(self, event):
        self.mouse_button_left_down = False

    def on_mouse_button_right_down(self, event):
        self.mouse_button_right_down = True

    def on_mouse_button_right_up(self, event):
        self.mouse_button_right_down = False

    def set_mouse_pos(self, pos):
        w = screen.window_width()
        h = screen.window_height()
        self.mouse_pos.x = pos.x - w / 2
        self.mouse_pos.y = h / 2 - pos.y

    def late_update(self):
        self.keys_down_this_frame.clear()
        self.keys_up_this_frame.clear()

    def internal_down(self, key):
        self.keys_down.add(key)
        self.keys_down_this_frame.add(key)

    def internal_up(self, key):
        self.keys_down.discard(key)
        self.keys_up_this_frame.add(key)

    def get_key(self, k):
        if k in self.keys_down:
            return True
        else:
            return False

    def get_key_down(self, k):
        if k in self.keys_down_this_frame:
            return True
        else:
            return False

    def bind_keys(self):
        screen.listen()
        for key in self.keys:
            screen.onkeypress(lambda k=key: self.internal_down(k), key)
            screen.onkeyrelease(lambda k=key: self.internal_up(k), key)


class Collection:
    def __init__(self):
        self.numbers = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "0"]
        self.keyboard_layout = ["q", "w", "e", "r", "t", "y", "u", "i", "o", "p", "a", "s", "d", "f", "g", "h", "j",
                                "k", "l", "z", "x", "c", "v", "b", "n", "m"]
        self.tile_inputs = []
        self.tile_inputs.extend(self.numbers)
        self.tile_inputs.extend(self.keyboard_layout)
        self.vertex_sets = []
        self.vertex_sets.append(None)
        pipe = self.mirror([Vector2(-1, 0.75), Vector2(1, 0.75), "*"])
        self.vertex_sets.append(pipe)
        self.vertex_sets.append(self.rotate(pipe, 90))
        pipe_corner = [Vector2(-1, 0.75), Vector2(0.55, 0.75), Vector2(0.75, 0.55), Vector2(0.75, -1), "*",
                       Vector2(-1, -0.75), Vector2(-0.75, -1)]
        self.vertex_sets.append(pipe_corner)
        self.vertex_sets.append(self.rotate(pipe_corner, 90))
        self.vertex_sets.append(self.rotate(pipe_corner, 180))
        self.vertex_sets.append(self.rotate(pipe_corner, 270))
        pipe_cap = [Vector2(-1, 0.75), Vector2(0.75, 0.75), Vector2(0.75, -0.75), Vector2(-1, -0.75)]
        self.vertex_sets.append(pipe_cap)
        self.vertex_sets.append(self.rotate(pipe_cap, 90))
        self.vertex_sets.append(self.rotate(pipe_cap, 180))
        self.vertex_sets.append(self.rotate(pipe_cap, 270))
        thin_pipe = self.mirror([Vector2(-1, 0.5), Vector2(1, 0.5), "*"])
        self.vertex_sets.append(thin_pipe)
        self.vertex_sets.append(self.rotate(thin_pipe, 90))
        thin_pipe_corner = [Vector2(-1, 0.5), Vector2(0.5, 0.5), Vector2(0.5, -1), "*", Vector2(-1, -0.5),
                            Vector2(-0.5, -1)]
        self.vertex_sets.append(thin_pipe_corner)
        self.vertex_sets.append(self.rotate(thin_pipe_corner, 90))
        self.vertex_sets.append(self.rotate(thin_pipe_corner, 180))
        self.vertex_sets.append(self.rotate(thin_pipe_corner, 270))
        thin_pipe_cap = [Vector2(-1, 0.5), Vector2(0.5, 0.5), Vector2(0.5, -0.5), Vector2(-1, -0.5)]
        self.vertex_sets.append(thin_pipe_cap)
        self.vertex_sets.append(self.rotate(thin_pipe_cap, 90))
        self.vertex_sets.append(self.rotate(thin_pipe_cap, 180))
        self.vertex_sets.append(self.rotate(thin_pipe_cap, 270))
        wad = self.mirror([Vector2(-1, 0), Vector2(-1, 0.5), Vector2(-0.75, 0.75), Vector2(0.75, 0.75), Vector2(1, 0.5),
                           Vector2(1, 0)])
        self.vertex_sets.append(wad)
        self.vertex_sets.append(self.rotate(wad, 90))
        self.vertex_sets.append(None)

        self.air_tile_types = [0, 36, 35, 34, 33, 32]
        self.directions = [Vector2(0, 1), Vector2(0, -1), Vector2(1, 0), Vector2(-1, 0)]

    def mirror(self, vertex_set, vert=True, hor=False):
        half = []
        for i in range(0, len(vertex_set)):
            vertex = vertex_set[len(vertex_set) - 1 - i]
            if not isinstance(vertex, Vector2):
                half.append(vertex)
                continue
            new_pos = Vector2(vertex.x, vertex.y)
            if vert:
                new_pos.y = -vertex.y
            if hor:
                new_pos.x = -vertex.x
            half.append(new_pos)
        return vertex_set + half

    def rotate(self, vertex_set, angle):
        new_vertex_set = []
        for i in range(0, len(vertex_set)):
            vertex = vertex_set[len(vertex_set) - 1 - i]
            if isinstance(vertex, Vector2):
                new_vertex = Vector2(vertex.x, vertex.y)
                new_vertex.rotate(angle)
                new_vertex_set.append(new_vertex)
            else:
                new_vertex_set.append(vertex)
        return new_vertex_set


collection = Collection()


class Tile:
    def __init__(self, grid_position, world_position=None, tile_type=0, tile_size=None):
        self.grid_position = grid_position
        self.world_position = world_position
        self.tile_type = tile_type
        self.tile_size = tile_size
        self.f = 0
        self.g = 0
        self.q = 0

    def is_in_bounds(self, pos, collider_scale):
        within_x = pos.x + collider_scale > self.world_position.x - self.tile_size.x / 2 and pos.x - collider_scale < self.world_position.x + self.tile_size.x / 2
        within_y = pos.y + collider_scale > self.world_position.y - self.tile_size.y / 2 and pos.y - collider_scale < self.world_position.y + self.tile_size.y / 2
        if within_x and within_y:
            return True
        else:
            return False


class Grid(Component):
    def __init__(self):
        self.grid_dimensions = Vector2()
        self.tile_size = Vector2(30, 30)
        self.pen = turtle.Turtle()
        self.pen.penup()
        self.pen.speed(0)
        self.pen.shape("square")
        self.pen.turtlesize(self.tile_size.y / 20, self.tile_size.x / 20)
        self.pen.pencolor("black")
        self.matrix = [[]]
        self.tile_type = 1
        self.editor_mode = False
        self.past_matrices = []
        self.past_matrix = None
        self.undo_index = 0
        self.undo_length = 99

        self.painting = False
        self.erasing = False

        self.debug_mode = False
        self.debug_pen = turtle.Turtle()
        self.debug_pen.penup()
        self.debug_pen.shape("circle")

    def update(self):
        if input_manager.get_key("Control_L") and input_manager.get_key_down("d"):
            self.editor_mode = not self.editor_mode
            self.render_grid()

        if input_manager.get_key("Control_L") and input_manager.get_key_down("v"):
            self.debug_mode = not self.debug_mode
            self.render_grid()

        if not self.editor_mode:
            return

        if input_manager.get_key("Control_L") and input_manager.get_key_down("z"):
            self.undo()
        elif input_manager.get_key("Control_L") and input_manager.get_key_down("y"):
            self.redo()
        elif input_manager.get_key("Control_L") and input_manager.get_key_down("s"):
            filename = screen.textinput("Save map", "Enter the name of your map")
            input_manager.internal_up("Control_L")
            input_manager.internal_up("s")
            screen.listen()
            self.save_grid_to_text_file(filename)
        elif input_manager.get_key("Control_L") and input_manager.get_key_down("i"):
            filename = screen.textinput("Import map", "Enter the name of your map")
            input_manager.internal_up("Control_L")
            input_manager.internal_up("i")
            screen.listen()
            self.import_grid_from_text_file(filename)
        elif collection.tile_inputs is not None:
            for i in range(0, len(collection.tile_inputs)):
                char = str(collection.tile_inputs[i])
                if input_manager.get_key(char):
                    self.tile_type = i + 1

        if input_manager.mouse_button_left_down:
            if not self.painting:
                self.painting = True
            self.paint_square(input_manager.mouse_pos)
        else:
            if self.painting:
                self.painting = False
                self.record_matrix()
        if input_manager.mouse_button_right_down:
            if not self.erasing:
                self.erasing = True
            self.erase_square(input_manager.mouse_pos)
        else:
            if self.erasing:
                self.erasing = False
                self.record_matrix()

    def undo(self):
        if len(self.past_matrices) > 1:
            self.past_matrices.pop()
            self.matrix = copy.deepcopy(self.past_matrices[len(self.past_matrices) - 1])
            self.render_grid()

    def shift_grid(self, direction):
        for x in range(0, len(self.matrix)):
            for y in range(0, len(self.matrix[x])):
                tile = self.matrix[x][y]
                new_x = int(x + direction.x)
                new_y = int(y + direction.y)
                if 0 <= new_x < len(self.matrix) and 0 <= new_y < len(self.matrix[0]):
                    new_tile = self.matrix[new_x][new_y]
                    my_tile_type = tile.tile_type
                    tile.tile_type = 0
                    new_tile.tile_type = my_tile_type
        self.record_matrix()
        self.calculate_coordinates()
        self.render_grid()

    def erase_square(self, screen_pos):
        closest_tile = self.get_closest_tile_by_world_position(screen_pos)
        if closest_tile is not None:
            closest_tile.tile_type = 0
            self.render_grid()

    def paint_square(self, screen_pos):
        closest_tile = self.get_closest_tile_by_world_position(screen_pos)
        if closest_tile is not None:
            closest_tile.tile_type = self.tile_type
            self.render_grid()

    def find_tiles_by_type(self, tile_type):
        tiles = []
        for i in range(0, len(self.matrix)):
            for j in range(0, len(self.matrix[i])):
                tile = self.matrix[i][j]
                if tile.tile_type == tile_type:
                    tiles.append(tile)
        return tiles

    def get_closest_tile_by_world_position(self, world_pos):
        if self.matrix[0][0].world_position is None:
            self.calculate_coordinates()
        closest_tile = None
        for x in range(0, len(self.matrix)):
            for y in range(0, len(self.matrix[x])):
                tile = self.matrix[x][y]
                if closest_tile is None:
                    closest_tile = tile
                else:
                    if (tile.world_position - world_pos).magnitude() < (
                            closest_tile.world_position - world_pos).magnitude():
                        closest_tile = tile
        return closest_tile

    def calculate_coordinates(self):
        for x in range(0, len(self.matrix)):
            for y in range(0, len(self.matrix[x])):
                tile = self.matrix[x][y]
                tile.world_position = self.grid_to_world_position(tile.grid_position)

    def grid_to_world_position(self, grid_pos):
        new_x = self.game_object.transform.position.x + grid_pos.x * self.tile_size.x
        new_y = self.game_object.transform.position.y + grid_pos.y * self.tile_size.y
        return Vector2(new_x, new_y)

    def create(self, dimensions):
        self.grid_dimensions = dimensions
        for x in range(0, self.grid_dimensions.x):
            self.matrix.append([])
            for y in range(0, self.grid_dimensions.y):
                grid_pos = Vector2(x, y)
                new_tile = Tile(grid_pos, tile_size=self.tile_size)
                self.matrix[x].append(new_tile)
        self.center_grid()
        self.calculate_coordinates()

    def get_path(self, start_tile, end_tile):
        self.debug_pen.clear()
        open_list = [start_tile]
        closed_list = []
        parent_child_pairs = {}

        start_tile.g = 0
        start_tile.h = abs(start_tile.grid_position.x - end_tile.grid_position.x) + abs(
            start_tile.grid_position.y - end_tile.grid_position.y)
        start_tile.f = start_tile.h

        if self.debug_mode:
            self.debug_pen.color("darkred")
            self.debug_pen.shapesize(1)
            self.debug_pen.goto(start_tile.world_position.x, start_tile.world_position.y)
            self.debug_pen.stamp()

            self.debug_pen.color("darkorange2")
            self.debug_pen.shapesize(1)
            self.debug_pen.goto(end_tile.world_position.x, end_tile.world_position.y)
            self.debug_pen.stamp()

        while len(open_list) > 0:
            current_tile = open_list[0]
            for tile in open_list:
                if tile.f < current_tile.f:
                    current_tile = tile

            if current_tile == end_tile:
                path = []
                while current_tile in parent_child_pairs:
                    path.append(current_tile)
                    current_tile = parent_child_pairs[current_tile]
                path.reverse()
                return path

            open_list.remove(current_tile)
            closed_list.append(current_tile)

            for direction in collection.directions:
                new_x = current_tile.grid_position.x + direction.x
                new_y = current_tile.grid_position.y + direction.y

                if self.debug_mode:
                    stamp_pos = self.grid_to_world_position(Vector2(new_x, new_y))
                    self.debug_pen.color("green")
                    self.debug_pen.shapesize(0.75)
                    self.debug_pen.goto(stamp_pos.x, stamp_pos.y)
                    self.debug_pen.stamp()

                if not (0 <= new_x < self.grid_dimensions.x and 0 <= new_y < self.grid_dimensions.y):
                    continue
                next_tile = self.matrix[new_x][new_y]
                if next_tile is not None and next_tile.tile_type in collection.air_tile_types and next_tile not in closed_list:
                    new_g = current_tile.g + 1
                    if next_tile not in open_list or new_g < next_tile.g:
                        parent_child_pairs[next_tile] = current_tile
                        next_tile.g = new_g
                        next_tile.h = abs(next_tile.grid_position.x - end_tile.grid_position.x) + abs(
                            next_tile.grid_position.y - end_tile.grid_position.y)
                        next_tile.f = next_tile.g + next_tile.h
                        if next_tile not in open_list:
                            open_list.append(next_tile)

        return []

    def populate_dots(self):
        tiles = self.find_tiles_by_type(0)
        for tile in tiles:
            dot_manager.add_pos(tile.world_position)
        dot_manager.render_dots()

    def center_grid(self):
        self.game_object.transform.position.x = -(self.grid_dimensions.x * self.tile_size.x) / 2
        self.game_object.transform.position.y = -(self.grid_dimensions.y * self.tile_size.y) / 2

    def render_grid(self):
        vertex_set_count = len(collection.vertex_sets)
        self.pen.clear()
        for x in range(0, len(self.matrix)):
            for y in range(0, len(self.matrix[x])):
                tile = self.matrix[x][y]
                vertices = []
                pen_color = "blue"
                fill_color = "black"
                will_skip = False
                if tile.tile_type < vertex_set_count:
                    vertices = collection.vertex_sets[tile.tile_type]

                if vertices is None or len(vertices) == 0 or (pen_color is None and pen_color is None):
                    will_skip = True
                if not will_skip:
                    if pen_color is not None:
                        self.pen.pencolor(pen_color)
                    if fill_color is not None:
                        self.pen.fillcolor(fill_color)

                    for i in range(len(vertices)):
                        vertex = vertices[i]
                        if vertex == "*":
                            self.pen.penup()
                            continue
                        pos = tile.world_position + (vertex * self.tile_size * 0.5)
                        self.pen.goto(pos.x, pos.y)
                        self.pen.pendown()

                self.pen.penup()
                self.pen.goto(tile.world_position.x, tile.world_position.y)
                if self.editor_mode:
                    self.pen.pencolor("white")
                    if tile.tile_type != 0:
                        self.pen.write(str(tile.tile_type), align="center")

    def record_matrix(self):
        matrix_copy = copy.deepcopy(self.matrix)
        self.past_matrices.append(matrix_copy)
        if len(self.past_matrices) > self.undo_length:
            del self.past_matrices[0]

    def save_grid_to_text_file(self, filename):
        if filename is not None:
            file = open(filename + ".txt", "w")
            for x in range(0, len(self.matrix)):
                if x > 0:
                    file.write("\n")
                for y in range(0, len(self.matrix[x])):
                    tile = self.matrix[x][y]
                    file.write(str(tile.tile_type) + ",")
            file.close()

    def import_grid_from_text_file(self, filename):
        if filename is not None:
            try:
                file = open(filename + ".txt")
            except FileNotFoundError:
                print("File does not exist")
                return
            txt = file.read()
            lines = txt.split("\n")
            for x in range(0, len(lines)):
                entries = lines[x].split(",")
                for y in range(0, len(entries)):
                    char = entries[y]
                    if char == "":
                        continue
                    new_grid_pos = Vector2(x, y)
                    self.matrix[x][y] = Tile(new_grid_pos, self.grid_to_world_position(new_grid_pos), int(char),
                                             self.tile_size)
            file.close()
        self.render_grid()

game_started = False

class Entity(Component):
    def __init__(self):
        super().__init__()
        self.move_input = Vector2(0, 0)
        self.move_speed = 3.3
        self.collider_scale = 999

    def start(self):
        pass

    def update(self):
        if not game_started:
            return

        movement = self.game_object.transform.position + self.move_input * self.move_speed
        tile = grid.get_closest_tile_by_world_position(movement)
        if tile.tile_type not in collection.air_tile_types and tile.is_in_bounds(movement, self.collider_scale):
            return
        self.game_object.transform.position = movement


class Player(Component):
    def __init__(self):
        super().__init__()
        self.entity = None
        self.mouth = None
        self.mouth_pivot = None
        self.origin_mouth_y_scale = 0

    def start(self):
        self.mouth_pivot = GameObject()
        self.mouth_pivot.transform.parent = self.game_object.transform
        self.mouth = GameObject(scale=Vector2(1, 1) * 0.6, starting_comps=[Sprite("triangle", "black")])
        self.origin_mouth_y_scale = self.mouth.transform.scale.y
        self.mouth.transform.rotation = 180
        self.mouth.transform.parent = self.mouth_pivot.transform
        self.mouth.transform.local_position = Vector2(8, 0)

        self.entity = self.game_object.get_component(Entity)
        self.entity.move_input = Vector2(1, 0)

        spawn_tiles = grid.find_tiles_by_type(36)
        if len(spawn_tiles) > 0:
            self.game_object.transform.position = spawn_tiles[0].world_position
        
        start_coroutine(self.mouth_routine())

    def update(self):
        global game_started
        if input_manager.get_key_down("Escape"):
            game_started = not game_started

        if not game_started:
            return

        if input_manager.get_key_down("Up") or input_manager.get_key_down("w"):
            self.entity.move_input = Vector2(0, 1)
            Lerp(self.mouth_pivot.transform, "local_rotation", 90, 0.075)
        if input_manager.get_key_down("Right") or input_manager.get_key_down("d"):
            self.entity.move_input = Vector2(1, 0)
            Lerp(self.mouth_pivot.transform, "local_rotation", 0, 0.075)
        if input_manager.get_key_down("Down") or input_manager.get_key_down("s"):
            self.entity.move_input = Vector2(0, -1)
            Lerp(self.mouth_pivot.transform, "local_rotation", -90, 0.075)
        if input_manager.get_key_down("Left") or input_manager.get_key_down("a"):
            self.entity.move_input = Vector2(-1, 0)
            Lerp(self.mouth_pivot.transform, "local_rotation", 180, 0.075)
    
    def mouth_routine(self):
        while not game_started:
            yield
        while game_started:
            Lerp(self.mouth.transform, "local_scale", Vector2(self.mouth.transform.local_scale.x, 0), 0.05)
            yield from wait_for_seconds(0.35)
            Lerp(self.mouth.transform, "local_scale", Vector2(self.mouth.transform.local_scale.x, self.origin_mouth_y_scale), 0.05)
            yield from wait_for_seconds(0.35)


def end_game(win=False):
    global game_started
    game_started = False
    dot_manager.dot_poses.clear()
    dot_manager.render_dots()
    for ghost in ghosts:
        ghost.destroy()
    if not win:
        start_coroutine(lose_routine())
    else:
        start_coroutine(win_routine())

def win_routine():
    yield from wait_for_seconds(0.5)
    txt = GameObject().add_component(Text("You Win", "white"))
    yield from wait_for_seconds(1)
    yield from wait_for_input()
    txt.game_object.destroy()
    pacman.destroy()
    start_coroutine(game_start_routine())

def lose_routine():
    yield from wait_for_seconds(0.5)
    Lerp(pacman.transform, "scale", Vector2(1, 0), 1)
    Lerp(pacman.transform, "position", pacman.transform.position - Vector2(0, 0.5), 1)
    yield from wait_for_seconds(1)
    pacman.destroy()
    yield from wait_for_seconds(0.5)
    txt = GameObject().add_component(Text("Game Over", "white"))
    yield from wait_for_seconds(1)
    yield from wait_for_input()
    txt.game_object.destroy()
    start_coroutine(game_start_routine())



class Ghost(Component):
    def __init__(self, offset=Vector2(), speed=3, spawn=0, engage_distance=0):
        super().__init__()
        self.entity = None
        self.path_points = []
        self.path_index = 0
        self.offset = offset
        self.speed = speed
        self.engage_distance = engage_distance
        self.spawn = spawn
        self.player_closest_tile = None

    def start(self):
        color = self.game_object.get_component(Sprite).color
        body = GameObject(scale=Vector2(1, 0.5), starting_comps=[Sprite("square", color)])
        body.transform.parent = self.game_object.transform
        body.transform.local_position = Vector2(0, -7)

        for i in range(0, 2):
            eye = GameObject(scale=Vector2(0.25, 0.35), starting_comps=[Sprite("circle", "white", 1)])
            eye.transform.parent = self.game_object.transform
            mult = 1
            if i != 0:
                mult = -1
            eye.transform.local_position = Vector2(6 * mult, 0)

        self.entity = self.game_object.get_component(Entity)
        self.entity.move_speed = self.speed
        spawn_tiles = grid.find_tiles_by_type(35 - self.spawn)
        if len(spawn_tiles) > 0:
            self.game_object.transform.position = spawn_tiles[0].world_position

    def calculate_path_to_player(self):
        closest_tile = grid.get_closest_tile_by_world_position(self.game_object.transform.position)
        candidate = grid.get_closest_tile_by_world_position(pacman.game_object.transform.position)
        
        close = (self.game_object.transform.position - pacman.game_object.transform.position).magnitude() < self.engage_distance
        if not close:
            try:
                candidate = grid.matrix[candidate.grid_position.x + self.offset.x][
                    candidate.grid_position.y + self.offset.y]
            except IndexError:
                pass
        
        if candidate.tile_type in collection.air_tile_types:
            self.player_closest_tile = candidate
        if self.player_closest_tile is None:
            return

        if closest_tile is not None and self.player_closest_tile is not None:
            self.path_points = grid.get_path(closest_tile, self.player_closest_tile)
            self.path_index = 0

    def update(self):
        if (self.game_object.transform.position - pacman.game_object.transform.position).magnitude() < 10:
            end_game()

        if (self.game_object.transform.position - pacman.game_object.transform.position).magnitude() < 25:
            if pacman.transform.position.x > self.game_object.transform.position.x:
                self.entity.move_input.x = 1
            elif pacman.transform.position.x < self.game_object.transform.position.x:
                self.entity.move_input.x = -1

            if pacman.transform.position.y > self.game_object.transform.position.y:
                self.entity.move_input.y = 1
            elif pacman.transform.position.y < self.game_object.transform.position.y:
                self.entity.move_input.y = -1
            return

        self.calculate_path_to_player()
        if self.path_points is None or len(self.path_points) == 0:
            return

        path_point = self.path_points[self.path_index]
        if path_point.world_position.x > self.game_object.transform.position.x:
            self.entity.move_input = Vector2(1, 0)
        elif path_point.world_position.x < self.game_object.transform.position.x:
            self.entity.move_input = Vector2(-1, 0)
        elif path_point.world_position.y > self.game_object.transform.position.y:
            self.entity.move_input = Vector2(0, 1)
        elif path_point.world_position.y < self.game_object.transform.position.y:
            self.entity.move_input = Vector2(0, -1)
        else:
            self.entity.move_input = Vector2(0, 0)

        if (self.game_object.transform.position - path_point.world_position).magnitude() < 0.5:
            if self.path_index + 1 < len(self.path_points):
                self.path_index += 1
            else:
                self.path_points.clear()


class DotManager(Component):
    def __init__(self):
        super().__init__()
        self.dot_poses = []
        self.dot_pen = turtle.Turtle()
        self.dot_pen.hideturtle()
        self.dot_pen.color("yellow")
        self.dot_pen.penup()
        self.dot_pen.speed(0)
        self.dot_pen.shape("circle")
        self.dot_pen.shapesize(0.5)

    def update(self):
        for dot_pos in self.dot_poses:
            if (dot_pos - pacman.game_object.transform.position).magnitude() < 15:
                self.dot_poses.remove(dot_pos)
                if len(self.dot_poses) <= 0:
                    end_game(win=True)
                self.render_dots()

    def add_pos(self, pos):
        if max_dots != -1 and len(self.dot_poses) >= max_dots:
            return
        self.dot_poses.append(pos)

    def render_dots(self):
        self.dot_pen.clear()
        for dot_pos in self.dot_poses:
            self.dot_pen.goto(dot_pos.x, dot_pos.y)
            self.dot_pen.stamp()


render_objects = []
game_objects = []
lerps = []
coroutines = []
dot_poses = []

screen = turtle.Screen()

screen.tracer(0, 0)
screen.delay(0)

screen.title("Pacman")
screen.bgcolor("black")
screen_dimensions = Vector2(1280, 720)
black_bars = GameObject().add_component(BlackBars(screen_dimensions))
screen.setup(screen_dimensions.x, screen_dimensions.y)

grid = None
dot_manager = None
input_manager = None
pacman = None
ghosts = None

def game_start_routine():
    global grid, dot_manager, input_manager, game_started, pacman, ghosts
    dot_manager = GameObject().add_component(DotManager())

    input_manager = Input()
    grid = GameObject().add_component(Grid())
    grid.create(Vector2(31, 21))
    grid.import_grid_from_text_file("map")
    grid.populate_dots()

    pacman = GameObject(starting_comps=[Sprite("circle", "yellow"), Entity(), Player()])

    blinky = GameObject(starting_comps=[Sprite("circle", "red"), Entity(), Ghost(speed=3, spawn=0)])
    pinky = GameObject(
        starting_comps=[Sprite("circle", "pink"), Entity(), Ghost(offset=Vector2(2, 0), speed=2.5, spawn=1, engage_distance=50)])
    clyde = GameObject(
        starting_comps=[Sprite("circle", "orange"), Entity(), Ghost(offset=Vector2(-2, 0), speed=2, spawn=2, engage_distance=75)])
    seth = GameObject(
        starting_comps=[Sprite("circle", "cyan"), Entity(), Ghost(offset=Vector2(0, -5), speed=2.5, spawn=1, engage_distance=100)])
    ghosts = [blinky, pinky, clyde, seth]

    txt = GameObject(position=Vector2(-10, 30)).add_component(Text(color="white", font_size="96"))
    for i in range(0, 3):
        txt.text = str(3 - i)
        yield from wait_for_seconds(1)
    txt.game_object.destroy()
    game_started = True


start_coroutine(game_start_routine())

def refresh_screen():
    sorted_render_objects = render_objects
    sorted_render_objects.sort(key=lambda r: r.sort_order)
    for r in sorted_render_objects:
        r.render()

def game_loop():
    for game_object in game_objects:
        game_object.update()
    for lerp in lerps:
        lerp.update()

    for coroutine in coroutines:
        try:
            next(coroutine)
        except StopIteration:
            coroutines.remove(coroutine)
    refresh_screen()
    input_manager.late_update()
    screen.ontimer(game_loop, int(1000 / fps))


game_loop()

refresh_screen()
screen.mainloop()