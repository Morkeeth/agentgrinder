-- 2026-09-13 · print the coach mode on hosted cards so demo and live are distinct.
-- Additive and nullable. Coordinator applies; this file is not executed against production here.

alter table public.runs
  add column if not exists coach_mode text;

comment on column public.runs.coach_mode is
  'Coach driver label, e.g. local scripted Strands loop vs Amazon Bedrock. Never treat a scripted sequence as autonomous reasoning.';
