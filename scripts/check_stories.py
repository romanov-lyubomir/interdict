"""Checks every story file and prints its level and length.

Run from the project root: python scripts/check_stories.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import stories  # noqa: E402

LANGUAGES = ["german", "italian", "spanish", "greek"]
MIN_WORDS, MAX_WORDS = 100, 200
STORIES_PER_LEVEL = 2

problems = []
for language in LANGUAGES:
    try:
        loaded = stories.load_stories(language)
    except stories.StoryError as error:
        problems.append(str(error))
        continue
    for level, level_stories in stories.by_level(loaded):
        if len(level_stories) != STORIES_PER_LEVEL:
            problems.append(f"{language} {level}: {len(level_stories)} stories")
        for story in level_stories:
            print(f"{language:8} {level} {story['words']:4} words  {story['title']}")
            if not MIN_WORDS <= story["words"] <= MAX_WORDS:
                problems.append(f"{language} {story['slug']}: {story['words']} words")

for problem in problems:
    print("PROBLEM:", problem)
sys.exit(1 if problems else 0)
