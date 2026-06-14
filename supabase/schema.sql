-- Claude Code Duolingo — esquema de base de datos (Postgres / Supabase)
-- Contenido como datos vive en el repo; aquí solo el ESTADO del usuario.

create table if not exists profiles (
  id          uuid primary key references auth.users(id) on delete cascade,
  username    text unique not null,
  is_admin    boolean not null default false,
  xp          integer not null default 0,
  streak_days integer not null default 0,
  created_at  timestamptz not null default now(),
  last_active timestamptz not null default now()
);

create table if not exists lesson_progress (
  user_id      uuid references profiles(id) on delete cascade,
  lesson_id    text not null,
  status       text not null default 'in_progress', -- in_progress | completed | mastered
  score        integer,
  attempts     integer not null default 0,
  completed_at timestamptz,
  primary key (user_id, lesson_id)
);

create table if not exists user_badges (
  user_id   uuid references profiles(id) on delete cascade,
  badge_id  text not null,
  earned_at timestamptz not null default now(),
  primary key (user_id, badge_id)
);

create table if not exists activity_log (
  id         bigint generated always as identity primary key,
  user_id    uuid references profiles(id) on delete cascade,
  event      text not null,
  payload    jsonb,
  created_at timestamptz not null default now()
);

-- Suma XP y registra actividad de forma segura (SECURITY DEFINER).
create or replace function add_xp(amount integer)
returns void language plpgsql security definer as $$
begin
  update profiles set xp = xp + amount, last_active = now() where id = auth.uid();
  insert into activity_log(user_id, event, payload)
    values (auth.uid(), 'xp_earned', jsonb_build_object('amount', amount));
end; $$;

-- ---------- Row Level Security ----------
alter table profiles        enable row level security;
alter table lesson_progress enable row level security;
alter table user_badges     enable row level security;
alter table activity_log    enable row level security;

create policy "own_profile"  on profiles
  for all using (auth.uid() = id) with check (auth.uid() = id);
create policy "own_progress" on lesson_progress
  for all using (auth.uid() = user_id) with check (auth.uid() = user_id);
create policy "own_badges"   on user_badges
  for all using (auth.uid() = user_id) with check (auth.uid() = user_id);
create policy "own_activity" on activity_log
  for all using (auth.uid() = user_id) with check (auth.uid() = user_id);

-- El admin puede LEER todos los perfiles (para estadísticas).
create policy "admin_reads_profiles" on profiles
  for select using (
    exists (select 1 from profiles p where p.id = auth.uid() and p.is_admin)
  );
