from importlib.metadata import version
from deepeval.metrics import HallucinationMetric
import inspect

print("DeepEval version:", version("deepeval"))
print("Metric source:", inspect.getfile(HallucinationMetric))
print(inspect.getsource(HallucinationMetric))