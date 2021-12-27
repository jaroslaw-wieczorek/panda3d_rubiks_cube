#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" Game Rubik's Cube in Panda3d and Blender"""
__author__ = "Jarosław Wieczorek"
__copyright__ = "Copyright 2021"
__license__ = "MIT"
__version__ = "1.0.0"
__email__ = "jaroslaw[dot]wieczorek[at]sealcode[dot]org"

# Direct
from direct.gui.OnscreenText import OnscreenText
from direct.interval.FunctionInterval import Func, Wait
from direct.interval.MetaInterval import Sequence
from direct.showbase.ShowBase import ShowBase
# Panda 3d
from panda3d.core import AmbientLight, Trackball, MouseButton, TextFont
from panda3d.core import CollisionNode, CollisionBox, CollisionEntry
from panda3d.core import CollisionTraverser, CollisionHandlerEvent
from panda3d.core import loadPrcFile
from panda3d.core import TextNode, NodePath
from panda3d.core import Vec3
# Mouse
from pynput.mouse import Controller as MouseController
# Other
from random import choices, randint
from string import ascii_letters
import sys

# Load configuration
loadPrcFile("config/conf.prc")

class MyGame(ShowBase):
    """Game Class"""
    def __init__(self, debug=False):
        ShowBase.__init__(self)

        # Set debug mode
        self.debug_mode = debug

        # Create mouse controller
        self.mouse_controller = MouseController()

        # Keeps last position of mouse
        self.p1 = (0, 0)
        # Current direction
        self.direction = -1
        self.animate = True
        self.randomizing = False

        # Print last pressed key
        self.pressed_button = OnscreenText()
        self.info_on_screen = OnscreenText()

        # Load rubik's cube model
        self.cube_model = self.loader.loadModel('./models/rubiks.bam')
        self.cube_model.setScale(1)
        self.cube_model.setPos(0, 0, 0)
        self.cube_model.setHpr(0, 0, 0)
        # Assign cube to render
        self.cube_model.reparentTo(self.render)

        # Set scene light
        self.light = AmbientLight('light')
        self.light.setColor((1, 1, 1, 1))
        self.plight = self.render.attachNewNode(self.light)
        self.plight.setPos(0, 0, 0)
        self.render.setLight(self.plight)

        # Set camera position and focus
        self.cam.setPos(0, -28, 0)
        self.cam.lookAt(self.cube_model)

        if self.debug_mode:
            # List all rubiks elements
            print(self.cube_model.ls())

        self.top_traverser = CollisionTraverser("top_traverser")
        self.bottom_traverser = CollisionTraverser("bottom_traverser")
        self.left_traverser = CollisionTraverser("left_traverser")
        self.right_traverser = CollisionTraverser("right_traverser")
        self.front_traverser = CollisionTraverser("front_traverser")
        self.back_traverser = CollisionTraverser("back_traverser")
        self.center_vert_traverser = CollisionTraverser("center_vert_traverser")
        self.center_hori_traverser = CollisionTraverser("center_hori_traverser")
        self.center_double_traverser = CollisionTraverser(
            "center_double_traverser")

        # Initialize the handler
        self.collHandEventTop = CollisionHandlerEvent()
        self.collHandEventBottom = CollisionHandlerEvent()
        self.collHandEventLeft = CollisionHandlerEvent()
        self.collHandEventRight = CollisionHandlerEvent()
        self.collHandEventFront = CollisionHandlerEvent()
        self.collHandEventBack = CollisionHandlerEvent()
        self.collHandEventDoubleCenter = CollisionHandlerEvent()
        self.collHandEventVertCenter = CollisionHandlerEvent()
        self.collHandEventHoriCenter = CollisionHandlerEvent()

        self.mapping_sides = {
            "TOP_SIDE": {
                "trav": self.top_traverser,
                "handler": self.collHandEventTop,
                "pattern": "top-%in",
                "key": "t",
                "rotation": Vec3(-90., 0., 0.),
                "num": 9,
            },
            "BOTTOM_SIDE": {
                "trav": self.bottom_traverser,
                "handler": self.collHandEventBottom,
                "pattern": "bottom-%in",
                "key": "d",
                "rotation": Vec3(-90., 0., 0.),
                "num": 9,
            },
            "LEFT_SIDE": {
                "trav": self.left_traverser,
                "handler": self.collHandEventLeft,
                "pattern": "left-%in",
                "key": "l",
                "rotation": Vec3(0., 90., 00.),
                "num": 9,
            },
            "RIGHT_SIDE": {
                "trav": self.right_traverser,
                "handler": self.collHandEventRight,
                "pattern": "right-%in",
                "key": "r",
                "rotation": Vec3(0., -90., 0.),
                "num": 9,
            },
            "FRONT_SIDE": {
                "trav": self.front_traverser,
                "handler": self.collHandEventFront,
                "pattern": "front-%in",
                "key": "f",
                "rotation": Vec3(0., 0., 90.),
                "num": 9,
            },
            "BACK_SIDE": {
                "trav": self.back_traverser,
                "handler": self.collHandEventBack,
                "pattern": "back-%in",
                "key": "b",
                "rotation": Vec3(0., 0., -90.),
                "num": 9,
            },
            "CENTER_VERTICAL_SIDE": {
                "trav": self.center_vert_traverser,
                "handler": self.collHandEventVertCenter,
                "pattern": "vert_center-%in",
                "key": "v",
                "rotation": Vec3(-90., 0., 0.),
                "num": 8,
            },
            "CENTER_DOUBLE_SIDE": {
                "trav": self.center_double_traverser,
                "handler": self.collHandEventDoubleCenter,
                "pattern": "double_center-%in",
                "key": "c",
                "rotation": Vec3(0., 0., 90.),
                "num": 8,
            },
            "CENTER_HORIZONTAL_SIDE": {
                "trav": self.center_hori_traverser,
                "handler": self.collHandEventHoriCenter,
                "pattern": "hori_center-%in",
                "key": "h",
                "rotation": Vec3(0., 90., 0.),
                "num": 8
            }
        }

        self.collided_cubes = set()
        for mapping_side in self.mapping_sides.values():
            mapping_side["handler"].addInPattern(mapping_side["pattern"])

        # Create side colliders
        self.create_side_colliders()

        # Create box colliders
        self.create_box_colliders()

        # Rotate sides
        self.buttonThrowers[0].node().setKeystrokeEvent('keystroke')

        # Exit on ESC
        self.accept("escape", sys.exit)

        # Disable default camera move and zoom by mouse
        self.trackball.node().set_control_mode(Trackball.CM_pan)
        self.trackball.node().require_button(MouseButton.two(), False)
        self.trackball.node().require_button(MouseButton.three(), False)

        # Mix cube
        # self.randomize()
        self.accept_once("keystroke", self.force_collisions)
        self.draw_3d_text()

    def draw_3d_text(self):
        self.font = self.loader.loadFont('./fonts/party.ttf')
        self.font.setRenderMode(TextFont.RMTexture)

        for side in self.mapping_sides.values():
            text = side['key'].upper()
            textlabel = TextNode(text)
            textlabel.setText(text)
            textlabel.setTextScale(0.9)
            textlabel.setTextColor(255, 255, 0, 0.8)

            textlabel.setCardColor(0, 0, 0, 0.8)
            textlabel.setCardAsMargin(0.35, 0.4, 0.0, -0.1)
            textlabel.setCardDecal(True)

            textlabel.setAlign(TextNode.ABoxedCenter)
            textlabel.setFont(self.font)
            textNode = self.cube_model.attachNewNode(textlabel)
            textNode.setPos(side['node_path'].getPos()*2)
            textNode.lookAt(self.trackball)

    def create_side_colliders(self):
        """ Create side colliders """
        self.sides = self.cube_model.find_all_matches("*SIDE*")

        for side in self.sides:
            side: NodePath
            name = side.getName()

            # Show bounds
            if self.debug_mode:
                side.show()
                side.showTightBounds()
            else:
                side.hide()

            cNode = CollisionNode(name)
            cNode.addSolid(
                CollisionBox(side.getTightBounds()[0], side.getTightBounds()[1])
            )
            sideC = side.attachNewNode(cNode)

            if self.debug_mode:
                sideC.show()
            else:
                sideC.hide()

            # Add side collider
            map_side = self.mapping_sides[name]
            map_side['node_path'] = side
            traverser, handler = map_side["trav"], map_side["handler"]
            traverser.addCollider(sideC, handler)

            pattern = map_side["pattern"].replace('%in', name)
            num = map_side["num"]
            self.accept(pattern, self.collide, [num])

    def create_box_colliders(self):
        """ Create box colliders """
        whites = self.cube_model.find_all_matches("*WHITE*")
        yellows = self.cube_model.find_all_matches("*YELLOW*")
        reds = self.cube_model.find_all_matches("*RED*")
        blues = self.cube_model.find_all_matches("*BLUE*")
        greens = self.cube_model.find_all_matches("*GREEN*")
        orange = self.cube_model.find_all_matches("*ORANGE*")

        self.cubes = {*whites, *yellows, *reds, *blues, *greens, *orange}
        for num, cube in enumerate(self.cubes):
            cube: NodePath

            if self.debug_mode:
                cube.showTightBounds()
            cCubeNode = CollisionNode(cube.name)
            min, max = cube.getTightBounds()

            # Scale BoxCollider smaller than cube
            min[0] += 0.2
            min[1] += 0.2
            min[2] += 0.2

            max[0] -= 0.2
            max[1] -= 0.2
            max[2] -= 0.2

            cCubeNode.addSolid(CollisionBox(min, max))
            cCube = cube.attachNewNode(cCubeNode)
            if self.debug_mode:
                cCube.show()

            # Add current cube collider for each traverser and set handler
            for mapping_side in self.mapping_sides.values():
                traverser = mapping_side["trav"]
                handler = mapping_side["handler"]
                traverser.addCollider(cCube, handler)

    def force_traverse(self, key):
        """ Force traverses by key"""
        # Set rotate direction
        print("Key:", key)
        if key.isupper():
            self.direction = -1
        else:
            self.direction = 1

        if key in ["t", "T"]:
            self.top_traverser.traverse(self.render)

        elif key in ["d", "D"]:
            self.bottom_traverser.traverse(self.render)

        elif key in ["l", "L"]:
            self.left_traverser.traverse(self.render)

        elif key in ["r", "R"]:
            self.right_traverser.traverse(self.render)

        elif key in ["f", "F"]:
            self.front_traverser.traverse(self.render)

        elif key in ["b", "B"]:
            self.back_traverser.traverse(self.render)

        elif key in ["h", "H"]:
            self.center_hori_traverser.traverse(self.render)

        elif key in ["v", "V"]:
            self.center_vert_traverser.traverse(self.render)

        elif key in ["c", "C"]:
            self.center_double_traverser.traverse(self.render)

        else:
            if key == ' ':
                self.randomize()
            elif key in ["1", "2", "3", "4", "5", "6", "7"]:
                self.look_at_cube_side(key)
                # No traverser has been activated.
            self.accept_once("keystroke", self.force_collisions)
        return True

    def force_collisions(self, key: str):
        """ Force traversers """
        self.force_traverse(key=key)
        for cube in self.cubes:
            cube.setFluidPos(cube.getX() + 15, cube.getY() + 15, cube.getZ() + 15)
        self.force_traverse(key=key)
        for cube in self.cubes:
            cube.setFluidPos(cube.getX() - 15, cube.getY() - 15, cube.getZ() - 15)
        self.print_key_on_screen(keyname=key)

    def print_key_on_screen(self, keyname):
        """ Handling a keystroke on the keyboard. """
        if keyname in ascii_letters:
            self.pressed_button.destroy()
            self.pressed_button: OnscreenText = self.gen_label_text(keyname, 0)
        return True

    def print_info_on_screen(self, msg, i=3):
        """ Handling a keystroke on the keyboard. """
        self.info_on_screen.destroy()
        self.info_on_screen = OnscreenText(
            text=msg, parent=self.a2dBottomCenter,
            pos=(0, 0.2), fg=(1, 1, 1, 1),
            align=TextNode.ACenter, shadow=(0, 0, 0, 0.5), scale=.05
        )

        return True

    def rotate_side(self, coll_entry):
        """ Rotate selected side """
        pivot: NodePath = coll_entry.getIntoNodePath()  # get big box
        name = pivot.getName()
        cubes = self.collided_cubes.copy()  # list of small cubes NodePaths
        pivot.clearTransform()

        pivot.show()
        pivot.getParent().show()
        for cubo in cubes:
            cubo.wrtReparentTo(pivot)  # re-parent small boxes to big box
            cubo.show()

        self.seq = Sequence()
        if self.animate:
            hprInterval = pivot.hprInterval(
                0.28, self.mapping_sides[name]['rotation'] * self.direction
            )
            self.seq.append(hprInterval)
        else:
            self.seq.append(Func(self.rotate_without_anim, name, pivot))
        self.seq.append(Func(self.reparent_cubes, pivot, cubes))
        self.seq.append(Func(self.reset, cubes))
        self.seq.start()

    def rotate_without_anim(self, name, pivot):
        pivot.setHpr(self.mapping_sides[name]['rotation'] * self.direction)

    def reset(self, cubes):
        cubes.clear()
        self.collided_cubes.clear()
        if not self.randomizing:
            self.accept_once("keystroke", self.force_collisions)

    def reparent_cubes(self, pivot, cubes):
        pivot.getParent().hide()
        pivot.hide()
        for cube in cubes:
            cube: NodePath
            cube.wrtReparentTo(self.cube_model)

    def collide(self, num: int, collEntry: CollisionEntry):
        """ Collide with side """
        cude_node = collEntry.getFromNodePath().getParent()
        if self.debug_mode:
            side_node = collEntry.getIntoNodePath()
            print(F" -- {side_node.getName()}  ::  {cude_node.getName()}")

        self.collided_cubes.add(cude_node)

        if len(self.collided_cubes) >= num:
            # Rotate selected side of cube
            self.rotate_side(collEntry)
        return True

    def look_at_cube_side(self, key):
        """ Set cam to look at chosen cube side"""
        tb = self.trackball.node()
        if key == "1":
            tmp_txt = "Front"
            tmp_hpr = (0, 0, 0)
        elif key == "2":
            tmp_txt = "Back"
            tmp_hpr = (0, 180, 180)
        elif key == "3":
            tmp_txt = "Left"
            tmp_hpr = (90, 0, 0)
        elif key == "4":
            tmp_txt = "Right"
            tmp_hpr = (-90, 0, 0)
        elif key == "5":
            tmp_txt = "Top"
            tmp_hpr = (0, 90, 0)
        elif key == "6":
            tmp_txt = "Bottom"
            tmp_hpr = (0, -90, 0)
        else:
            tmp_txt = "Opposite side"
            tmp_hpr = tb.getHpr()
            tmp_hpr[2] -= 90

        tb.setHpr(*tmp_hpr)
        self.print_info_on_screen(tmp_txt)

    def gen_label_text(self, text, i):
        """ Draw last rotate side """
        return OnscreenText(
            text=text, parent=self.a2dTopLeft,
            pos=(0.07, -.06 * i - 0.1), fg=(1, 1, 1, 1),
            align=TextNode.ALeft, shadow=(0, 0, 0, 0.5), scale=.05
        )

    def turn_on_off_anmiate(self, state):
        if state:
            self.animate = True
        else:
            self.animate = False

    def turn_of_randomize(self):
        self.randomizing = False
        self.accept_once("keystroke", self.force_collisions)

    def randomize(self):
        keys = []
        print("Space")
        if not self.randomizing:
            self.randomizing = True
            for x in self.mapping_sides.values():
                keys.append(x['key'])
                keys.append(x['key'].upper())
            choosed_keys = choices(keys, k=randint(30, 60))
            random_seq = Sequence()
            random_seq.append(Func(self.turn_on_off_anmiate, False))
            random_seq.append(Wait(1.0))
            for key in choosed_keys:
                random_seq.append(Func(self.force_collisions, key))
                random_seq.append(Wait(0.15))
            random_seq.append(Func(self.turn_on_off_anmiate, True))
            random_seq.append(Func(self.turn_of_randomize))
            random_seq.start()


if __name__ == '__main__':
    game = MyGame(debug=True)
    game.cam.node().getDisplayRegion(0).setSort(1)
    game.run()
