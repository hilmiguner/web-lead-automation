"""Website demo generation primitives."""

from web_lead_automation.demo.generator import (
    DemoGenerationError,
    DemoGenerationRequest,
    DemoGenerator,
    GeneratedDemo,
    SavedDemoDraft,
    demo_slug,
)
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
    "DemoGenerationError",
    "DemoGenerationRequest",
    "DemoGenerator",
    "DemoService",
    "DemoTemplateContext",
    "DemoTheme",
    "GeneratedDemo",
    "SavedDemoDraft",
    "THEMES",
    "ThemeKey",
    "demo_slug",
    "recommend_theme",
    "render_demo_html",
    "resolve_theme",
]
