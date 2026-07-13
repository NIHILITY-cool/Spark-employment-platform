#!/bin/bash
set -e

SOURCE_DIR="${1:-data/raw/ncss_jobs}"
HDFS_DIR="${2:-/employment-platform/raw/jobs/source=ncss}"

echo "Uploading raw job data to HDFS"
echo "Local source: ${SOURCE_DIR}"
echo "HDFS target:  ${HDFS_DIR}"

hdfs dfs -mkdir -p "${HDFS_DIR}"
hdfs dfs -put -f "${SOURCE_DIR}" "${HDFS_DIR}"

echo "Upload completed"
