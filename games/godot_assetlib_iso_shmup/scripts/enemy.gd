extends Node3D
## Enemy block drifting toward +Z (camera iso); mesh from KayKit structure_low (#2124).

@export var speed: float = 4.5

func _physics_process(delta: float) -> void:
	position.z += speed * delta
	if position.z > 28.0:
		queue_free()
