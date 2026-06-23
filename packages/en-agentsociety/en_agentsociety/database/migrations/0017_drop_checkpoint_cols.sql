ALTER TABLE experiment_info DROP COLUMN IF EXISTS last_mobility_safe_step;
ALTER TABLE experiment_info DROP COLUMN IF EXISTS prev_mobility_safe_step;
ALTER TABLE experiment_info DROP COLUMN IF EXISTS economy_checkpoint_path