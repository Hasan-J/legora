from typing import Union

import dagster as dg

from legora_dagster.defs.assets import extract_decisions, transform_decisions

partitioned_asset_job = dg.define_asset_job(
    "monthly_decisions_job", selection=[extract_decisions, transform_decisions])

asset_partitioned_schedule = dg.build_schedule_from_partitioned_job(
    partitioned_asset_job
)
