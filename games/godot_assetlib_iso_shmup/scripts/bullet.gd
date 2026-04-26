extends Node3D
## Projectile visual: KayKit solarpanel (#2124), flies toward -Z.

@export var speed: float = 22.0

func _physics_process(delta: float) -> void:
	position.z -= speed * delta
	if position.z < -30.0:
		queue_free()
