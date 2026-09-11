#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Base Service class for all services
"""


class BaseService:
    """
    Base class for all service implementations.
    Provides common functionality and interface for services.
    """

    def __init__(self):
        """Initialize the base service."""
        pass

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        pass
