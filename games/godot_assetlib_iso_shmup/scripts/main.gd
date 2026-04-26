extends Node3D
## Spawns enemies; Space fires bullets. Meshes #2124; background #1539. GameState autoload.

@onready var _player: Node3D = $Player
var _enemy_scene: PackedScene = preload("res://scenes/enemy.tscn")
var _bullet_scene: PackedScene = preload("res://scenes/bullet.tscn")
var _spawn_timer: Timer
var _base_spawn: float = 2.0
var _wave: int = 0


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	_spawn_timer = Timer.new()
	_spawn_timer.wait_time = _base_spawn
	_spawn_timer.timeout.connect(_on_spawn_enemy)
	add_child(_spawn_timer)
	_spawn_timer.start()
	GameState.stats_changed.connect(_on_stats_changed)
	_on_stats_changed()


func _on_stats_changed() -> void:
	_spawn_timer.paused = not GameState.running


func _on_spawn_enemy() -> void:
	if not GameState.running:
		return
	var e: Node3D = _enemy_scene.instantiate()
	e.position = Vector3(randf_range(-5.0, 5.0), 0.0, -18.0)
	add_child(e)
	_wave += 1
	var t := maxf(0.55, _base_spawn - float(_wave) * 0.04)
	_spawn_timer.wait_time = t


func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed(&"ui_accept"):
		if not GameState.running:
			_restart_run()
		else:
			var b: Node3D = _bullet_scene.instantiate()
			b.global_position = _player.global_position + Vector3(0.0, 0.6, -1.2)
			add_child(b)


func _restart_run() -> void:
	GameState.reset_game()
	_wave = 0
	_spawn_timer.wait_time = _base_spawn
	for n in get_tree().get_nodes_in_group(&"enemies"):
		n.queue_free()
	for n in get_tree().get_nodes_in_group(&"bullets"):
		n.queue_free()
