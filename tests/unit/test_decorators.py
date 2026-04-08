"""Tests for lazy implementation decorators (@lazy, @lazy_fn, @lazy_class).

NOTE: The @lazy, @lazy_fn, @lazy_class decorators have been extracted to the
separate 'lazy-impl' package (https://github.com/benbuzz790/lazy-impl).
These tests are skipped until migrated to that package.
Install with: pip install lazy-impl

TODO: Migrate these tests to lazy-impl or remove by 2026-06-01 (see WO053)
"""

import pytest

pytest.skip("lazy decorators moved to lazy-impl package", allow_module_level=True)
