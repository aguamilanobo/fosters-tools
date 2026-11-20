import unittest
from unittest.mock import patch
from fastapi.testclient import TestClient

from main import app


class ShortSalesTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def decide(self, **data):
        response = self.client.post('/decide-next-action', json=data)
        self.assertEqual(response.status_code, 200)
        return response.json()

    def test_selected_size_and_two_colors_go_straight_to_shipping(self):
        with patch('main.urllib_request.urlopen') as network:
            result = self.decide(product='henley', color='azul y negra', size='L',
                                 wants_to_buy=False, is_opening=True)
            self.assertEqual(result['next_action'], 'ask_destination')
            self.assertEqual(result['selected_colors'], ['Azul', 'Negro'])
            self.assertEqual(result['message'], '¿De qué ciudad sos?')
            self.assertFalse(result['stock_check_required'])
            self.assertNotIn('send_product_photos', result)
            network.assert_not_called()

    def test_aliases_and_invalid_color_do_not_invent_variants(self):
        result = self.decide(product='polo', color='plomo, beige claro', size='XL')
        self.assertEqual(result['selected_colors'], ['Gris', 'Beige'])
        invalid = self.decide(product='henley', color='azul y gris', size='M', wants_to_buy=True,
                              opening_sent=True)
        self.assertEqual(invalid['next_action'], 'ask_color')
        self.assertEqual(invalid['missing_fields'], ['color'])

    def test_delivery_asks_only_the_missing_field_then_stops(self):
        base = dict(product='polo', color='Negro', size='L')
        self.assertEqual(self.decide(**base, city='Santa Cruz')['message'],
                         'Pasame tu ubicación para coordinar el envío.')
        for shipping in [dict(city='Santa Cruz', location_shared=True),
                         dict(city='La Paz', full_name='Prueba', ci='TEST')]:
            result = self.decide(**base, **shipping)
            self.assertEqual(result['next_action'], 'handoff')
            self.assertTrue(result['stop_after_handoff'])
            self.assertEqual(result['message'], 'Perfecto, querido. Enseguida te contacta alguien del equipo.')
            self.assertEqual(result['missing_fields'], [])
        self.assertEqual(self.decide(**base, city='La Paz', full_name='Prueba')['message'], '¿Me pasás tu CI?')
        self.assertEqual(self.decide(**base, city='La Paz', ci='TEST')['message'], '¿Me pasás tu nombre completo?')

    def test_followup_replies_are_one_short_paragraph(self):
        examples = [dict(is_opening=True), dict(product='henley', color='Negro', size='M'),
                    dict(product='henley', color='Negro', size='M', city='La Paz'),
                    dict(asks_for_human=True), dict(asks_for_store_location=True)]
        for data in examples:
            result = self.decide(**data)
            text = result.get('message', result.get('suggested_reply', ''))
            self.assertTrue(text)
            self.assertLessEqual(len(text.split()), 25)
            self.assertNotIn('\n', text)
            self.assertNotIn('stock', text.lower())
            self.assertNotIn('reserv', text.lower())

    def test_explicit_photo_and_payment_requests_keep_their_priority(self):
        base = dict(product='henley', color='Azul y Negro', size='L')
        result = self.decide(**base, asks_for_photos=True)
        self.assertEqual(result['next_action'], 'send_catalog')
        self.assertEqual(result['photo_count'], 2)
        for flag in ['asks_for_human', 'asks_for_payment', 'has_complaint']:
            result = self.decide(**base, **{flag: True})
            self.assertEqual(result['next_action'], 'handoff')

    def test_catalog_and_shipping_never_gate_on_inventory(self):
        catalog = self.client.get('/fosters/products').json()
        self.assertFalse(catalog['stock_check_required'])
        for product in catalog['products']:
            self.assertFalse(product['stock_check_required'])
            self.assertNotIn('Pancake', product['availability_note'])
        for data in [dict(city='Santa Cruz', location_shared=True),
                     dict(city='La Paz', full_name='Prueba', ci='TEST')]:
            result = self.client.post('/prepare-shipping', json={'order_confirmed': True, **data}).json()
            self.assertTrue(result['handoff_required'])
            self.assertEqual(result['message'], 'Perfecto, querido. Enseguida te contacta alguien del equipo.')
