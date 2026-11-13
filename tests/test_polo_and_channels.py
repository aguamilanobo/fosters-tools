import unittest
from unittest.mock import patch

from fosters_products import products, product, campaign_reply, media_plan, product_key
from main import (NextActionRequest, decide_next_action, OrderPrepRequest, prepare_order,
                  FostersPaymentSummaryRequest, fosters_payment_summary, get_discount)


class PoloAndChannelTests(unittest.TestCase):
    def test_polo_catalog_and_plomo_alias(self):
        p = product(product='polo', color='plomo')['product']
        self.assertEqual(p['selected_color'], 'Gris')
        self.assertEqual(p['sizes'], ['M', 'L', 'XL'])
        self.assertEqual(p['price_bs'], 300)
        self.assertEqual(len(p['colors']), 6)
        self.assertEqual(p['material_label'], 'Algodón texturizado')
        self.assertFalse(product(product='henley', color='plomo')['found'])

    def test_general_opening_does_not_choose_or_send_product(self):
        for result in [campaign_reply(), decide_next_action(NextActionRequest(is_opening=True)),
                       decide_next_action(NextActionRequest(message='Hola querido', is_opening=True))]:
            self.assertEqual(result['campaign_key'], 'general')
            self.assertEqual(result['next_action'], 'ask_product')
            self.assertEqual(result['photo_count'], 0)
            self.assertFalse(result['send_product_photos'])
            self.assertIn('Henley de lino', result['suggested_reply'])
            self.assertIn('Polo de algodón texturizado', result['suggested_reply'])

    def test_ad_messages_select_correct_opening(self):
        for text, key, count in [('Hola estoy interesado en las polos', 'polo', 6),
                                 ('Hola, quiero una Polo de algodón texturizado', 'polo', 6),
                                 ('Estoy interesado en la Henley', 'henley', 5)]:
            with self.subTest(text=text):
                result = decide_next_action(NextActionRequest(message=text, is_opening=True))
                self.assertEqual(result['campaign_key'], key)
                self.assertEqual(result['photo_count'], count)
                self.assertTrue(result['send_size_chart'])
                self.assertFalse(result['media_sent'])
        switched = decide_next_action(NextActionRequest(product='henley',
            message='Quiero las polos', is_opening=True))
        self.assertEqual(switched['product'], 'polo')

    def test_polo_media_is_separate_and_needs_real_bindings(self):
        plan = media_plan(product='polo')
        self.assertEqual(len({p['attachment_key'] for p in plan['photo_attachments']}), 6)
        self.assertTrue(plan['media_bindings_required'])
        self.assertTrue(all(p['filename'] is None for p in plan['photo_attachments']))
        gray = media_plan('plomo', product='polo')
        self.assertEqual(gray['photo_count'], 1)
        self.assertEqual(gray['color'], 'Gris')
        self.assertEqual(gray['photo_attachments'][0]['attachment_key'], 'polo_gris')

    def test_polo_order_keeps_product_and_normalizes_variant(self):
        order = prepare_order(OrderPrepRequest(product='polos', color='plomo', size='xl', city='Santa Cruz'))
        self.assertTrue(order['ready_to_order'])
        self.assertEqual((order['product'], order['color'], order['size']), ('polo', 'Gris', 'XL'))
        self.assertFalse(order['order_created'])
        invalid = prepare_order(OrderPrepRequest(product='henley', color='gris', size='S', city='La Paz'))
        self.assertFalse(invalid['ready_to_order'])
        self.assertEqual(invalid['missing_fields'], ['color', 'size'])

    def test_unknown_product_needs_selection_before_order(self):
        self.assertIsNone(product_key('Henley y Polo'))
        self.assertEqual(prepare_order(OrderPrepRequest(color='Negro', size='M', city='La Paz'))['next_action'], 'ask_product')
        self.assertEqual(decide_next_action(NextActionRequest(wants_to_buy=True))['next_action'], 'ask_product')

    def test_handoff_discount_and_shipping_priorities(self):
        for key in ['henley', 'polo']:
            for flag in ['asks_for_payment', 'asks_for_human', 'has_complaint']:
                result = decide_next_action(NextActionRequest(product=key, is_opening=True, **{flag: True}))
                self.assertEqual(result['next_action'], 'handoff')
            self.assertEqual(decide_next_action(NextActionRequest(product=key, is_opening=True,
                asks_for_discount=True, quantity=2))['next_action'], 'get_discount')
            self.assertEqual(decide_next_action(NextActionRequest(product=key, is_opening=True,
                wants_to_buy=True, color='Negro', size='M', city='Santa Cruz', location_shared=True))['next_action'], 'handoff')
        for quantity, total in [(2, 560), (3, 810), (5, 1250)]:
            self.assertEqual(get_discount(quantity)['total_bs'], total)

    def test_opening_not_repeated_but_requested_photos_can_repeat(self):
        for key in ['henley', 'polo']:
            self.assertEqual(decide_next_action(NextActionRequest(product=key, is_opening=True,
                opening_sent=True))['next_action'], 'continue_sales')
            self.assertEqual(decide_next_action(NextActionRequest(product=key, opening_sent=True,
                asks_for_photos=True))['next_action'], 'send_catalog')

    def test_web_orders_cannot_trigger_sales_or_printer(self):
        self.assertFalse(products()['web_orders_enabled'])
        for kwargs in [dict(web_order=True), dict(message='Hola Fosters, quiero hacer este pedido (42)'),
                       dict(message='Mi pedido en fostersbolivia.shop')]:
            action = decide_next_action(NextActionRequest(product='polo', is_opening=True, **kwargs))
            self.assertEqual(action['reason'], 'web_orders_disabled')
            order = prepare_order(OrderPrepRequest(product='polo', **kwargs))
            self.assertFalse(order['ready_to_order'])
        with patch('main.urllib_request.urlopen') as outbound:
            summary = fosters_payment_summary(FostersPaymentSummaryRequest(web_order=True, items='Polo Negro M'))
            self.assertFalse(summary['should_send_summary'])
            outbound.assert_not_called()

    def test_polo_summary_never_becomes_henley(self):
        with patch.dict('os.environ', {'PRINTER_TELEGRAM_BOT_TOKEN': '', 'PRINTER_TELEGRAM_CHAT_ID': ''}):
            summary = fosters_payment_summary(FostersPaymentSummaryRequest(
                items='Polo Gris XL', full_name='Prueba', ci='TEST', department='La Paz', phone='TEST'))
        self.assertTrue(summary['ready_for_payment'])
        self.assertIn('Polo Gris XL', summary['summary_message'])
        self.assertNotIn('Henley', summary['summary_message'])
