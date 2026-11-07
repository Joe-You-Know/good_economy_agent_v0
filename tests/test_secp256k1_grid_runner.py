import unittest

from tools.secp256k1_grid_runner import pair_collision_upper95, parse_int_list


class Secp256k1GridRunnerTests(unittest.TestCase):
    def test_parse_int_list(self):
        self.assertEqual(parse_int_list("1, 2,3"), [1, 2, 3])

    def test_pair_collision_upper95_for_zero_collisions(self):
        bound = pair_collision_upper95(1024, 0)
        self.assertGreater(bound, 0.0)
        self.assertLess(bound, 0.00001)


if __name__ == "__main__":
    unittest.main()
