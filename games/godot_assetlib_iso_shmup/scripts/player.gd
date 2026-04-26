extends CharacterBody3D
## Player: KayKit spacetruck (Asset Library #2124). WASD / arrows on XZ playfield.

const SPEED := 9.0

func _physics_process(delta: float) -> void:
	var inp := Input.get_vector(&"ui_left", &"ui_right", &"ui_up", &"ui_down")
	var dir := Vector3(inp.x, 0.0, -inp.y)
	velocity = dir * SPEED
	move_and_slide()
