-- Sync Supabase Auth (`auth.users`) with app profile rows (`iam.users`).
-- After each `auth.users` insert, upsert a row in `iam.users` with the same UUID (auth and profile are separate entities).
-- Application code must not INSERT/UPSERT `iam.users`; only this trigger writes profile rows (see UserService.ensureAppUserFromSupabaseAuth).
-- Versioned here so `migrate deploy` reproduces the same trigger in every environment.
-- If this fails on hosted Supabase (rare permission edge cases on `auth`), run the same statements in the SQL Editor,
-- then: `pnpm exec prisma migrate resolve --applied 20260414000000_on_auth_user_created` from `packages/db`.

DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;

CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = ''
AS $$
DECLARE
  v_email TEXT;
  v_name  TEXT;
  v_phone TEXT;
BEGIN
  v_email := COALESCE(NEW.email, NEW.id::TEXT || '@users.local');
  v_name := COALESCE(
    NULLIF(TRIM(NEW.raw_user_meta_data->>'full_name'), ''),
    NULLIF(TRIM(NEW.raw_user_meta_data->>'name'), ''),
    NULLIF(SPLIT_PART(COALESCE(NEW.email, ''), '@', 1), ''),
    'User'
  );
  v_phone := COALESCE(
    NULLIF(TRIM(NEW.phone), ''),
    '+' || REPLACE(NEW.id::TEXT, '-', '')
  );

  INSERT INTO iam.users (
    id,
    name,
    email,
    phone,
    is_active,
    is_platform_admin
  )
  VALUES (
    NEW.id,
    v_name,
    v_email,
    v_phone,
    false,
    false
  )
  ON CONFLICT (id) DO UPDATE SET
    email = EXCLUDED.email,
    name = EXCLUDED.name,
    phone = EXCLUDED.phone,
    updated_at = CURRENT_TIMESTAMP;

  RETURN NEW;
END;
$$;

CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW
  EXECUTE FUNCTION public.handle_new_user();
