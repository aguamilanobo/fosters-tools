import io
import json
import unittest
from unittest.mock import patch
from urllib.error import HTTPError, URLError

from fastapi import HTTPException
from fastapi.testclient import TestClient
from fosters_ad_source import classify_metadata, fetch_ad, resolve_ad
from main import app, API_TOKEN


class AdSourceTests(unittest.TestCase):
    def test_new_ad_ids_are_resolved_from_names_without_a_list(self):
        for ad_id, name, expected in [("52571868382709", "Empezá con una Henley Fosters", "henley"),
                                      ("99999999999999", "FOSTERS | POLOS | Noviembre", "polo")]:
            with self.subTest(ad_id=ad_id):
                result = classify_metadata({"id": ad_id, "name": name}, ad_id)
                self.assertEqual(result['product'], expected)
                self.assertTrue(result['should_set_product'])
                self.assertFalse(result['mutated'])

    def test_campaign_name_resolves_generic_ad_name(self):
        result = classify_metadata({'id': '12345', 'name': 'Tus básicos de la semana',
                                   'campaign': {'name': 'FOSTERS - POLO'}}, '12345')
        self.assertEqual(result['product'], 'polo')

    def test_ambiguous_or_unknown_names_never_default_to_henley(self):
        for data in [{'id': '12345', 'name': 'Fosters básicos'},
                     {'id': '12345', 'name': 'Henley y Polo'},
                     {'id': '12345', 'name': 'Polo', 'campaign': {'name': 'Henley'}},
                     {'id': '12345', 'name': 'polonio'},
                     {'id': '67890', 'name': 'Polo'}, [], None]:
            result = classify_metadata(data, '12345')
            self.assertFalse(result['resolved'])
            self.assertIsNone(result['product'])
            self.assertFalse(result['should_set_product'])

    def test_missing_id_does_not_make_a_remote_request(self):
        with patch('fosters_ad_source.fetch_ad') as remote:
            self.assertEqual(resolve_ad(None)['reason'], 'missing_ad_id')
            self.assertEqual(resolve_ad('')['reason'], 'missing_ad_id')
            remote.assert_not_called()

    def test_invalid_id_cannot_become_a_url(self):
        for value in ['../me', 'https://example.com', '123?access_token=x', '12345/ads']:
            with self.assertRaises(HTTPException):
                resolve_ad(value)

    def test_config_is_required_without_guessing_access(self):
        with patch.dict('os.environ', {'META_ADS_ACCESS_TOKEN': '', 'META_GRAPH_API_VERSION': ''}):
            self.assertEqual(resolve_ad('12345')['reason'], 'meta_credentials_missing')
        with patch.dict('os.environ', {'META_ADS_ACCESS_TOKEN': 'test-only', 'META_GRAPH_API_VERSION': ''}):
            self.assertEqual(resolve_ad('12345')['reason'], 'meta_api_version_missing_or_invalid')

    def test_fetch_and_failures_return_safe_results(self):
        with patch.dict('os.environ', {'META_ADS_ACCESS_TOKEN': 'test-only', 'META_GRAPH_API_VERSION': 'v99.0'}):
            with patch('fosters_ad_source.fetch_ad', return_value={'id': '12345', 'name': 'Polo'}) as remote:
                self.assertEqual(resolve_ad('12345')['product'], 'polo')
                remote.assert_called_once_with('12345', 'test-only', 'v99.0')
            for exc in [HTTPError('url', 403, 'secret-value', {}, io.BytesIO(b'secret-value')),
                        URLError('secret-value'), ValueError('secret-value')]:
                with patch('fosters_ad_source.fetch_ad', side_effect=exc):
                    result = resolve_ad('12345')
                    self.assertFalse(result['resolved'])
                    self.assertNotIn('secret-value', json.dumps(result))

    def test_request_keeps_token_out_of_url_and_disables_redirects(self):
        with patch('fosters_ad_source.request.build_opener') as factory:
            response = factory.return_value.open.return_value.__enter__.return_value
            response.read.return_value = b'{"id":"12345","name":"Polo"}'
            self.assertEqual(fetch_ad('12345', 'test-only', 'v99.0')['name'], 'Polo')
            req = factory.return_value.open.call_args.args[0]
            self.assertTrue(req.full_url.startswith('https://graph.facebook.com/v99.0/12345?'))
            self.assertNotIn('test-only', req.full_url)
            self.assertEqual(req.get_header('Authorization'), 'Bearer test-only')

    def test_endpoint_auth_and_real_fastapi_serialization(self):
        with TestClient(app) as client:
            self.assertEqual(client.post('/fosters/ads/resolve', json={'ad_id': '12345'}).status_code, 401)
            with patch('fosters_ad_source.fetch_ad', return_value={'id': '12345', 'name': 'Henley'}), \
                 patch.dict('os.environ', {'META_ADS_ACCESS_TOKEN': 'test-only', 'META_GRAPH_API_VERSION': 'v99.0'}):
                response = client.post('/fosters/ads/resolve', json={'ad_id': '12345'},
                                       headers={'Authorization': 'Bearer ' + API_TOKEN})
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json()['product'], 'henley')
