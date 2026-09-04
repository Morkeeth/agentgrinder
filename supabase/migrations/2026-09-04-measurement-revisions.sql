-- Additive references to immutable local measurements. These references establish no
-- independent verification of client-submitted counts.
alter table public.runs
  add column if not exists schema_version integer,
  add column if not exists measurement_revision text,
  add column if not exists baseline_revision text,
  add column if not exists progress_delta double precision,
  add column if not exists trace_basis text,
  add column if not exists route jsonb,
  add column if not exists rhythm jsonb,
  add column if not exists note text;

comment on column public.runs.measurement_revision is 'Opaque local measurement revision; not independent attestation';
comment on column public.runs.baseline_revision is 'Frozen local revision used for this comparison';

-- Native durations can include fractions of a second. Preserve the measured value.
alter table public.runs alter column duration_s type double precision;
