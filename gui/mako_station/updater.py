"""Signed releases and safe per-user update storage. No Qt or ROS imports."""
import base64
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import platform
import re
import shutil
import stat
import tarfile
import tempfile
import urllib.parse
import urllib.request

REPOSITORY = 'adhamsherif67A/adhamsherif67A-MarineXperts-Season-2027'
MANIFEST = 'operation-mx-update.json'
MAX_ARCHIVE = 1024 * 1024 * 1024


def version(value):
    match = re.fullmatch(r'v?(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)', value)
    if not match:
        raise ValueError('Expected a stable version such as 1.2.0')
    return tuple(map(int, match.groups()))


def current_version():
    return Path(__file__).with_name('VERSION').read_text().strip()


def token_path():
    override = os.environ.get('OPERATION_MX_GITHUB_TOKEN_FILE')
    if override:
        return Path(override).expanduser()
    return Path(os.environ.get('XDG_CONFIG_HOME', Path.home()/'.config'))/'operation-mx/github-token'


def github_token():
    value = os.environ.get('OPERATION_MX_GITHUB_TOKEN', '').strip()
    path = token_path()
    if not value and path.is_file():
        if stat.S_IMODE(path.stat().st_mode) & 0o077:
            raise ValueError('GitHub token file must have permissions 600')
        value = path.read_text().strip()
    if value and (len(value) > 4096 or not re.fullmatch(r'[A-Za-z0-9_]+', value)):
        raise ValueError('Invalid GitHub token format')
    return value


def save_github_token(value):
    value = value.strip()
    if value and (len(value) > 4096 or not re.fullmatch(r'[A-Za-z0-9_]+', value)):
        raise ValueError('Invalid GitHub token format')
    path = token_path()
    if not value:
        path.unlink(missing_ok=True)
        return
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    fd, temporary = tempfile.mkstemp(prefix='.github-token-', dir=path.parent)
    try:
        with os.fdopen(fd, 'w') as stream:
            stream.write(value+'\n')
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)


GITHUB_HOSTS = {'api.github.com', 'github.com', 'objects.githubusercontent.com',
                'release-assets.githubusercontent.com'}


def check_github_url(url):
    parsed = urllib.parse.urlparse(url)
    if (parsed.scheme != 'https' or parsed.hostname not in GITHUB_HOSTS or
            parsed.username or parsed.password or parsed.port not in (None, 443)):
        raise ValueError('Updates must come from GitHub over HTTPS')
    return parsed


class GitHubRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        destination = check_github_url(newurl)
        redirected = super().redirect_request(request, fp, code, msg, headers, newurl)
        # Signed CDN URLs need no credential. Never forward the user's PAT.
        if redirected is not None and destination.hostname != 'api.github.com':
            redirected.remove_header('Authorization')
        return redirected


def open_github(url):
    parsed = check_github_url(url)
    headers = {'User-Agent': 'Operation-MX-Updater/1', 'X-GitHub-Api-Version': '2022-11-28'}
    if parsed.hostname == 'api.github.com':
        headers['Accept'] = ('application/octet-stream' if '/releases/assets/' in parsed.path
                             else 'application/vnd.github+json')
        token = github_token()
        if token:
            headers['Authorization'] = 'Bearer '+token
    request = urllib.request.Request(url, headers=headers)
    return urllib.request.build_opener(GitHubRedirect()).open(request, timeout=30)


def atomic_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix='.update-', dir=path.parent)
    try:
        with os.fdopen(fd, 'w') as stream:
            json.dump(value, stream)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        directory = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        Path(temporary).unlink(missing_ok=True)


def verify_manifest(raw, signature, public_key):
    from cryptography.hazmat.primitives.serialization import load_pem_public_key
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
    if len(raw) > 65536:
        raise ValueError('Update manifest is too large')
    key = load_pem_public_key(Path(public_key).read_bytes())
    if not isinstance(key, Ed25519PublicKey):
        raise ValueError('An Ed25519 release key is required')
    key.verify(base64.b64decode(signature, validate=True), raw)
    manifest = json.loads(raw)
    version(manifest['version'])
    if manifest.get('schema') != 1 or manifest.get('launcher_version') != 1:
        raise ValueError('This update requires a newer installer')
    if manifest.get('platform') != 'ubuntu-22.04-x86_64':
        raise ValueError('Unsupported update platform')
    archive = manifest['archive']
    if not re.fullmatch(r'operation-mx-[0-9.]+-linux-x86_64\.tar\.gz', archive['name']):
        raise ValueError('Invalid archive name')
    if not re.fullmatch(r'[0-9a-f]{64}', archive['sha256']):
        raise ValueError('Invalid archive checksum')
    if not isinstance(archive['size'], int) or not 0 < archive['size'] <= MAX_ARCHIVE:
        raise ValueError('Invalid archive size')
    return manifest


def fetch(url, limit=65536):
    with open_github(url) as response:
        check_github_url(response.url)
        data = response.read(limit + 1)
    if len(data) > limit:
        raise ValueError('Update response exceeds its size limit')
    return data


def latest(public_key, installed, get=fetch):
    release = json.loads(get(f'https://api.github.com/repos/{REPOSITORY}/releases/latest', 1024*1024))
    if release.get('draft') or release.get('prerelease'):
        return None
    # Private release assets must be requested through the authenticated API.
    assets = {item['name']: item.get('url') or item['browser_download_url'] for item in release['assets']}
    if MANIFEST not in assets or MANIFEST+'.sig' not in assets:
        return None  # A published release may still be building its assets.
    raw = get(assets[MANIFEST], 65536)
    signature = get(assets[MANIFEST+'.sig'], 1024)
    manifest = verify_manifest(raw, signature, public_key)
    if version(release['tag_name']) != version(manifest['version']):
        raise ValueError('Release tag and signed manifest disagree')
    if version(manifest['version']) <= version(installed):
        return None
    name = manifest['archive']['name']
    if name not in assets:
        return None
    return manifest, raw, signature, assets[name]


def archive_valid(path, manifest):
    path = Path(path)
    if not path.is_file() or path.stat().st_size != manifest['archive']['size']:
        return False
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024*1024), b''):
            digest.update(chunk)
    return digest.hexdigest() == manifest['archive']['sha256']


def download(url, target, manifest):
    """Stream bounded data; never expose a partially downloaded archive."""
    # Apply the same origin policy before opening a streaming response.
    parsed = check_github_url(url)
    if parsed.hostname not in {'github.com', 'api.github.com'}:
        raise ValueError('Invalid release download URL')
    target = Path(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix('.part')
    try:
        with open_github(url) as response, temporary.open('wb') as stream:
            check_github_url(response.url)
            total = 0
            while True:
                chunk = response.read(1024*1024)
                if not chunk:
                    break
                total += len(chunk)
                if total > manifest['archive']['size']:
                    raise ValueError('Archive exceeded its signed size')
                stream.write(chunk)
        if not archive_valid(temporary, manifest):
            raise ValueError('Update checksum verification failed')
        os.replace(temporary, target)
    finally:
        temporary.unlink(missing_ok=True)


def extract_archive(path, destination):
    """Only regular files/directories; reject traversal, links and tar bombs."""
    destination = Path(destination)
    if destination.exists():
        raise ValueError('Extraction destination must be new')
    destination.mkdir(parents=True)
    try:
        with tarfile.open(path, 'r:gz') as archive:
            members = archive.getmembers()
            if len(members) > 50000 or sum(m.size for m in members) > 3*MAX_ARCHIVE:
                raise ValueError('Archive extraction limit exceeded')
            seen = set()
            for member in members:
                name = PurePosixPath(member.name)
                if (name.is_absolute() or '..' in name.parts or '\\' in member.name
                        or not name.parts or name.parts[0] not in {'workspace', 'runtime', 'release.json'}
                        or not (member.isfile() or member.isdir()) or member.name in seen
                        or member.size < 0 or member.size > MAX_ARCHIVE):
                    raise ValueError('Unsafe release archive member: '+member.name)
                seen.add(member.name)
            for member in members:
                target = destination/member.name
                if member.isdir():
                    target.mkdir(parents=True, exist_ok=True)
                else:
                    target.parent.mkdir(parents=True, exist_ok=True)
                    with archive.extractfile(member) as source, target.open('wb') as output:
                        shutil.copyfileobj(source, output)
                    target.chmod(0o755 if member.mode & 0o111 else 0o644)
    except BaseException:
        shutil.rmtree(destination)
        raise


def queue_update(root, raw, signature, archive):
    root = Path(root)
    manifest = verify_manifest(raw, signature, root/'update_public_key.pem')
    if not archive_valid(archive, manifest):
        raise ValueError('Cannot queue a corrupt archive')
    atomic_json(root/'pending.json', {
        'manifest': base64.b64encode(raw).decode(),
        'signature': signature.decode(), 'archive': str(Path(archive).resolve())})


def host_compatible():
    values = dict(line.strip().split('=', 1) for line in Path('/etc/os-release').read_text().splitlines() if '=' in line)
    return (values.get('ID', '').strip('"') == 'ubuntu'
            and values.get('VERSION_ID', '').strip('"') == '22.04'
            and platform.machine() == 'x86_64')
