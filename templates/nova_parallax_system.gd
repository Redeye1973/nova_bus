extends SceneTree

const ROOT := "L:/ZZZ ZZ NOVA GAME OUTPUT/31-05-2026/SM_Part1"
const VW := 480
const VH := 854
const SCALE := 1.5
const TILE_H := 270.0

func _initialize() -> void:
	_apply_parallax_system()
	print("nova_parallax_system: done")
	quit()

func _apply_parallax_system() -> void:
	_write_background_parallax_gd()
	_write_main_tscn()
	_store(ROOT + "/tools/nova_parallax_system.done", Time.get_datetime_string_from_system())

func _write_background_parallax_gd() -> void:
	var text := """extends Node2D

const VIEWPORT_H := 854.0
const TILE_H := 270.0
@export var scroll_speeds: Array[float] = [12.0, 28.0, 52.0, 88.0, 130.0]

func _ready() -> void:
	_ensure_tile_pairs()
	_apply_layer_alphas()

func _apply_layer_alphas() -> void:
	var alphas := [0.32, 0.48, 0.62, 0.78, 0.95]
	var bases: Array[Sprite2D] = []
	for child in get_children():
		if child is Sprite2D and not str(child.name).ends_with(\"B\"):
			bases.append(child)
	bases.sort_custom(func(a, b): return str(a.name) < str(b.name))
	for i in bases.size():
		var a: float = alphas[min(i, alphas.size() - 1)]
		var tint := Color(0.55 + a * 0.35, 0.58 + a * 0.3, 0.72 + a * 0.2, a)
		bases[i].modulate = tint
		var bname := bases[i].name + \"B\"
		if has_node(NodePath(bname)):
			get_node(NodePath(bname)).modulate = tint

func _ensure_tile_pairs() -> void:
	var bases: Array[Sprite2D] = []
	for child in get_children():
		if child is Sprite2D and not str(child.name).ends_with(\"B\"):
			bases.append(child)
	for sp in bases:
		var h := _layer_height(sp)
		var bname := sp.name + \"B\"
		if has_node(NodePath(String(sp.name) + \"B\")):
			var dup_existing := get_node(NodePath(bname)) as Sprite2D
			dup_existing.position = sp.position + Vector2(0, -h)
			continue
		var dup := sp.duplicate() as Sprite2D
		dup.name = bname
		dup.position = sp.position + Vector2(0, -h)
		add_child(dup)

func _layer_height(sp: Sprite2D) -> float:
	if sp.texture:
		return float(sp.texture.get_height()) * sp.scale.y
	return TILE_H

func _layer_index(sp: Sprite2D) -> int:
	var n := str(sp.name)
	if n.ends_with(\"B\"):
		n = n.substr(0, n.length() - 1)
	if n.begins_with(\"Layer\"):
		return max(int(n.substr(5)) - 1, 0)
	return 0

func _process(delta: float) -> void:
	for child in get_children():
		if not child is Sprite2D:
			continue
		var idx := _layer_index(child)
		var sp: float = scroll_speeds[min(idx, scroll_speeds.size() - 1)] if scroll_speeds.size() > 0 else 40.0
		child.position.y += sp * delta
		var h := _layer_height(child)
		if child.position.y >= VIEWPORT_H:
			child.position.y -= h * 2.0
"""
	_store(ROOT + "/scripts/background_parallax.gd", text)

func _write_main_tscn() -> void:
	var layers := [
		["Layer1", "bg_layer_1_sky.png", -10],
		["Layer2", "bg_layer_2_far.png", -9],
		["Layer3", "bg_layer_3_mid.png", -8],
		["Layer4", "bg_layer_4_near.png", -7],
		["Layer5", "bg_layer_5_detail.png", -6],
	]
	var ext := 10
	var body := ""
	var idx := 1
	for L in layers:
		body += "\\n[ext_resource type=\\\"Texture2D\\\" path=\\\"res://assets/backgrounds/%s\\\" id=\\\"%d\\\"]" % [L[1], idx]
		idx += 1
	var main := """[gd_scene load_steps=%d format=3]

[ext_resource type=\\\"Script\\\" path=\\\"res://scripts/background_parallax.gd\\\" id=\\\"1\\\"]
[ext_resource type=\\\"Script\\\" path=\\\"res://scripts/player.gd\\\" id=\\\"2\\\"]
[ext_resource type=\\\"Script\\\" path=\\\"res://scripts/spawner.gd\\\" id=\\\"3\\\"]
[ext_resource type=\\\"PackedScene\\\" path=\\\"res://scenes/bullet_player.tscn\\\" id=\\\"4\\\"]
[ext_resource type=\\\"PackedScene\\\" path=\\\"res://scenes/enemy_basic.tscn\\\" id=\\\"5\\\"]
[ext_resource type=\\\"Texture2D\\\" path=\\\"res://assets/sprites/player_ship.png\\\" id=\\\"6\\\"]
%s

[node name=\\\"Main\\\" type=\\\"Node2D\\\"]

[node name=\\\"BackgroundParallax\\\" type=\\\"Node2D\\\" parent=\\\".\\\"]
z_index = -100
script = ExtResource(\\\"1\\\")
""" % [ext, body]
	for i, L in enumerate(layers):
		main += """
[node name=\\\"%s\\\" type=\\\"Sprite2D\\\" parent=\\\"BackgroundParallax\\\"]
z_index = %d
position = Vector2(0, %d)
scale = Vector2(%s, %s)
centered = false
texture = ExtResource(\\\"%d\\\")
""" % [L[0], L[2], int(-TILE_H * i), SCALE, SCALE, i + 1]
	main += """
[node name=\\\"Player\\\" type=\\\"CharacterBody2D\\\" parent=\\\".\\\"]
z_index = 10
position = Vector2(240, 720)
script = ExtResource(\\\"2\\\")
bullet_scene = ExtResource(\\\"4\\\")

[node name=\\\"Sprite2D\\\" type=\\\"Sprite2D\\\" parent=\\\"Player\\\"]
texture = ExtResource(\\\"6\\\")

[node name=\\\"Spawner\\\" type=\\\"Node2D\\\" parent=\\\".\\\"]
z_index = 5
script = ExtResource(\\\"3\\\")
enemy_basic_scene = ExtResource(\\\"5\\\")
"""
	_store(ROOT + "/scenes/main.tscn", main)

func _store(path: String, text: String) -> void:
	var f := FileAccess.open(path, FileAccess.WRITE)
	if f:
		f.store_string(text)
