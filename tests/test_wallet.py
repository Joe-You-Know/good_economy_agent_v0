import unittest

from agent.wallet import ComputeWallet, EconomicWallet


class WalletTests(unittest.TestCase):
    def test_compute_wallet_respects_hard_stop(self):
        wallet = ComputeWallet(
            starting_credit_usd=1.00,
            hard_stop_remaining_usd=0.25,
            max_single_charge_usd=0.50,
        )
        wallet.charge(0.50, "allowed")
        with self.assertRaises(RuntimeError):
            wallet.charge(0.30, "would cross hard stop")

    def test_compute_wallet_respects_single_charge_cap(self):
        wallet = ComputeWallet(
            starting_credit_usd=2.00,
            hard_stop_remaining_usd=0.25,
            max_single_charge_usd=0.50,
        )
        with self.assertRaises(RuntimeError):
            wallet.charge(0.75, "too large")

    def test_economic_wallet_cannot_spend_unearned_money(self):
        wallet = EconomicWallet(starting_cash_usd=0.0)
        with self.assertRaises(RuntimeError):
            wallet.spend(1.00, "not earned")


if __name__ == "__main__":
    unittest.main()
