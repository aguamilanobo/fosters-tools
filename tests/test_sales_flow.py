import unittest

from main import (
    NextActionRequest, decide_next_action,
    AguaNextActionRequest, decide_agua_next_action,
)
from agua_sales_v2 import Lead, next_action
from fosters_upsell import OfferRequest, offer, DecisionRequest, decision
from sales_policy import LOCATION_REPLY, store_info


class SalesFlowTests(unittest.TestCase):
    def test_location_exact_across_bots(self):
        routes = [
            (NextActionRequest, decide_next_action),
            (AguaNextActionRequest, decide_agua_next_action),
            (Lead, next_action),
        ]
        for model, handler in routes:
            with self.subTest(model=model.__name__):
                result = handler(model(asks_for_store_location=True, wants_to_buy=True))
                self.assertEqual(result['message'], LOCATION_REPLY)
                self.assertTrue(result['stop_after_reply'])
                self.assertEqual(result['missing_fields'], [])
        self.assertEqual(store_info()['message'], LOCATION_REPLY)

    def test_human_payment_and_complaint_keep_priority(self):
        for field in ['asks_for_human', 'asks_for_payment', 'has_complaint']:
            for model, handler in [(NextActionRequest, decide_next_action),
                                   (AguaNextActionRequest, decide_agua_next_action),
                                   (Lead, next_action)]:
                with self.subTest(field=field, model=model.__name__):
                    result = handler(model(asks_for_store_location=True, **{field: True}))
                    self.assertEqual(result['next_action'], 'handoff')

    def test_explicit_photos_work_with_selected_color(self):
        for field in ['asks_for_photos', 'asks_for_catalog']:
            for model, handler in [(NextActionRequest, decide_next_action),
                                   (AguaNextActionRequest, decide_agua_next_action)]:
                with self.subTest(field=field, model=model.__name__):
                    result = handler(model(color='Negro', **{field: True}))
                    self.assertEqual(result['next_action'], 'send_catalog')
                    self.assertEqual(result['color'], 'Negro')
                    self.assertTrue(result['send_product_photos'])
                    self.assertEqual(result['media_delivery'], 'botcake_flow_required')

    def test_ready_order_does_not_reopen_sale(self):
        for model, handler in [(NextActionRequest, decide_next_action),
                               (AguaNextActionRequest, decide_agua_next_action)]:
            for delivery in [dict(city='Santa Cruz', location_shared=True),
                             dict(city='La Paz', full_name='Cliente de prueba', ci='TEST')]:
                with self.subTest(model=model.__name__, delivery=delivery):
                    result = handler(model(product='henley', color='Negro', size='M',
                                           wants_to_buy=True, **delivery))
                    self.assertEqual(result['next_action'], 'handoff')

    def test_buying_intent_alone_does_not_trigger_upsell(self):
        data = dict(shirt_color='Negro', shirt_size='M', buying_intent=True)
        self.assertFalse(offer(OfferRequest(**data))['should_offer'])
        result = offer(OfferRequest(customer_requested_upsell=True, **data))
        self.assertTrue(result['should_offer'])
        self.assertIn('300 Bs', result['message'])
        self.assertNotIn('270', result['message'])
        self.assertFalse(result['do_not_handoff_yet'])
        self.assertFalse(offer(OfferRequest(customer_requested_upsell=True,
                                          already_handed_off=True, **data))['should_offer'])

    def test_accepted_upsell_total_unchanged(self):
        result = decision(DecisionRequest(decision='si', short_color='perla', short_size='M'))
        self.assertEqual(result['total_bs'], 550)
        self.assertFalse(result['order_created'])


if __name__ == '__main__':
    unittest.main()
