#!/usr/bin/env bash
export PGPASSWORD=$POSTGRES_PASSWORD
date=$(date '+%Y-%m-%d:%H:%M')
backupFile=microcosm-${date}.sql.gz
stateFile="state.txt"
restoreFile="backup.sql.gz"

# Backing up DataBase
if [ "$DB_ACTION" == "backup" ]; then
	# Backup database and make maximum compression at the slowest speed
	# --quote-all-identifiers
	pg_dump -h $POSTGRES_HOST -U $POSTGRES_USER $POSTGRES_DB | gzip -9 >$backupFile

	# AWS
	if [ "$CLOUDPROVIDER" == "aws" ]; then
		# Upload to S3
		aws s3 cp $backupFile $AWS_S3_BUCKET/database/$backupFile
		# The file state.txt contain the latest version of DB path
		echo "$AWS_S3_BUCKET/database/$backupFile" >$stateFile
		aws s3 cp $stateFile $AWS_S3_BUCKET/database/$stateFile
	fi
fi

# Restoring DataBase
if [ "$DB_ACTION" == "restore" ]; then
	# AWS
	wget -O $restoreFile $RESTORE_URL_FILE
	gunzip <$restoreFile | psql -h $POSTGRES_HOST -U $POSTGRES_USER -d $POSTGRES_DB
fi

# This part of the code will clean the backups that have an aging of more than a week,
# this can be activated according to a environment variable.
if [ $CLEAN_BACKUPS == "true" ]; then
	DATE=$(date --date="5 day ago" +"%Y-%m-%d")
	# AWS
	if [ $CLOUDPROVIDER == "aws" ]; then
		# Filter files from S3
		aws s3 ls $AWS_S3_BUCKET/database/ |
			awk '{print $4}' |
			awk -F"microcosm-" '{$1=$1}1' |
			awk '/sql.gz/{print}' |
			awk -F".sql.gz" '{$1=$1}1' |
			awk '$1 < "'"$DATE"'" {print $0}' |
			sort -n >output
		# Delete filtered files
		while read file; do
			aws s3 rm $AWS_S3_BUCKET/database/microcosm-$file.sql.gz
		done <output
		rm output
	fi
fi
