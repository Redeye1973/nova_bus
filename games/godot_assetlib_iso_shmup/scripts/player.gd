extends CharacterBody3D
## Player: KayKit spacetruck (#2124). WASD / arrows on XZ playfield.

const SPEED := 9.0


func _ready() -> void:
	var hb := get_node_or_null(^"Hurtbox") as Area3D
	if hb:
		hb.area_entered.connect(_on_hurtbox_area_entered)


func _physics_process(delta: float) -> void:
	if not GameState.running:
		return
	var inp := Input.get_vector(&"ui_left", &"ui_right", &"ui_up", &"ui_down")
	var dir := Vector3(inp.x, 0.0, -inp.y)
	velocity = dir * SPEED
	move_and_slide()


func _on_hurtbox_area_entered(area: Area3D) -> void:
	if area.is_in_group(&"enemies") and GameState.running:
		GameState.player_hit()
		area.queue_free()
