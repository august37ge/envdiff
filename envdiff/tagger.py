"""Tag keys in a CompareResult with user-defined labels for grouping and reporting."""
from __future__ import annotations

from dataclasses import dataclass, field
from fnmatch import fnmatch
from typing import Dict, List, Optional

from envdiff.comparator import CompareResult


class TagError(Exception):
    """Raised when tagging configuration is invalid."""


@dataclass
class TagRule:
    """A single rule mapping a glob pattern to a tag label."""
    pattern: str
    tag: str

    def matches(self, key: str) -> bool:
        return fnmatch(key, self.pattern)


@dataclass
class TaggedKey:
    key: str
    tags: List[str] = field(default_factory=list)

    def __str__(self) -> str:
        tag_str = ", ".join(self.tags) if self.tags else "(untagged)"
        return f"{self.key} [{tag_str}]"


@dataclass
class TagResult:
    tagged: List[TaggedKey] = field(default_factory=list)

    def by_tag(self, tag: str) -> List[TaggedKey]:
        return [t for t in self.tagged if tag in t.tags]

    def untagged(self) -> List[TaggedKey]:
        return [t for t in self.tagged if not t.tags]

    def all_tags(self) -> List[str]:
        seen: List[str] = []
        for tk in self.tagged:
            for tag in tk.tags:
                if tag not in seen:
                    seen.append(tag)
        return seen


def tag_result(
    result: CompareResult,
    rules: List[TagRule],
    include_values: bool = False,
) -> TagResult:
    """Apply *rules* to every differing key in *result* and return a TagResult."""
    if result is None:
        raise TagError("result must not be None")
    if not isinstance(rules, list):
        raise TagError("rules must be a list of TagRule objects")

    all_keys: List[str] = []
    for kd in result.diffs:
        if kd.key not in all_keys:
            all_keys.append(kd.key)

    tagged_keys: List[TaggedKey] = []
    for key in all_keys:
        matched = [rule.tag for rule in rules if rule.matches(key)]
        tagged_keys.append(TaggedKey(key=key, tags=matched))

    return TagResult(tagged=tagged_keys)
