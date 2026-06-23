CREATE TABLE IF NOT EXISTS experiment_info (
	tenant_id LowCardinality(String),
	id UUID,
	name String,
	num_day Int32,
	status Int32,
	cur_day Int32,
	cur_t Float64,
	config String CODEC(ZSTD(3)),
	error String CODEC(ZSTD(3)),
	input_tokens Int64,
	output_tokens Int64,
	created_at DateTime64(3),
	updated_at DateTime64(3)
)
ENGINE = ReplacingMergeTree(updated_at)
ORDER BY (tenant_id, id)
PARTITION BY tenant_id;
