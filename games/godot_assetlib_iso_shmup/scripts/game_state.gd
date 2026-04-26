extends Node
## Run stats for the shmup; autoload singleton.

signal stats_changed

var score: int = 0
var lives: int = 3
var running: bool = true


func reset_game() -> void:
	score = 0
	lives = 3
	running = true
	stats_changed.emit()


func add_points(amount: int) -> void:
	if not running:
		return
	score += amount
	stats_changed.emit()


func player_hit() -> void:
	if not running:
		return
	lives -= 1
	stats_changed.emit()
	if lives <= 0:
		running = false
		stats_changed.emit()
