ALTER TABLE experiment_info ADD COLUMN IF NOT EXISTS last_mobility_safe_step Int32 DEFAULT -1;
ALTER TABLE experiment_info ADD COLUMN IF NOT EXISTS prev_mobility_safe_step Int32 DEFAULT -1;
ALTER TABLE experiment_info ADD COLUMN IF NOT EXISTS economy_checkpoint_path String DEFAULT '';
