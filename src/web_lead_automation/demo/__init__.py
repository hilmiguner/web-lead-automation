"""Website demo template primitives."""

from web_lead_automation.demo.template import (
    DemoService,
    DemoTemplateContext,
    render_demo_html,
)
from web_lead_automation.demo.theme import (
    DemoTheme,
    THEMES,
    ThemeKey,
    recommend_theme,
    resolve_theme,
)

__all__ = [
    "DemoService",
    "DemoTemplateContext",
    "DemoTheme",
    "THEMES",
    "ThemeKey",
    "recommend_theme",
    "render_demo_html",
    "resolve_theme",
]
