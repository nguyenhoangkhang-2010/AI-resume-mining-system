from time import perf_counter

from app.extraction.skills.skill_extractor import SkillExtractor

extractor = SkillExtractor()

text = """
Python FastAPI PostgreSQL React Docker Kubernetes
TensorFlow PyTorch Machine Learning Deep Learning
Git GitHub Linux Azure AWS
""" * 200

# Warm up
extractor.extract(text)

start = perf_counter()

for _ in range(100):
    extractor.extract(text)

elapsed = perf_counter() - start

print(f"Total: {elapsed:.3f}s")
print(f"Average: {elapsed / 100:.4f}s")