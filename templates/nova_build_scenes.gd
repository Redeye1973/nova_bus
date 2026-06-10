extends SceneTree

const ROOT := "L:/ZZZ ZZ NOVA GAME OUTPUT/31-05-2026/SM_Part1"
const OUT := "L:/ZZZ ZZ NOVA GAME OUTPUT/31-05-2026/SM_Part1"

const SCRIPTS := {
	"player.gd": """extends CharacterBody2D
const SPEED := 300.0
const MINIGUN_RATE := 0.05
const MISSILE_COOLDOWN := 0.8
const MOUSE_LERP := 8.0
var health := 100
var shield := false
var _minigun_cd := 0.0
var _missile_cd := 0.0
@export var bullet_scene: PackedScene
@export var missile_scene: PackedScene

func _physics_process(delta: float) -> void:
	var vp := get_viewport_rect().size
	var mouse := get_viewport().get_mouse_position()
	var target := mouse.clamp(Vector2(16, 16), vp - Vector2(16, 16))
	var dir := Vector2.ZERO
	if Input.is_action_pressed("ui_left"): dir.x -= 1
	if Input.is_action_pressed("ui_right"): dir.x += 1
	if Input.is_action_pressed("ui_up"): dir.y -= 1
	if Input.is_action_pressed("ui_down"): dir.y += 1
	if dir.length() > 0.0:
		velocity = dir.normalized() * SPEED
		move_and_slide()
	else:
		position = position.lerp(target, MOUSE_LERP * delta)
	position.x = clamp(position.x, 16, vp.x - 16)
	position.y = clamp(position.y, 16, vp.y - 16)
	_minigun_cd = max(_minigun_cd - delta, 0.0)
	_missile_cd = max(_missile_cd - delta, 0.0)
	if (Input.is_mouse_button_pressed(MOUSE_BUTTON_LEFT) or Input.is_action_pressed("ui_accept")) and _minigun_cd <= 0.0 and bullet_scene:
		_fire_minigun()
	if Input.is_mouse_button_pressed(MOUSE_BUTTON_RIGHT) and _missile_cd <= 0.0 and missile_scene:
		_fire_missile()

func _fire_minigun() -> void:
	_minigun_cd = MINIGUN_RATE
	var b = bullet_scene.instantiate()
	b.global_position = global_position + Vector2(randf_range(-4, 4), -8)
	var spread := randf_range(-0.12, 0.12)
	b.direction = Vector2.UP.rotated(spread)
	b.speed = 520.0
	b.damage = 5
	get_tree().current_scene.add_child(b)

func _fire_missile() -> void:
	_missile_cd = MISSILE_COOLDOWN
	var m = missile_scene.instantiate()
	m.global_position = global_position + Vector2(0, -12)
	get_tree().current_scene.add_child(m)

func take_damage(amount: int) -> void:
	if shield: return
	health -= amount
	if health <= 0: queue_free()
""",
	"background_parallax.gd": """extends Node2D
@export var scroll_speeds: Array = [20, 40, 80, 120, 160]

func _process(delta: float) -> void:
	var i := 0
	for child in get_children():
		if not child is Sprite2D: continue
		var sp := scroll_speeds[min(i, scroll_speeds.size()-1)] if scroll_speeds.size() > 0 else 40
		child.position.y += sp * delta
		var h := child.texture.get_height() if child.texture else 180
		if child.position.y > get_viewport_rect().size.y: child.position.y -= h * 2
		i += 1
""",
	"spawner.gd": """extends Node2D
@export var enemy_basic_scene: PackedScene
@export var enemy_tank_scene: PackedScene
var _timer := 0.0
var _toggle := false

func _process(delta: float) -> void:
	_timer += delta
	if _timer < 2.0: return
	_timer = 0.0
	var scene = enemy_tank_scene if _toggle else enemy_basic_scene
	_toggle = not _toggle
	if scene:
		var e = scene.instantiate()
		e.global_position = Vector2(randf_range(32, get_viewport_rect().size.x - 32), -16)
		add_child(e)
""",
	"enemy_basic.gd": """extends CharacterBody2D
const SPEED := 80.0
var health := 30
var _shoot := 0.0
@export var bullet_scene: PackedScene

func _physics_process(delta: float) -> void:
	velocity = Vector2.DOWN * SPEED
	move_and_slide()
	_shoot += delta
	if _shoot >= 1.5 and bullet_scene:
		_shoot = 0.0
		var b = bullet_scene.instantiate()
		b.global_position = global_position
		b.direction = Vector2.DOWN
		get_tree().current_scene.add_child(b)
	if global_position.y > get_viewport_rect().size.y + 32: queue_free()

func take_damage(amount: int) -> void:
	health -= amount
	if health <= 0: queue_free()
""",
	"bullet.gd": """extends Area2D
@export var speed := 400.0
@export var direction := Vector2.UP
@export var damage := 10

func _physics_process(delta: float) -> void:
	position += direction.normalized() * speed * delta
	var vp := get_viewport_rect().size
	if position.x < -16 or position.x > vp.x + 16 or position.y < -16 or position.y > vp.y + 16:
		queue_free()

func _on_body_entered(body: Node) -> void:
	if body.has_method("take_damage"): body.take_damage(damage)
	queue_free()
""",
	"missile.gd": """extends Area2D
@export var speed := 260.0
@export var damage := 40
@export var turn_rate := 3.5
var direction := Vector2.UP

func _physics_process(delta: float) -> void:
	var target := _nearest_enemy()
	if target:
		var desired := (target.global_position - global_position).normalized()
		direction = direction.lerp(desired, turn_rate * delta).normalized()
	position += direction * speed * delta
	var vp := get_viewport_rect().size
	if position.x < -32 or position.x > vp.x + 32 or position.y < -32 or position.y > vp.y + 32:
		queue_free()

func _nearest_enemy() -> Node2D:
	var best: Node2D = null
	var best_d := 999999.0
	for node in get_tree().current_scene.get_children():
		if node == self.get_parent(): continue
		if node is CharacterBody2D and node.has_method("take_damage") and node != get_tree().current_scene.get_node_or_null("Player"):
			var d := global_position.distance_squared_to(node.global_position)
			if d < best_d:
				best_d = d
				best = node
	return best

func _on_body_entered(body: Node) -> void:
	if body.has_method("take_damage"): body.take_damage(damage)
	queue_free()
""",
}

func _initialize() -> void:
	_write_scripts()
	_write_scenes()
	_write_play_txt()
	_mirror_output()
	print("nova_build_scenes: done")
	quit()

func _write_scripts() -> void:
	var dir := ROOT + "/scripts"
	DirAccess.make_dir_recursive_absolute(dir)
	for name in SCRIPTS:
		var f := FileAccess.open(dir + "/" + name, FileAccess.WRITE)
		if f: f.store_string(SCRIPTS[name])

func _write_scenes() -> void:
	var scenes := ROOT + "/scenes"
	DirAccess.make_dir_recursive_absolute(scenes)
	var bullet := """[gd_scene load_steps=3 format=3]

[ext_resource type="Script" path="res://scripts/bullet.gd" id="1"]
[ext_resource type="Texture2D" path="res://assets/sprites/bullet_player.png" id="2"]

[node name="Bullet" type="Area2D"]
script = ExtResource("1")

[node name="Sprite2D" type="Sprite2D" parent="."]
texture = ExtResource("2")

[node name="CollisionShape2D" type="CollisionShape2D" parent="."]
"""
	var enemy := """[gd_scene load_steps=4 format=3]

[ext_resource type="Script" path="res://scripts/enemy_basic.gd" id="1"]
[ext_resource type="PackedScene" path="res://scenes/bullet_enemy.tscn" id="2"]
[ext_resource type="Texture2D" path="res://assets/sprites/enemy_fighter.png" id="3"]

[node name="EnemyBasic" type="CharacterBody2D"]
script = ExtResource("1")
bullet_scene = ExtResource("2")

[node name="Sprite2D" type="Sprite2D" parent="."]
texture = ExtResource("3")
"""
	var bullet_enemy := """[gd_scene load_steps=3 format=3]

[ext_resource type="Script" path="res://scripts/bullet.gd" id="1"]
[ext_resource type="Texture2D" path="res://assets/sprites/bullet_enemy.png" id="2"]

[node name="BulletEnemy" type="Area2D"]
script = ExtResource("1")
direction = Vector2(0, 1)

[node name="Sprite2D" type="Sprite2D" parent="."]
texture = ExtResource("2")
"""
	var main := """[gd_scene load_steps=11 format=3]

[ext_resource type="Script" path="res://scripts/background_parallax.gd" id="1"]
[ext_resource type="Script" path="res://scripts/player.gd" id="2"]
[ext_resource type="Script" path="res://scripts/spawner.gd" id="3"]
[ext_resource type="PackedScene" path="res://scenes/bullet_player.tscn" id="4"]
[ext_resource type="PackedScene" path="res://scenes/enemy_basic.tscn" id="5"]
[ext_resource type="Texture2D" path="res://assets/sprites/player_ship.png" id="6"]
[ext_resource type="Texture2D" path="res://assets/backgrounds/bg_layer_1_sky.png" id="7"]
[ext_resource type="Texture2D" path="res://assets/backgrounds/bg_layer_2_far.png" id="8"]
[ext_resource type="Texture2D" path="res://assets/backgrounds/bg_layer_3_mid.png" id="9"]
[ext_resource type="PackedScene" path="res://scenes/missile_player.tscn" id="10"]

[node name="Main" type="Node2D"]

[node name="BackgroundParallax" type="Node2D" parent="."]
script = ExtResource("1")

[node name="Layer1" type="Sprite2D" parent="BackgroundParallax"]
texture = ExtResource("7")
centered = false

[node name="Layer2" type="Sprite2D" parent="BackgroundParallax"]
texture = ExtResource("8")
centered = false

[node name="Layer3" type="Sprite2D" parent="BackgroundParallax"]
texture = ExtResource("9")
centered = false

[node name="Player" type="CharacterBody2D" parent="."]
z_index = 10
position = Vector2(160, 200)
script = ExtResource("2")
bullet_scene = ExtResource("4")
missile_scene = ExtResource("10")

[node name="Sprite2D" type="Sprite2D" parent="Player"]
texture = ExtResource("6")

[node name="Spawner" type="Node2D" parent="."]
z_index = 5
script = ExtResource("3")
enemy_basic_scene = ExtResource("5")
"""
	var missile := """[gd_scene load_steps=3 format=3]

[ext_resource type="Script" path="res://scripts/missile.gd" id="1"]
[ext_resource type="Texture2D" path="res://assets/sprites/bullet_player.png" id="2"]

[node name="MissilePlayer" type="Area2D"]
scale = Vector2(1.5, 1.5)
script = ExtResource("1")

[node name="Sprite2D" type="Sprite2D" parent="."]
modulate = Color(1, 0.6, 0.2, 1)
texture = ExtResource("2")

[node name="CollisionShape2D" type="CollisionShape2D" parent="."]
"""
	_store(scenes + "/bullet_player.tscn", bullet)
	_store(scenes + "/bullet_enemy.tscn", bullet_enemy)
	_store(scenes + "/enemy_basic.tscn", enemy)
	_store(scenes + "/missile_player.tscn", missile)
	_store(scenes + "/main.tscn", main)
	var pg_path := ROOT + "/project.godot"
	if FileAccess.file_exists(pg_path):
		var pg := FileAccess.get_file_as_string(pg_path)
		if "run/main_scene" not in pg:
			pg += '\nrun/main_scene="res://scenes/main.tscn"\n'
			_store(pg_path, pg)

func _write_play_txt() -> void:
	DirAccess.make_dir_recursive_absolute(OUT)
	var txt := """SM_Part1 — NOVA Shmup Part 1
Open in Godot 4.x:
  Project: L:/ZZZ ZZ NOVA GAME OUTPUT/31-05-2026/SM_Part1/project.godot
Press F5 to play (main scene: scenes/main.tscn)
Controls: Mouse move (or arrows), LMB minigun, RMB missiles, Space minigun fallback
"""
	_store(OUT + "/PLAY.txt", txt)

func _mirror_output() -> void:
	DirAccess.make_dir_recursive_absolute(OUT)
	DirAccess.make_dir_recursive_absolute(OUT + "/scripts")
	DirAccess.make_dir_recursive_absolute(OUT + "/scenes")
	for name in SCRIPTS:
		_copy_file(ROOT + "/scripts/" + name, OUT + "/scripts/" + name)
	for s in ["main.tscn", "bullet_player.tscn", "bullet_enemy.tscn", "enemy_basic.tscn", "missile_player.tscn"]:
		_copy_file(ROOT + "/scenes/" + s, OUT + "/scenes/" + s)
	_copy_file(ROOT + "/project.godot", OUT + "/project.godot")

func _store(path: String, text: String) -> void:
	var f := FileAccess.open(path, FileAccess.WRITE)
	if f: f.store_string(text)

func _copy_file(src: String, dst: String) -> void:
	if FileAccess.file_exists(src):
		_store(dst, FileAccess.get_file_as_string(src))
