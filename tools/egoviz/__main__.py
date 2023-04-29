from ursina import *

app = Ursina()

cube = Entity(model='cube', color=hsv(300,1,1), scale=2, collider='box', texture='white_cube')

def spin():
    cube.animate('rotation_y', cube.rotation_y+360, duration=2, curve=curve.in_out_expo)
    cube.fade_out()

def add_small_cube():
    # cast a ray from the camera towards the mouse position
    hit_info = mouse.raycast
    if hit_info:
        pass
        # create a new cube at the collision point
        # small_cube = Entity(model='cube', color=hsv(200,1,1), scale=0.5, position=hit_info.world_point)
        # small_cube.parent = cube

cube.on_click = spin
cube.on_mouse_enter = add_small_cube
EditorCamera()  # add camera controls for orbiting and moving the camera

app.run()
