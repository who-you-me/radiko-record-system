# -*- coding: utf-8 -*-

import argparse
import base64
import os
import subprocess
import urllib.request
import xml.etree.ElementTree as ET
from urllib.parse import urlparse

import requests

# sudo apt install swftools
# sudo apt install rtmpdump


class Radiko(object):
    PLAYER_URL = 'http://radiko.jp/apps/js/flash/myplayer-release.swf'
    PLAYER_PATH = '/tmp/player.swf'

    KEY_PATH = '/tmp/authkey.png'

    AUTH1_URL = 'https://radiko.jp/v2/api/auth1_fms'
    AUTH2_URL = 'https://radiko.jp/v2/api/auth2_fms'

    STREAM_URL = 'http://radiko.jp/v2/station/stream/{}.xml'

    def __init__(self):
        self._get_player()
        self._get_key()
        self._auth_fm1()
        self._auth_fms2()

    def record(self, channel, duration, output):
        url, app, play_path = self._stream_url(channel)
        subprocess.run([
            'rtmpdump',
            '-r', url,
            '--app', app,
            '--playpath', play_path,
            '-W', self.PLAYER_URL,
            '-C', 'S:""', '-C', 'S:""', '-C', 'S:""', '-C', f'S:{self.auth_token}',
            '--live',
            '--stop', str(duration),
            '--flv', output,
        ])

    @classmethod
    def _get_player(cls, force=False):
        if not force and os.path.exists(cls.PLAYER_PATH):
            return
        urllib.request.urlretrieve(cls.PLAYER_URL, cls.PLAYER_PATH)

    @classmethod
    def _get_key(cls, force=False):
        if not force and os.path.exists(cls.KEY_PATH):
            return
        subprocess.run(['swfextract', '-b', '12', cls.PLAYER_PATH, '-o', cls.KEY_PATH])

    @property
    def auth_header(self):
        return {
            'X-Radiko-App': 'pc_ts',
            'X-Radiko-App-Version': '4.0.0',
            'X-Radiko-Device': 'pc',
            'X-Radiko-User': 'test-stream',
        }

    def _auth_fm1(self):
        r = requests.post(self.AUTH1_URL, headers=self.auth_header)

        data = {}
        for row in r.content.decode('utf8').split('\r\n'):
            values = row.split('=')
            if len(values) != 2:
                continue
            data[values[0].lower()] = values[1]

        self.auth_token = data['x-radiko-authtoken']
        offset = int(data['x-radiko-keyoffset'])
        length = int(data['x-radiko-keylength'])

        with open(self.KEY_PATH, 'rb') as f:
            f.seek(offset)
            self.partial_key = base64.b64encode(f.read(length)).decode('utf8')

    def _auth_fms2(self):
        headers = {
            **self.auth_header,
            'X-Radiko-Authtoken': self.auth_token,
            'X-Radiko-Partialkey': self.partial_key,
        }
        requests.post(self.AUTH2_URL, headers=headers)

    def _stream_url(self, channel):
        url = self.STREAM_URL.format(channel)
        r = requests.get(url)

        tree = ET.fromstring(r.content)
        item = tree.find('item')
        o = urlparse(item.text)
        paths = o.path.split('/')[1:]

        return f'{o.scheme}://{o.netloc}', '/'.join(paths[:2]), paths[-1]


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Record Radiko')
    parser.add_argument('--channel', '-C', required=True)
    parser.add_argument('--duration', '-D', type=int, required=True)
    parser.add_argument('--output', '-O', required=True)

    args = parser.parse_args()

    radiko = Radiko()
    radiko.record(args.channel, args.duration, args.output)
