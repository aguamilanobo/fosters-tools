import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from fosters_products import products, product, campaign_reply, media_plan
from main import (
    get_products, NextActionRequest, decide_next_action, prepare_order, OrderPrepRequest,
    fosters_payment_summary, FostersPaymentSummaryRequest,
)


class HenleyOnlyTests(unittest.TestCase):
    def test_catalog_and_sync_publish_only_henley(self):
        self.assertEqual([p['id'] for p in products()['products']], ['henley'])
        sync = get_products(page=1, pageSize=50)
        self.assertEqual(sync['total'], 1)
        self.assertEqual(sync['data'][0]['product']['id'], 'fosters-henley')
        self.assertEqual(len(sync['data'][0]['product']['variations']), 15)

    def test_retired_and_unknown_requests_do_not_become_henley(self):
        for value in ['shorts-lino', 'shorts_lino', 'short', 'bermuda', 'pantalón corto',
                      'Henley + shorts', 'camisa-lino-brasilero', 'otro producto']:
            with self.subTest(product=value):
                detail = product(product=value)
                self.assertFalse(detail['found'])
                self.assertFalse(detail['send_product_photos'])
                campaign = campaign_reply(product=value)
                self.assertEqual(campaign['status'], 'inactive')
                self.assertFalse(campaign['send_product_photos'])
                for extra in [{'wants_to_buy': True}, {'asks_for_photos': True},
                              {'is_opening': True}]:
                    action = decide_next_action(NextActionRequest(product=value, **extra))
                    self.assertEqual(action['next_action'], 'answer_product_unavailable')
                    self.assertFalse(action['send_product_photos'])
                order = prepare_order(OrderPrepRequest(product=value, color='Negro',
                                                       size='M', city='Santa Cruz'))
                self.assertFalse(order['ready_to_order'])
                self.assertFalse(order['order_created'])

    def test_retired_items_cannot_reach_printer(self):
        with patch('main.urllib_request.urlopen') as external_request:
            for text in ['Shorts Negro M', 'Henley Negro M + short Perla M']:
                result = fosters_payment_summary(FostersPaymentSummaryRequest(
                    items=text, full_name='Prueba', ci='TEST', department='La Paz', phone='TEST'))
                self.assertFalse(result['ready_for_payment'])
                self.assertFalse(result['should_send_summary'])
                self.assertIsNone(result['summary_message'])
            external_request.assert_not_called()

    def test_opening_returns_five_original_henley_attachments(self):
        expected = {'negra.png', 'blanca.png', 'navy.png', 'celeste.png', 'crema.png'}
        for result in [campaign_reply(), decide_next_action(NextActionRequest(is_opening=True))]:
            self.assertTrue(result['send_product_photos'])
            self.assertEqual(result['photo_count'], 5)
            self.assertEqual({p['filename'] for p in result['photo_attachments']}, expected)
            self.assertFalse(result['media_sent'])
            self.assertEqual(result['media_delivery'], 'botcake_flow_required')
        self.assertNotEqual(decide_next_action(NextActionRequest(
            is_opening=True, opening_sent=True))['next_action'], 'send_catalog')
        # A direct photo request must allow resending even after opening.
        self.assertEqual(decide_next_action(NextActionRequest(
            opening_sent=True, asks_for_photos=True))['photo_count'], 5)

    def test_selected_color_sends_only_its_original(self):
        for alias, filename in [('navy', 'navy.png'), ('Azul marino', 'navy.png'),
                                ('Negro', 'negra.png'), ('crema', 'crema.png')]:
            with self.subTest(color=alias):
                result = decide_next_action(NextActionRequest(asks_for_photos=True, color=alias))
                self.assertEqual(result['photo_count'], 1)
                self.assertEqual(result['photo_attachments'][0]['filename'], filename)
        self.assertFalse(media_plan('Perla')['send_product_photos'])
        self.assertFalse(product(color='Perla')['found'])

    def test_opening_does_not_interrupt_checkout_or_location(self):
        action = decide_next_action(NextActionRequest(is_opening=True, wants_to_buy=True,
                    color='Negro', size='M', city='Santa Cruz', location_shared=True))
        self.assertEqual(action['next_action'], 'handoff')
        action = decide_next_action(NextActionRequest(is_opening=True, asks_for_store_location=True))
        self.assertEqual(action['next_action'], 'answer_store_location')


class HenleyHTTPTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data_dir = tempfile.TemporaryDirectory(prefix='henley-http-')
        with socket.socket() as sock:
            sock.bind(('127.0.0.1', 0))
            port = sock.getsockname()[1]
        cls.base_url = f'http://127.0.0.1:{port}'
        cls.server = subprocess.Popen([
            sys.executable, '-m', 'uvicorn', 'main:app', '--host', '127.0.0.1', '--port', str(port),
        ], cwd=Path(__file__).resolve().parents[1],
           env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1', 'DISPATCH_DATA_DIR': cls.data_dir.name},
           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        cls.addClassCleanup(cls.data_dir.cleanup)
        cls.addClassCleanup(cls.stop_server)
        for _ in range(100):
            try:
                cls.request('/openapi.json')
                break
            except URLError:
                if cls.server.poll() is not None:
                    raise RuntimeError('HTTP server failed to start')
                time.sleep(.05)
        else:
            raise RuntimeError('HTTP server startup timed out')

    @classmethod
    def stop_server(cls):
        cls.server.terminate()
        cls.server.wait(timeout=10)

    @classmethod
    def request(cls, path, data=None):
        request = Request(cls.base_url + path, headers={'Content-Type': 'application/json'},
                          data=json.dumps(data).encode() if data is not None else None)
        try:
            response = urlopen(request, timeout=5)
        except HTTPError as error:
            response = error
        with response:
            return response.status, json.load(response)

    def test_legacy_api_cannot_offer_or_accept_anything(self):
        _, schema = self.request('/openapi.json')
        self.assertFalse(any('/upsell' in p for p in schema['paths']))
        for path, payload in [('/fosters/upsell/config', None),
                              ('/fosters/upsell/offer', {'customer_requested_upsell': True,
                               'buying_intent': True, 'shirt_color': 'Negro', 'shirt_size': 'M'}),
                              ('/fosters/upsell/decision/', {'decision': 'si',
                               'short_color': 'Perla', 'short_size': 'M'})]:
            with self.subTest(path=path):
                status, result = self.request(path, payload)
                self.assertEqual(status, 410)
                self.assertFalse(result['should_offer'])
                self.assertFalse(result['accepted'])
                self.assertFalse(result['send_product_photos'])
                self.assertNotIn('price_bs', result)
                self.assertNotIn('short_item', result)

    def test_public_routes_are_single_product_and_opening_has_media(self):
        for path in ['/catalog?product=shorts-lino', '/fosters/product?product=shorts_lino',
                     '/fosters/campaign-reply?product=bermuda']:
            status, result = self.request(path)
            self.assertEqual(status, 200)
            self.assertFalse(result['found'])
            self.assertFalse(result['send_product_photos'])
        _, catalog = self.request('/fosters/products')
        self.assertEqual([p['id'] for p in catalog['products']], ['henley'])
        _, sync = self.request('/products')
        self.assertEqual(sync['total'], 1)
        _, action = self.request('/decide-next-action', {'is_opening': True})
        self.assertEqual(action['photo_count'], 5)
        self.assertFalse(action['media_sent'])
        _, schema = self.request('/openapi.json')
        self.assertIn('is_opening', schema['components']['schemas']['NextActionRequest']['properties'])


if __name__ == '__main__':
    unittest.main()
