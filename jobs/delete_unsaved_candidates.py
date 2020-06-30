#!/usr/bin/env python

import datetime
from skyportal.models import init_db, Candidate, Source, Obj, DBSession
from baselayer.app.env import load_env


env, cfg = load_env()
init_db(**cfg["database"])

try:
    n_days = int(cfg["misc.days_to_keep_unsaved_candidates"])
except ValueError:
    raise ValueError("Invalid (non-integer) value provided for "
                     "days_to_keep_unsaved_candidates in config file.")

if not 1 <= n_days <= 30:
    raise ValueError("days_to_keep_unsaved_candidates must be an integer between 1 and 30")

cutoff_datetime = datetime.datetime.now() - datetime.timedelta(days=n_days)

n_deleted = (
    Obj.query
    .filter(Obj.id.in_(DBSession.query(Candidate.obj_id)))
    .filter(Obj.id.notin_(DBSession.query(Source.obj_id)))
    .filter(Obj.created_at <= cutoff_datetime)
    .delete()
)

DBSession.commit()

print(f"Deleted {n_deleted} unsaved candidates.")
