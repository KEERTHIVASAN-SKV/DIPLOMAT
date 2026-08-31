"""
DIPLOMAT API Module
REST and GraphQL interfaces for enterprise integration
"""

from .diplomat_api import DiplomatAPI, GraphQLInterface, WebhookManager

__all__ = ["DiplomatAPI", "GraphQLInterface", "WebhookManager"]
