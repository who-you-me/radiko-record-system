#!/usr/bin/env bash

set -eu

channel=$1
duration=$2
offset=$3
prefix=$4

archive_dir="$HOME/archive/${prefix}"

if [ ! -d ${archive_dir} ]; then
  mkdir -p ${archive_dir}
fi

date=`date +"%Y%m%d"`
dst="${archive_dir}/${date}"
dbx_dst="/${prefix}/${date}.m4a"

python radiko.py -C ${channel} -D ${duration} -O "${dst}.flv"
ffmpeg -loglevel quiet -y -i "${dst}.flv" -acodec copy -ss ${offset} "${dst}.aac"
MP4Box -add "${dst}.aac" "${dst}.m4a" -sbr
python upload.py "${dst}.m4a" "${dbx_dst}" -T ${DROPBOX_TOKEN}
