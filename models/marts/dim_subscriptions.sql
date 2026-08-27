SELECT DISTINCT sub_id, user_id, plan, status, mrr
FROM read_parquet('../data/curated/subscriptions.parquet')
