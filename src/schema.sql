create table
  public.carts (
    id bigint generated by default as identity,
    created_at timestamp with time zone not null default now(),
    customer_name text null,
    constraint carts_pkey1 primary key (id)
  ) tablespace pg_default;


create table
  public.cart_items (
    cart_id bigint generated by default as identity,
    created_at timestamp with time zone not null default now(),
    catalog_id bigint null,
    quantity integer null,
    constraint carts_pkey primary key (cart_id)
  ) tablespace pg_default;


create table
  public.catalog (
    id bigint generated by default as identity,
    created_at timestamp with time zone not null default now(),
    sku text null,
    price integer null,
    potion_type jsonb null,
    inventory integer null,
    red integer null default 0,
    blue integer null default 0,
    green integer null default 0,
    dark integer null default 0,
    constraint catalog_pkey primary key (id)
  ) tablespace pg_default;
