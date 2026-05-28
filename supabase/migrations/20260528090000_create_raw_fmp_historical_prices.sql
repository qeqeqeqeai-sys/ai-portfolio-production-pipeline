create table if not exists public.raw_fmp_historical_prices (
  id uuid primary key default gen_random_uuid(),
  symbol text not null,
  price_date date not null,
  open numeric null,
  high numeric null,
  low numeric null,
  close numeric null,
  adj_close numeric null,
  volume numeric null,
  source text not null default 'fmp',
  endpoint_family text null,
  retrieved_at timestamptz not null default now(),
  payload_hash text null,
  created_at timestamptz not null default now(),
  unique(symbol, price_date, source)
);

create index if not exists idx_raw_fmp_historical_prices_symbol_date on public.raw_fmp_historical_prices(symbol, price_date);
create index if not exists idx_raw_fmp_historical_prices_price_date on public.raw_fmp_historical_prices(price_date);
create index if not exists idx_raw_fmp_historical_prices_retrieved_at on public.raw_fmp_historical_prices(retrieved_at);
