import pytest

from app.detectors.language_detector import LanguageDetector


CORPUS = [
    ("cpp", '#include <iostream>\nint main(){std::cout << "x"; return 0;}\n'),
    ("cpp", "#include <vector>\nstd::vector<int> values{1,2};\nint main(){return values[0];}\n"),
    ("cpp", "#include <string>\nint main(){std::string value = \"x\"; return 0;}\n"),
    ("cpp", "#include <map>\nint main(){std::map<int,int> m; return m.size();}\n"),
    ("cpp", '#include <iostream>\nint main( { std::cout << "broken"; }\n'),
    ("cpp", "#include <memory>\nint main(){auto p = nullptr; return p == nullptr;}\n"),
    ("cpp", "#include <set>\nusing namespace std;\nint main(){set<int> s; return 0;}\n"),
    ("cpp", "#include <unordered_map>\nint main(){std::unordered_map<int,int> m; return 0;}\n"),
    ("python", "from pathlib import Path\n\ndef f():\n    return Path('.')\n"),
    ("python", "import json\n\nclass Encoder:\n    def run(self):\n        return json.dumps({})\n"),
    ("python", "import asyncio\n\nasync def run():\n    return True\n"),
    ("python", "def main():\n    return None\n\nif __name__ == '__main__':\n    main()\n"),
    ("python", "def total(values):\n    for value in values:\n        if value:\n            return value\n"),
    ("python", "def safe():\n    try:\n        return True\n    except ValueError:\n        return False\n"),
    ("python", "from dataclasses import dataclass\n\n@dataclass\nclass Item:\n    value: int\n"),
    ("python", "from typing import Iterable\n\ndef first(values: Iterable[int]):\n    return next(iter(values))\n"),
    ("unknown", "value = 1"),
    ("unknown", "x + y"),
    ("unknown", "{}"),
    ("unknown", 'print("hello")'),
]


@pytest.mark.parametrize(("expected", "source"), CORPUS)
def test_controlled_language_corpus(expected, source):
    assert LanguageDetector().detect(source).language == expected


def test_corpus_accuracy_meets_prd_target():
    correct = sum(
        LanguageDetector().detect(source).language == expected
        for expected, source in CORPUS
    )

    assert correct / len(CORPUS) >= 0.90
