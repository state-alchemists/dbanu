"""
Union pagination utilities
"""

from typing import Dict, Tuple


def calculate_union_pagination(
    source_counts: Dict[str, int], priority: list[str], limit: int, offset: int
) -> Dict[str, Tuple[int, int]]:
    """
    Calculate which records to fetch from each source for union pagination

    Args:
        source_counts: Dictionary mapping source names to their record counts
        priority: List of source names in priority order
        limit: Total number of records to fetch
        offset: Starting offset in the combined dataset

    Returns:
        Dictionary mapping source names to (limit, offset) tuples
    """
    fetch_plan = {}
    remaining_limit = limit
    current_offset = offset

    for source_name in priority:
        source_count = source_counts[source_name]

        # Skip this source if offset is beyond its records
        if current_offset >= source_count:
            current_offset -= source_count
            continue

        # Calculate how many records to fetch from this source
        source_limit = min(remaining_limit, source_count - current_offset)

        if source_limit > 0:
            fetch_plan[source_name] = (source_limit, current_offset)
            remaining_limit -= source_limit
            # Reset offset for next source
            current_offset = 0

        # Stop if we've reached the limit
        if remaining_limit <= 0:
            break

    return fetch_plan
