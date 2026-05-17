CREATE OR REPLACE FUNCTION public.get_unique_constraints_for_table(
    target_table text
)
RETURNS TABLE (
    constraint_name text,
    column_names text[]
)
LANGUAGE sql
SECURITY DEFINER
AS $$
SELECT
    tc.constraint_name::text,
    array_agg(
        kcu.column_name::text
        ORDER BY kcu.ordinal_position
    ) AS column_names
FROM information_schema.table_constraints tc
JOIN information_schema.key_column_usage kcu
    ON tc.constraint_name = kcu.constraint_name
   AND tc.table_schema = kcu.table_schema
   AND tc.table_name = kcu.table_name
WHERE tc.constraint_type = 'UNIQUE'
  AND tc.table_schema = 'public'
  AND tc.table_name = target_table
GROUP BY tc.constraint_name;
$$;
