-- Tier 3H.4C.3: align DB uniqueness contract with candidate ON CONFLICT idempotency target
-- Runtime idempotency target: (run_date_sgt, theme_name, candidate_asset_id, discovery_method)

-- Required duplicate audit query (run and review before/after migration):
-- SELECT
--   run_date_sgt,
--   theme_name,
--   candidate_asset_id,
--   discovery_method,
--   COUNT(*) AS duplicate_count
-- FROM public.tier3h_dynamic_entity_discovery
-- GROUP BY
--   run_date_sgt,
--   theme_name,
--   candidate_asset_id,
--   discovery_method
-- HAVING COUNT(*) > 1
-- ORDER BY duplicate_count DESC;

DO $$
DECLARE
  duplicate_group_count bigint;
BEGIN
  SELECT COUNT(*)
  INTO duplicate_group_count
  FROM (
    SELECT 1
    FROM public.tier3h_dynamic_entity_discovery
    GROUP BY run_date_sgt, theme_name, candidate_asset_id, discovery_method
    HAVING COUNT(*) > 1
  ) AS duplicate_groups;

  IF duplicate_group_count > 0 THEN
    RAISE NOTICE 'Skipping unique index creation for public.tier3h_dynamic_entity_discovery due to % duplicate key groups on (run_date_sgt, theme_name, candidate_asset_id, discovery_method). Deduplicate first (recommended keep newest by updated_at then id).', duplicate_group_count;
  ELSE
    CREATE UNIQUE INDEX IF NOT EXISTS idx_tier3h_dynamic_entity_discovery_idempotency
      ON public.tier3h_dynamic_entity_discovery (
        run_date_sgt,
        theme_name,
        candidate_asset_id,
        discovery_method
      );
  END IF;
END $$;
