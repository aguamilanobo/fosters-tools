import unittest
from fastapi.testclient import TestClient
from main import app


class CompleteOpeningTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def decide(self, **data):
        r = self.client.post('/decide-next-action', json=data)
        self.assertEqual(r.status_code, 200)
        return r.json()

    def assert_complete_opening(self, result, product):
        count = 5 if product == 'henley' else 6
        self.assertEqual(result['next_action'], 'send_catalog')
        self.assertEqual(result['reason'], 'opening')
        self.assertTrue(result['opening_required'])
        self.assertFalse(result['text_only_allowed'])
        self.assertTrue(result['send_product_photos'])
        self.assertTrue(result['send_size_chart'])
        self.assertTrue(result['opening_complete_requires_media'])
        self.assertFalse(result['media_sent'])
        self.assertNotIn('manual_botcake_flow_setup_required', result)
        self.assertEqual(result['media_configuration_status'], 'not_observed_by_backend')
        self.assertEqual(result['photo_count'], count)
        self.assertEqual(len(result['photo_attachments']), count)
        self.assertEqual(result['required_media_count'], count + 1)
        self.assertEqual(result['response_style'], 'complete_product_opening')
        self.assertIsNone(result['max_response_words'])
        self.assertIn('Hola querido', result['opening_intro'])
        self.assertIn('Fosters', result['opening_intro'])
        self.assertIn('M, L y XL', result['opening_intro'])
        self.assertIn('300 Bs' if product == 'henley' else '280 Bs', result['opening_intro'])
        self.assertEqual([s['type'] for s in result['delivery_steps']],
                         ['text', 'product_photos', 'size_chart', 'text'])
        self.assertEqual(len(result['delivery_steps'][1]['attachments']), count)
        self.assertEqual(result['delivery_steps'][3]['text'], result['opening_question'])

    def test_first_ad_price_message_does_not_need_a_photo_request(self):
        for product in ['henley', 'polo']:
            for message in ['Hola, precio?', 'Precio', '¿Cuánto cuestan?', 'Buenos días', 'Hola, quiero más información',
                            'Estoy interesado en las ' + product]:
                with self.subTest(product=product, message=message):
                    result = self.decide(product=product, message=message,
                                         is_opening=False, opening_sent=False)
                    self.assert_complete_opening(result, product)

    def test_interest_flag_alone_cannot_skip_the_opening(self):
        for product in ['henley', 'polo']:
            result = self.decide(product=product, wants_to_buy=True, opening_sent=False)
            self.assert_complete_opening(result, product)

    def test_legacy_product_only_call_also_completes_pending_opening(self):
        for product in ['henley', 'polo']:
            self.assert_complete_opening(self.decide(product=product), product)

    def test_first_unavailable_color_shows_real_catalog_without_inventing_variant(self):
        result = self.decide(product='henley', color='Gris', size='M', wants_to_buy=True)
        self.assert_complete_opening(result, 'henley')
        self.assertNotIn('Gris', [p['color'] for p in result['photo_attachments']])
        self.assertEqual(result['opening_question'], '¿Qué color buscás?')

    def test_first_opening_keeps_all_colors_and_only_asks_missing_size(self):
        result = self.decide(product='henley', color='Negro', wants_to_buy=True)
        self.assert_complete_opening(result, 'henley')
        self.assertEqual(result['opening_question'], '¿Qué talle buscás?')

    def test_followup_price_does_not_repeat_a_completed_opening(self):
        result = self.decide(product='polo', message='Precio?', opening_sent=True)
        self.assertEqual(result['next_action'], 'continue_sales')
        self.assertNotIn('send_product_photos', result)
        self.assertEqual(result['max_response_words'], 25)

    def test_complete_variant_still_advances_without_catalog_or_confirmation(self):
        result = self.decide(product='henley', message='Hola quiero L azul y negra',
                             color='Azul y Negro', size='L', is_opening=True)
        self.assertEqual(result['next_action'], 'ask_destination')
        self.assertEqual(result['message'], '¿De qué ciudad sos?')
        self.assertNotIn('send_product_photos', result)

    def test_priority_questions_and_handoff_do_not_trigger_openings(self):
        for flag in ['asks_for_human', 'asks_for_payment', 'has_complaint']:
            result = self.decide(product='polo', message='Hola precio', **{flag: True})
            self.assertEqual(result['next_action'], 'handoff')
            self.assertNotIn('send_product_photos', result)
        self.assertEqual(self.decide(product='henley', message='Hola precio',
                                    asks_for_store_location=True)['next_action'], 'answer_store_location')
        self.assertEqual(self.decide(product='henley', message='Hola precio',
                                    asks_for_discount=True, quantity=2)['next_action'], 'get_discount')
        for message in ['Hola, hacen envíos a La Paz?', 'Hola quiero cambiar mi pedido']:
            self.assertNotIn('send_product_photos', self.decide(product='henley', message=message))

    def test_general_has_no_product_photos_and_choice_then_opens_product(self):
        general = self.decide(message='Hola precio')
        self.assertEqual(general['next_action'], 'ask_product')
        self.assertFalse(general['send_product_photos'])
        result = self.decide(product='polo', message='Quiero las polos')
        self.assert_complete_opening(result, 'polo')

    def test_campaign_endpoint_uses_same_complete_bundle(self):
        for product in ['henley', 'polo']:
            response = self.client.get('/fosters/campaign-reply', params={'product': product})
            result = response.json()
            self.assertTrue(result['opening_required'])
            self.assertFalse(result['text_only_allowed'])
            self.assertEqual(result['response_style'], 'complete_product_opening')
            self.assertIsNone(result['max_response_words'])
            self.assertIn('Hola querido', result['opening_intro'])
