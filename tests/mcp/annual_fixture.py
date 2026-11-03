"""Invented quarterly rates for offline annual-average protocol tests, not official data."""
import pandas as pd

from labourlens.agent.tools import StatsData


def statistics():
    rows = []
    for year, values in ((2025, [2.1, 2.2, 2.3, 2.34]), (2026, [2.4, 2.5])):
        for quarter, value in enumerate(values, 1):
            rows.append(dict(observation_id=f"{year * 10 + quarter:016x}", source_id="resident_unemployment_rate",
                             indicator_id="rate", population="resident", adjustment="seasonally_adjusted", dimension="",
                             unit="percent", period=f"{year}-Q{quarter}", value=value, in_answer_scope=True,
                             missing_reason="", release_stage="final"))
    return StatsData(pd.DataFrame(rows))


if __name__ == "__main__":
    from labourlens.mcp import server

    server._data = statistics()
    server.mcp.run(transport="stdio")
