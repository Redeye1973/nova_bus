extends Area3D
## Projectile: KayKit solarpanel (#2124). Destroys enemies on overlap; layer "bullet".

@export var speed: float = 22.0


func _ready() -> void:
	add_to_group(&"bullets")
	area_entered.connect(_on_area_entered)


func _physics_process(delta: float) -> void:
	if not GameState.running:
		return
	position.z -= speed * delta
	if position.z < -30.0:
		queue_free()


func _on_area_entered(area: Area3D) -> void:
	if area.is_in_group(&"enemies"):
		GameState.add_points(100)
		area.queue_free()
		queue_free()
