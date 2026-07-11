import { createClient } from '@supabase/supabase-js'

export const supabase = createClient(
  import.meta.env.VITE_SUPABASE_URL,
  import.meta.env.VITE_SUPABASE_ANON_KEY
)

export const PUB_R2 = 'https://pub-04c202b65f234888bf415f2ec899d7f8.r2.dev'
