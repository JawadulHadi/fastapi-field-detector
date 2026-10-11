import subprocess
import sys
from pathlib import Path

from eval.run_eval import main, score

ROOT = Path(__file__).parent.parent


def test_samples_exist_and_eval_passes_threshold():
    subprocess.run([sys.executable, 'eval/make_samples.py'], cwd=ROOT, check=True)
    result = score()
    assert result['documents'] == 10
    assert result['overall']['f1'] >= 0.9
    assert main(threshold=0.9) == 0
