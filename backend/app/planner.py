from __future__ import annotations

import re
from typing import Protocol

from .models import AppSpec, ComponentSpec, PageSpec


class Planner(Protocol):
    def plan(self, prompt: str) -> AppSpec:
        """Turn a natural-language app request into a structured app specification."""


class HeuristicPlanner:
    """Deterministic MVP planner used until a real model provider is configured."""

    def plan(self, prompt: str) -> AppSpec:
        text = prompt.strip()
        lower = text.lower()

        app_type = self._detect_app_type(lower)
        name = self._make_name(text, app_type)
        pages = self._detect_pages(lower, app_type)
        features = self._detect_features(lower)
        components = self._components_for(pages, features)
        routes = [page.route for page in pages]

        dependencies = ["html", "css", "javascript"]
        if any("form" in feature.lower() for feature in features):
            dependencies.append("form-validation")

        return AppSpec(
            name=name,
            app_type=app_type,
            pages=pages,
            components=components,
            features=features,
            routes=routes,
            data_requirements=self._detect_data_requirements(lower),
            dependencies=dependencies,
            styling_direction=self._detect_styling(lower),
            constraints=[
                "Responsive on mobile and desktop",
                "Accessible semantic structure",
                "Keep the generated project simple and maintainable",
            ],
        )

    @staticmethod
    def _detect_app_type(prompt: str) -> str:
        types = (
            ("restaurant", "restaurant website"),
            ("portfolio", "portfolio website"),
            ("saas", "SaaS application"),
            ("dashboard", "dashboard application"),
            ("blog", "blog website"),
            ("shop", "e-commerce website"),
            ("landing", "landing page"),
        )
        for keyword, label in types:
            if keyword in prompt:
                return label
        return "web application"

    @staticmethod
    def _make_name(prompt: str, app_type: str) -> str:
        match = re.search(r"(?:called|named)\s+['\"]?([A-Za-z0-9][A-Za-z0-9 _-]{1,48})", prompt, re.I)
        if match:
            return match.group(1).strip(" .,'\"")
        return app_type.title()

    @staticmethod
    def _detect_pages(prompt: str, app_type: str) -> list[PageSpec]:
        candidates = [
            ("home", "/", "Primary entry point and overview"),
            ("about", "/about", "Explain the product, business, or story"),
            ("menu", "/menu", "Present available items or offerings"),
            ("contact", "/contact", "Let visitors contact the business or team"),
            ("pricing", "/pricing", "Present plans and pricing"),
            ("features", "/features", "Explain key capabilities"),
            ("dashboard", "/dashboard", "Main authenticated workspace"),
            ("profile", "/profile", "User profile and account details"),
            ("blog", "/blog", "List published articles"),
            ("shop", "/shop", "Browse products or services"),
        ]

        selected: list[PageSpec] = []
        for keyword, route, purpose in candidates:
            if keyword == "home" or keyword in prompt:
                selected.append(PageSpec(name=keyword.title(), route=route, purpose=purpose))

        if app_type == "restaurant website" and not any(p.route == "/menu" for p in selected):
            selected.append(PageSpec(name="Menu", route="/menu", purpose="Present the restaurant menu"))

        if app_type == "portfolio website" and not any(p.route == "/about" for p in selected):
            selected.append(PageSpec(name="Work", route="/work", purpose="Showcase selected work and projects"))

        return selected[:8]

    @staticmethod
    def _detect_features(prompt: str) -> list[str]:
        checks = (
            ("contact form", ("contact form", "contact us", "contact")),
            ("responsive layout", ("responsive", "mobile")),
            ("search", ("search", "find")),
            ("authentication", ("login", "sign in", "authentication", "signup", "sign up")),
            ("navigation", ("navigation", "navbar", "nav")),
            ("gallery", ("gallery", "photos", "images")),
            ("shopping cart", ("cart", "checkout", "e-commerce", "shop")),
            ("pricing section", ("pricing", "plans")),
        )
        features = [label for label, keywords in checks if any(keyword in prompt for keyword in keywords)]
        if "navigation" not in features:
            features.append("navigation")
        if "responsive layout" not in features:
            features.append("responsive layout")
        return features

    @staticmethod
    def _components_for(pages: list[PageSpec], features: list[str]) -> list[ComponentSpec]:
        components = [
            ComponentSpec(name="Header", purpose="Global navigation and branding"),
            ComponentSpec(name="Footer", purpose="Global footer and supporting links"),
        ]
        if any(page.route == "/" for page in pages):
            components.append(ComponentSpec(name="Hero", purpose="Primary value proposition and call to action"))
        if "gallery" in features:
            components.append(ComponentSpec(name="Gallery", purpose="Responsive image collection"))
        if "contact form" in features:
            components.append(ComponentSpec(name="ContactForm", purpose="Collect visitor contact information"))
        if "pricing section" in features:
            components.append(ComponentSpec(name="PricingCards", purpose="Present plans and pricing"))
        return components

    @staticmethod
    def _detect_data_requirements(prompt: str) -> list[str]:
        data = []
        if any(word in prompt for word in ("form", "contact", "signup", "login")):
            data.append("User-submitted form data")
        if any(word in prompt for word in ("shop", "product", "cart", "checkout")):
            data.append("Products and cart state")
        return data

    @staticmethod
    def _detect_styling(prompt: str) -> str:
        if "dark" in prompt:
            return "Dark, modern, high-contrast interface"
        if "minimal" in prompt or "apple" in prompt:
            return "Minimal, premium, spacious interface"
        if "purple" in prompt:
            return "Clean interface with purple accent and soft surfaces"
        return "Clean, modern, responsive interface"
