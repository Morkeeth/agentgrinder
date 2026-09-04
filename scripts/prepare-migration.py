"""Print the ordered, atomic product migration for review. Never connects to a database."""
from pathlib import Path
import re
root=Path(__file__).resolve().parents[1]
print('begin;')
print('''-- Existing production base tables and the 3 September coach migration are prerequisites.
do $$ begin
 if to_regclass('public.profiles') is null or to_regclass('public.runs') is null or to_regclass('public.acks') is null then
  raise exception 'The existing profiles/runs/acks schema is required';
 end if;
end $$;''')
for name in (root/'scripts/migration-order.txt').read_text().splitlines():
    text=(root/'supabase/migrations'/name).read_text()
    text=re.sub(r'^\s*(begin|commit);\s*$', '', text, flags=re.M|re.I)
    print('-- '+name+'\n'+text)
print('commit;')
