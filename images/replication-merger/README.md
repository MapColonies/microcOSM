# Replication-Merger

This container is responsible for merging the delta replication files created by the `replication-job` container using `osmosis`.
It merges the minute replications into larger time units: hours, days, weeks.
Every time unit will be merged to it's one upper level time unit, minutes to hours, hours to days etc.

### Configuration

**Env Variables**

- `REPLICATION_MERGE_INTERVAL` the interval in **seconds** for the merging job process to take place.

**Files**

- `(time-unit-name)-config.txt`: every time unit has it's own configuration to be set and used by osmosis, the properties the config holds are:
    - `baseUrl` The URL \ Local directory that contains the change files.
    - `intervalLength` The length of an extraction interval in seconds.
    - `maxInterval` the maximum period of time in seconds to be downloaded in a single invocation. Setting to 0 disables this feature.