"""stage2-screener: systematic Minervini / Weinstein Stage 2 screening for NSE equities."""
from .config import ScreenConfig
from .screens import (
    trend_template,
    stage2_status,
    screen_stage2,
    screen_near_high,
    screen_rs_in_decline,
    screen_bottoming,
)

__all__ = [
    "ScreenConfig",
    "trend_template",
    "stage2_status",
    "screen_stage2",
    "screen_near_high",
    "screen_rs_in_decline",
    "screen_bottoming",
]
__version__ = "1.0.0"
