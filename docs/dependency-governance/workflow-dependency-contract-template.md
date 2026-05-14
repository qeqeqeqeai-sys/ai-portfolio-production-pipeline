# Workflow Dependency Contract Template

Use this template for each production or scheduled workflow.

## Workflow

| Field | Value |
|---|---|
| Workflow filename | `<workflow>.yml` |
| Workflow display name | `<github.workflow>` |
| Runtime layer | GitHub Actions |
| Owner | TBD |
| Run mode | scheduled / manual / replay / backfill |
| Criticality | low / medium / high / critical |

## Trigger

| Trigger | Details |
|---|---|
| Schedule | TBD |
| Manual dispatch | yes/no |
| Downstream consumers | TBD |

## Upstream dependencies

| Dependency type | Name | Required freshness | Required partition | Minimum rows | Fail policy |
|---|---|---:|---|---:|---|
| table | `<table_name>` | `<N hours>` | `run_date_sgt = today` | `> 0` | warn/fail |
| workflow | `<workflow_name>` | `<N hours>` | same run date | n/a | warn/fail |

## Outputs

| Output type | Name | Partition key | Expected rows | Consumer |
|---|---|---|---:|---|
| table | `<table_name>` | `run_date_sgt` | TBD | TBD |

## Locking policy

| Field | Value |
|---|---|
| Requires lock | yes/no |
| Lock key | `<workflow_or_resource_lock>` |
| Collision policy | fail / wait / advisory |
| Replay collision sensitivity | low / medium / high |

## Guardrail mode

| Mode | Value |
|---|---|
| Advisory first | yes |
| Strict allowed after clean runs | yes |
| Required before mutating step | yes |

## Notes

Add workflow-specific notes here.
