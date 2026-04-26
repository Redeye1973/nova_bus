extends Control
## Fancy line/particle background — adapted from Asset Library #1539 (MIT, Ark2000 / k2kra).
## Original: https://godotengine.org/asset-library/asset/1539
## When follow_mouse is false, the first point stays at the control center (shmup-friendly).

@export var follow_mouse: bool = false
@export var max_points: int = 60
@export var fade_time: float = 2.0
@export var max_line_length: float = 160.0
@export var interact_intension: float = 3000.0
@export var min_radius: float = 0.5
@export var max_radius: float = 3.0
@export var min_velocity: float = 20.0
@export var max_velocity: float = 60.0
@export var point_color: Color = Color(0.15, 0.35, 0.85, 1.0)
@export var line_color: Color = Color(0.5, 0.7, 1.0, 1.0)

var _points: Array = []


class Po:
	var position: Vector2
	var velocity: Vector2
	var radius: float
	var life: float
	var velocity2: Vector2


func _ready() -> void:
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	for i in range(max_points):
		_points.push_back(_reset_po(Po.new()))


func _reset_po(po: Po) -> Po:
	var r := get_rect()
	po.position = Vector2(randf() * r.size.x, randf() * r.size.y)
	po.velocity = Vector2.RIGHT.rotated(randf() * TAU) * randf_range(min_velocity, max_velocity)
	po.radius = randf_range(min_radius, max_radius)
	po.life = 0.0
	po.velocity2 = Vector2.ZERO
	return po


func _physics_process(delta: float) -> void:
	for po in _points:
		if not get_rect().has_point(po.position):
			po.life -= delta
			if po.life < 0.0:
				_reset_po(po)
		else:
			po.life = minf(po.life + delta, fade_time)
		po.position += (po.velocity + po.velocity2) * delta
	if _points.size() > 0:
		if follow_mouse:
			_points[0].position = get_local_mouse_position()
		else:
			_points[0].position = get_rect().get_center()
	queue_redraw()


func _draw() -> void:
	if _points.is_empty():
		return
	var p_mouse_pos: Vector2 = _points[0].position
	var p_a: Po
	var p_b: Po
	var p_color: Color
	var l_color: Color
	for a in range(_points.size()):
		p_a = _points[a]
		p_color = point_color
		p_color.a = p_a.life / fade_time
		draw_circle(p_a.position, p_a.radius, p_color)
		var mouse_dist := p_a.position.distance_to(p_mouse_pos)
		if mouse_dist < max_line_length and a != 0:
			p_a.velocity2 = (p_a.position - p_mouse_pos).normalized() * (1.0 / mouse_dist) * interact_intension
		else:
			p_a.velocity2 = Vector2.ZERO
		for b in range(_points.size()):
			if a <= b:
				continue
			p_b = _points[b]
			var distance := p_a.position.distance_to(p_b.position)
			if distance < max_line_length:
				l_color = line_color
				l_color.a = (1.0 - distance / max_line_length) * minf(p_a.life, p_b.life) / fade_time
				draw_line(p_a.position, p_b.position, l_color, 2.0 * (1.0 - distance / max_line_length))
