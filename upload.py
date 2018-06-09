# -*- coding: utf-8 -*-

import argparse
import datetime
import os
import time

import dropbox


def upload(dbx: dropbox.Dropbox, src: str, dst: str, overwrite: bool = False):
    mode = (dropbox.files.WriteMode.overwrite
            if overwrite
            else dropbox.files.WriteMode.add)
    mtime = os.path.getmtime(src)

    with open(src, 'rb') as f:
        data = f.read()

    try:
        res = dbx.files_upload(
            data, dst, mode,
            client_modified=datetime.datetime(*time.gmtime(mtime)[:6]),
            mute=True)
    except dropbox.exceptions.ApiError as err:
        print('*** API error', err)
        return None

    print('upload as', res.name.encode('utf8'))
    return res


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Upload file to Dropbox')
    parser.add_argument('src')
    parser.add_argument('dst')
    parser.add_argument('--token', '-T', required=True)

    args = parser.parse_args()

    dbx = dropbox.Dropbox(args.token)
    upload(dbx, args.src, args.dst)

