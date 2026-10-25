"""Private downloads authenticate only to GitHub API; keep PATs off CDN URLs."""
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import urllib.request

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'mako_station'))
import updater


class PrivateUpdateTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(); self.addCleanup(temp.cleanup)
        self.path = Path(temp.name)/'private/github-token'
        env = patch.dict(os.environ, {'OPERATION_MX_GITHUB_TOKEN_FILE': str(self.path), 'OPERATION_MX_GITHUB_TOKEN': ''})
        env.start(); self.addCleanup(env.stop)

    def test_token_saved_owner_only_and_removed(self):
        updater.save_github_token('github_pat_example')
        self.assertEqual(self.path.stat().st_mode & 0o777, 0o600)
        self.assertEqual(updater.github_token(), 'github_pat_example')
        updater.save_github_token('')
        self.assertFalse(self.path.exists())

    def test_world_readable_token_is_refused(self):
        updater.save_github_token('github_pat_example'); self.path.chmod(0o644)
        with self.assertRaisesRegex(ValueError, '600'): updater.github_token()

    def test_auth_only_attached_to_api(self):
        updater.save_github_token('github_pat_example')
        with patch('urllib.request.build_opener') as opener:
            updater.open_github('https://api.github.com/repos/team/repo/releases/assets/42')
            request = opener.return_value.open.call_args.args[0]
            self.assertEqual(request.get_header('Authorization'), 'Bearer github_pat_example')
            self.assertEqual(request.get_header('Accept'), 'application/octet-stream')
            updater.open_github('https://release-assets.githubusercontent.com/a')
            request = opener.return_value.open.call_args.args[0]
            self.assertIsNone(request.get_header('Authorization'))

    def test_cdn_redirect_strips_credentials(self):
        request = urllib.request.Request('https://api.github.com/repos/team/repo/releases/assets/42',
                                         headers={'Authorization': 'Bearer secret'})
        redirected = updater.GitHubRedirect().redirect_request(request, None, 302, '', {},
                         'https://release-assets.githubusercontent.com/signed-download')
        self.assertIsNone(redirected.get_header('Authorization'))
        with self.assertRaises(ValueError):
            updater.GitHubRedirect().redirect_request(request, None, 302, '', {}, 'https://evil.example/steal')

    def test_private_release_uses_asset_api_urls(self):
        assets = [{'name': updater.MANIFEST, 'url': 'https://api.github.com/repos/t/r/releases/assets/1'},
                  {'name': updater.MANIFEST+'.sig', 'url': 'https://api.github.com/repos/t/r/releases/assets/2'},
                  {'name': 'operation-mx-1.1.0-linux-x86_64.tar.gz', 'url': 'https://api.github.com/repos/t/r/releases/assets/3'}]
        def get(url, limit):
            if url.endswith('/releases/latest'): return json.dumps({'tag_name':'v1.1.0','assets':assets}).encode()
            return b'signature' if url.endswith('/2') else b'manifest'
        with patch('updater.verify_manifest', return_value={'version':'1.1.0','archive':{'name':assets[2]['name']}}):
            result = updater.latest(Path('unused'), '1.0.2', get)
        self.assertEqual(result[-1], assets[2]['url'])
