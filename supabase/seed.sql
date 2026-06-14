-- Crea el usuario admin/admin para arranque/demo.
-- ADVERTENCIA: admin/admin es una credencial débil. Forzar cambio de contraseña
-- en el primer login antes de cualquier uso real.
--
-- Ejecuta esto tras crear el usuario 'admin@local' vía Supabase Auth
-- (Dashboard > Authentication > Add user, email admin@local, password admin).
-- Después marca su perfil como admin:

insert into profiles (id, username, is_admin)
select id, 'admin', true
from auth.users
where email = 'admin@local'
on conflict (id) do update set is_admin = true;
