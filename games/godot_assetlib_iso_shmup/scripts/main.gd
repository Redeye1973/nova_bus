extends Node3D
## Spawns enemies; Space spawns bullets. Asset Library meshes only (#2124).

@onready var _player: Node3D = $Player
var _enemy_scene: PackedScene = preload("res://scenes/enemy.tscn")
var _bullet_scene: PackedScene = preload("res://scenes/bullet.tscn")
var _spawn_timer: Timer

func _ready() -> void:
	_spawn_timer = Timer.new()
	_spawn_timer.wait_time = 2.0
	_spawn_timer.timeout.connect(_on_spawn_enemy)
	add_child(_spawn_timer)
	_spawn_timer.start()

func _on_spawn_enemy() -> void:
	var e: Node3D = _enemy_scene.instantiate()
	e.position = Vector3(randf_range(-5.0, 5.0), 0.0, -18.0)
	add_child(e)

func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed("ui_accept"):
		var b: Node3D = _bullet_scene.instantiate()
		b.global_position = _player.global_position + Vector3(0.0, 0.6, -1.2)
		add_child(b)
