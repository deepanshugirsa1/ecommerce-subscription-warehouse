SELECT txn_id, user_id, amount, device_id
FROM read_parquet('../data/curated/transactions.parquet')
