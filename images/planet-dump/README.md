### Planet dump Container

A container to create periodeclly planet dumps (pbf files), of the OSM database.

### Environment variables 

- `POSTGRES_HOST` - db
- `POSTGRES_DB` - openstreetmap
- `POSTGRES_USER` - postgres
- `POSTGRES_PASSWORD` - 1234

- `CREATE_DUMP_SCHEDULE_CRON` - When to create a dump in CRON pattern
- `DUMP_STORAGE_FOLDER` - the directory inside the container in which to store the created dumps
- `DUMP_FILE_PREFIX` - Prefix to each dump file
- `OSMOSIS_OMIT_METADATA` - Variable whetever dumps should contain the metadata (users, changeset id)


