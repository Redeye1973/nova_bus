extends CanvasLayer
## Score / lives / game-over overlay; reads GameState autoload.

@onready var _score: Label = %ScoreLabel
@onready var _lives: Label = %LivesLabel
@onready var _overlay: ColorRect = %GameOverOverlay
@onready var _hint: Label = %RestartHint


func _ready() -> void:
	GameState.stats_changed.connect(_refresh)
	_refresh()


func _refresh() -> void:
	_score.text = "Score: %d" % GameState.score
	_lives.text = "Lives: %d" % GameState.lives
	var over := not GameState.running
	_overlay.visible = over
	_hint.visible = over
