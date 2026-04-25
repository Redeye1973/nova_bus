INSERT INTO pipeline_budgets VALUES
    ('ship_sprite_test', 0.50, 600, 30, 100, 80)
ON CONFLICT (pipeline_type) DO NOTHING;
