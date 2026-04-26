extends Area3D
## Enemy drifting toward +Z; mesh KayKit structure_low (#2124). Collision layer "enemy".

@export var speed: float = 4.5


func _ready() -> void:
	add_to_group(&"enemies")


func _physics_process(delta: float) -> void:
	if not GameState.running:
		return
	position.z += speed * delta
	if position.z > 28.0:
		queue_free()
