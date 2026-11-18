#!/usr/bin/env python3
"""Publish validated assets as a release; never overwrite a signed version."""
import argparse
import json
import os
from pathlib import Path
import urllib.parse
import urllib.request
import urllib.error


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('tag')
    parser.add_argument('--directory', type=Path, default=Path('dist/desktop'))
    parser.add_argument('--create', action='store_true')
    parser.add_argument('--target', default='main')
    parser.add_argument('--notes-file', type=Path)
    args = parser.parse_args()
    token = os.environ['GITHUB_TOKEN']
    repository = os.environ['GITHUB_REPOSITORY']
    headers = {'Authorization': 'Bearer '+token, 'Accept': 'application/vnd.github+json', 'User-Agent': 'Operation-MX-release'}
    base = 'https://api.github.com/repos/'+repository
    url = base+'/releases/tags/'+urllib.parse.quote(args.tag, safe='')
    # Only publish the four expected artifacts; reject stale mixed-version output.
    release_version = args.tag.removeprefix('v')
    assets = [args.directory/name for name in [f'operation-mx-{release_version}-linux-x86_64.tar.gz',
               f'operation-mx-installer-{release_version}.tar.gz', 'operation-mx-update.json.sig', 'operation-mx-update.json']]
    if not all(path.is_file() for path in assets):
        raise RuntimeError('Incomplete release artifacts')
    manifest = json.loads(assets[-1].read_text())
    if manifest['version'] != release_version:
        raise ValueError('Release tag and manifest version differ')
    def api(url, payload=None, method=None):
        data = json.dumps(payload).encode() if payload is not None else None
        request = urllib.request.Request(url, data=data, headers=dict(headers, **{'Content-Type': 'application/json'}), method=method)
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.load(response)
    try:
        release = api(url)
    except urllib.error.HTTPError as error:
        if error.code != 404 or not args.create:
            raise
        release = api(base+'/releases', {'tag_name': args.tag, 'target_commitish': args.target,
            'name': 'Operation MX '+release_version, 'draft': True, 'prerelease': False,
            'body': args.notes_file.read_text() if args.notes_file else 'Operation MX desktop update.'})
    existing = {item['name'] for item in release['assets']}
    if any(path.name in existing for path in assets):
        raise RuntimeError('Release assets already exist. Publish a new version instead of replacing signed assets.')
    upload = release['upload_url'].split('{', 1)[0]
    if urllib.parse.urlparse(upload).hostname != 'uploads.github.com':
        raise ValueError('Unexpected release upload endpoint')
    for path in assets:
        request = urllib.request.Request(upload+'?name='+urllib.parse.quote(path.name), data=path.read_bytes(),
                                         headers=dict(headers, **{'Content-Type': 'application/octet-stream'}), method='POST')
        with urllib.request.urlopen(request, timeout=180) as response:
            json.load(response)
        print('Uploaded', path.name)
    if release.get('draft'):
        release = api(base+'/releases/'+str(release['id']), {'draft': False, 'make_latest': 'true'}, 'PATCH')
    print('Published', release['html_url'])


if __name__ == '__main__':
    main()
