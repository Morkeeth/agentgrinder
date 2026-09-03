-- 2026-09-03 · the coach's numbers on the hosted card.
--
-- Adds the five-number parts and the coach verdict to public.runs. Every column is nullable and
-- nothing here drops, renames or rewrites anything: a run posted before this migration keeps
-- every value it had, and site/index.html renders a dash for each null.
--
-- Apply by hand (the coordinator does this; the build lane never runs it):
--   supabase db push            or paste into the SQL editor of the live project.
-- Safe to run twice: every statement is IF NOT EXISTS.

alter table public.runs
  add column if not exists claims             integer,   -- claim lines the agent wrote in the sitting
  add column if not exists claims_verified    integer,   -- of those, with evidence in their own turn
  add column if not exists artifacts_produced integer,   -- files the run wrote that exist at close
  add column if not exists coach_verdict      text,      -- the coach's one paragraph
  add column if not exists coach_plan         text,      -- the next-session plan, newline separated
  add column if not exists coach_tool_calls   integer,   -- tool calls the Strands hook logged
  add column if not exists progress_verdict   text;      -- baseline | helped | hurt | unchanged, vs your last grind on the project

comment on column public.runs.claims is 'claim lines the agent wrote (agentgrinder claims.py rule, v0, over-counts)';
comment on column public.runs.claims_verified is 'claims with tool evidence in the same human turn';
comment on column public.runs.artifacts_produced is 'Edit/Write paths that existed when the card was drawn';
comment on column public.runs.coach_verdict is 'the grind coach paragraph; every number in it came from a tool result';
comment on column public.runs.coach_plan is 'the grind coach next-session plan, one line per item';
comment on column public.runs.coach_tool_calls is 'tool calls the Strands AfterToolCallEvent hook logged for this verdict';
comment on column public.runs.progress_verdict is 'this grind vs the previous grind on the same project, by verified per turn';
