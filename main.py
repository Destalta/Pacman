import math
import random
import time
import turtle

fps = 60


def wait_for_seconds(t):
    for i in range(0, int(t * 16)):
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

    def on_delete():
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
            self.position = self.parent.position + self.local_position
            self.rotation = self.parent.rotation + self.local_rotation
            if not self.ignore_parent_scale:
                self.scale = self.parent.scale * self.local_scale
            self.rotation = self.parent.rotation + self.local_rotation

    def tween_position(self, new_position, speed):
        return Lerp(self, "position", new_position, speed)

    def tween_rotation(self, new_rotation, speed):
        return Lerp(self, "rotation", new_rotation, speed)

    def tween_scale(self, new_scale, speed):
        return Lerp(self, "scale", new_scale, speed)

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
            self.pseudostamp()

    def on_delete(self):
        super().on_delete()
        self.pen.clear()
        render_objects.remove(self)

    def pseudostamp(self):
        pass


class Sprite(RenderObject):
    def __init__(self, shape="square", color="white"):
        super().__init__()
        self.shape = shape
        self.color = color

    def pseudostamp(self):
        super().pseudostamp()
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

    def pseudostamp(self):
        super().pseudostamp()
        self.pen.color(self.color)
        self.pen.write(self.text, font=(self.font, self.font_size), align="center")


class EdgeDelete(Component):
    def __init__(self):
        super().__init__()

    def update(self):
        super().update()
        transform = self.game_object.transform
        bool_x = self.detect(transform.position.x, screen_dimensions.x / 2, -transform.scale.x * 10)
        bool_y = self.detect(transform.position.y, screen_dimensions.y / 2, -transform.scale.y * 10)
        if bool_x or bool_y:
            self.game_object.destroy()

    def detect(self, a, b, extra_size=0):
        if a >= (b - extra_size):
            return True
        elif a <= (-b + extra_size):
            return True
        return False


class EdgeConstrict(Component):
    def __init__(self):
        super().__init__()

    def update(self):
        super().update()
        transform = self.game_object.transform
        transform.position.x = self.constrict(transform.position.x, screen_dimensions.x / 2, transform.scale.x * 10)
        transform.position.y = self.constrict(transform.position.y, (screen_dimensions.y + 10) / 2,
                                              transform.scale.y * 20)

    def constrict(self, a, b, extra_size=0):
        if a >= (b - extra_size):
            a = b - extra_size
        elif a <= (-b + extra_size):
            a = -b + extra_size
        return a


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
            new_val += (self.target - new_val) * self.timer
            setattr(self.obj, self.attribute, new_val)
            if self.timer >= 1:
                self.stop()


class Input:
    def __init__(self):
        screen.listen()
        self.keys = ["Up", "Down", "Left", "Right",
                     "Control_L", "Shift_L"]

        self.keys_down = set()
        self.keys_down_this_frame = set()
        self.keys_up_this_frame = set()

        self.mouse_pos = Vector2()
        screen.getcanvas().bind("<Motion>", self.set_mouse_pos)
        self.mouse_button_left_down = False
        self.mouse_button_right_down = False
        screen.getcanvas().bind('<ButtonPress-1>', self.on_mouse_button_left_down)
        screen.getcanvas().bind('<ButtonRelease-1>', self.on_mouse_button_left_up)
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
        self.keyboard_layout = ["q", "w", "e", "r", "t", "y", "u", "i", "o", "p", "a", "s", "d", "f", "g", "h", "j", "k", "l", "z", "x", "c", "v", "b", "n", "m"]
        self.tile_inputs = []
        self.tile_inputs.extend(self.numbers)
        self.tile_inputs.extend(self.keyboard_layout)
        self.vertex_sets = []
        self.vertex_sets.append(None)
        pipe = self.mirror([Vector2(-1, 0.75), Vector2(1, 0.75), "*"])
        self.vertex_sets.append(pipe)
        self.vertex_sets.append(self.rotate(pipe, 90))
        pipe_corner = [Vector2(-1, 0.75), Vector2(0.55, 0.75), Vector2(0.75, 0.55), Vector2(0.75, -1), "*", Vector2(-1, -0.75), Vector2(-0.75, -1)]
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
        thin_pipe_corner = [Vector2(-1, 0.5), Vector2(0.5, 0.5), Vector2(0.5, -1), "*", Vector2(-1, -0.5), Vector2(-0.5, -1)]
        self.vertex_sets.append(thin_pipe_corner) 
        self.vertex_sets.append(self.rotate(thin_pipe_corner, 90))
        self.vertex_sets.append(self.rotate(thin_pipe_corner, 180))
        self.vertex_sets.append(self.rotate(thin_pipe_corner, 270))
        thin_pipe_cap = [Vector2(-1, 0.5), Vector2(0.5, 0.5), Vector2(0.5, -0.5), Vector2(-1, -0.5)]
        self.vertex_sets.append(thin_pipe_cap)
        self.vertex_sets.append(self.rotate(thin_pipe_cap, 90)) 
        self.vertex_sets.append(self.rotate(thin_pipe_cap, 180))
        self.vertex_sets.append(self.rotate(thin_pipe_cap, 270))
        wad = self.mirror([Vector2(-1, 0), Vector2(-1, 0.5), Vector2(-0.75, 0.75), Vector2(0.75, 0.75), Vector2(1, 0.5),Vector2(1, 0)])
        self.vertex_sets.append(wad)
        self.vertex_sets.append(self.rotate(wad, 90))

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
    def __init__(self, grid_position, world_position=None, tile_type=0):
        self.grid_position = grid_position
        self.world_position = world_position
        self.tile_type = tile_type


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
        self.editor_mode = True
        self.debug_mode = False
        self.past_matrices = []
        self.past_matrix = None

    def update(self):
        if not self.editor_mode:
            return
        
        if input_manager.get_key("Control_L") and input_manager.get_key_down("s"):
            self.save_grid_to_text_file()
        elif input_manager.get_key("Control_L") and input_manager.get_key_down("i"):
            self.import_grid_from_text_file()
        elif input_manager.mouse_button_left_down:
            self.paint_square(input_manager.mouse_pos)
        elif input_manager.mouse_button_right_down:
            self.erase_square(input_manager.mouse_pos)
        elif input_manager.get_key("Control_L") and input_manager.get_key_down("d"):
            self.debug_mode = not self.debug_mode
            self.render_grid()
        elif collection.tile_inputs is not None:
            for i in range(0, len(collection.tile_inputs)):
                char = str(collection.tile_inputs[i])
                if input_manager.get_key(char):
                    self.tile_type = i + 1

    def erase_square(self, screen_pos):
        closest_tile = self.get_closest_tile_by_screen_position(screen_pos)
        if closest_tile is not None:
            closest_tile.tile_type = 0
            self.render_grid()

    def paint_square(self, screen_pos):
        closest_tile = self.get_closest_tile_by_screen_position(screen_pos)
        if closest_tile is not None:
            closest_tile.tile_type = self.tile_type

            self.render_grid()

    def get_closest_tile_by_screen_position(self, screen_pos):
        if self.matrix[0][0].world_position is None:
            self.calculate_coordinates()
        closest_tile = None
        for x in range(0, len(self.matrix)):
            for y in range(0, len(self.matrix[x])):
                tile = self.matrix[x][y]
                if closest_tile is None:
                    closest_tile = tile
                else:
                    pos = Vector2(screen_pos.x, screen_pos.y)
                    if (tile.world_position - pos).magnitude() < (closest_tile.world_position - pos).magnitude():
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
                new_tile = Tile(grid_pos)
                self.matrix[x].append(new_tile)
        self.center_grid()
        self.calculate_coordinates()

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
                if tile.tile_type < vertex_set_count:
                    vertices = collection.vertex_sets[tile.tile_type]
                
                if vertices is None or len(vertices) == 0 or (pen_color is None and pen_color is None):
                    continue
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
                if self.debug_mode:
                    self.pen.pencolor("white")
                    self.pen.write(str(tile.tile_type), align="center")

    def record_matrix(self):
        if self.past_matrix is not None and self.past_matrix != self.matrix:
            self.past_matrices.append(self)
            self.past_matrix = self.matrix

    def save_grid_to_text_file(self):
        filename = screen.textinput("Save map", "Enter the name of your map")
        if filename is not None:
            with open(filename + ".txt", "w") as file:
                for x in range(0, len(self.matrix)):
                    if x > 0:
                        file.write("\n")
                    for y in range(0, len(self.matrix[x])):
                        tile = self.matrix[x][y]
                        file.write(str(tile.tile_type) + ",")
        screen.listen()

    def import_grid_from_text_file(self):
        filename = screen.textinput("Import map", "Enter the name of your map")
        if filename is not None:
            with open(filename + ".txt") as file:
                txt = file.read()
                lines = txt.split("\n")
                for x in range(0, len(lines)):
                    entries = lines[x].split(",")
                    for y in range(0, len(entries)):
                        char = entries[y]
                        if char == "":
                            continue
                        new_grid_pos = Vector2(x, y)
                        self.matrix[x][y] = Tile(new_grid_pos, self.grid_to_world_position(new_grid_pos), int(char))
        self.render_grid()
        screen.listen()


render_objects = []
game_objects = []
lerps = []
coroutines = []

screen = turtle.Screen()

screen.tracer(0, 0)
screen.delay(0)

screen.title("Pacman")
screen.bgcolor("black")
screen_dimensions = Vector2(1280, 720)
black_bars = GameObject().add_component(BlackBars(screen_dimensions))
screen.setup(screen_dimensions.x, screen_dimensions.y)

box = GameObject().add_component(Sprite("square", "black"))
box.game_object.transform.position = Vector2(-100, 50)

input_manager = Input()
grid = GameObject().add_component(Grid())
grid.create(Vector2(31, 21))
grid.render_grid()


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
