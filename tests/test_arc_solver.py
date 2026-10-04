import importlib.util
from pathlib import Path
import unittest

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    'arc_solver', ROOT / 'competitions/arc-prize-2026-arc-agi-2/src/solver.py')
SOLVER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SOLVER)


class ArcSolverTests(unittest.TestCase):
    def test_rotation_and_multiple_test_inputs(self):
        inputs = [[[1, 1, 2], [3, 4, 4]], [[4, 2, 3], [1, 1, 4]]]
        task = {'train': [{'input': grid, 'output': np.rot90(grid).tolist()} for grid in inputs],
                'test': [{'input': grid} for grid in inputs]}
        predictions, _ = SOLVER.solve_task(task)
        self.assertEqual(len(predictions), 2)
        for grid, guesses in zip(inputs, predictions):
            self.assertIn(np.rot90(grid).tolist(), guesses.values())
        SOLVER.validate_submission({'task': task}, {'task': predictions})

    def test_one_rule_must_fit_all_demonstrations(self):
        mapping = SOLVER.fit_mapping([np.array([[1]]), np.array([[1]])],
                                    [np.array([[2]]), np.array([[3]])])
        self.assertIsNone(mapping)

    def test_color_mapping_and_unseen_colors(self):
        task = {'train': [{'input': [[1, 1, 0], [0, 1, 0]],
                           'output': [[2, 2, 0], [0, 2, 0]]}],
                'test': [{'input': [[1, 3, 0], [0, 1, 0]]}]}
        predictions, _ = SOLVER.solve_task(task)
        self.assertEqual(predictions[0]['attempt_1'], [[2, 3, 0], [0, 2, 0]])

    def test_validation_rejects_invalid_grid_and_missing_outputs(self):
        challenge = {'x': {'train': [], 'test': [{'input': [[1]]}]}}
        for submission in ({'x': []}, {'x': [{'attempt_1': [[10]], 'attempt_2': [[0]]}]},
                           {'x': [{'attempt_1': [[1], [1, 2]], 'attempt_2': [[0]]}]}):
            with self.assertRaises(ValueError):
                SOLVER.validate_submission(challenge, submission)

    def test_test_output_field_does_not_leak_into_predictions(self):
        task = {'train': [{'input': [[1, 0]], 'output': [[2, 0]]}],
                'test': [{'input': [[0, 1]]}]}
        before = SOLVER.solve_task(task)
        task['test'][0]['output'] = [[9]]
        self.assertEqual(before, SOLVER.solve_task(task))


if __name__ == '__main__':
    unittest.main()
