#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Network connectivity manager for Mergen.

Provides internet connectivity detection, retry logic,
and graceful offline mode handling.
"""

import os
import socket
import time
from enum import Enum
from typing import Any, Callable, Optional

from src.core.logger import get_logger

logger = get_logger(__name__)


class ConnectionState(Enum):
    """Network connection states"""
    ONLINE = "online"
    OFFLINE = "offline"
    CHECKING = "checking"
    UNKNOWN = "unknown"


class NetworkManager:
    """
    Manages network connectivity checks and retry logic.
    
    Features:
    - Fast connectivity checks (Google DNS 8.8.8.8:53)
    - Cached results with configurable TTL
    - Exponential backoff retry
    - Callback support for state changes
    """
    
    def __init__(self, check_interval: int = 30):
        """
        Initialize NetworkManager.
        
        Args:
            check_interval: Seconds between cached checks (default: 30)
        """
        self.check_interval = check_interval
        self.last_check_time = 0.0
        self._state = ConnectionState.UNKNOWN
        self._state_callbacks: list[Callable[[ConnectionState], None]] = []
        
    @property
    def state(self) -> ConnectionState:
        """Get current connection state"""
        return self._state
    
    def add_state_callback(self, callback: Callable[[ConnectionState], None]):
        """Register callback for state changes"""
        self._state_callbacks.append(callback)
    
    def _notify_state_change(self, new_state: ConnectionState):
        """Notify all callbacks of state change"""
        if new_state != self._state:
            self._state = new_state
            for callback in self._state_callbacks:
                try:
                    callback(new_state)
                except Exception as e:
                    logger.warning(f"State callback error: {e}")
    
    def check_connectivity(self, timeout: float = 3.0) -> bool:
        """
        Check internet connectivity (Google DNS).
        
        Args:
            timeout: Connection timeout in seconds
            
        Returns:
            True if online, False if offline
        """
        verbose = os.environ.get("MERGEN_VERBOSE") == "1"
        
        try:
            # Try to connect to Google's public DNS
            sock = socket.create_connection(("8.8.8.8", 53), timeout=timeout)
            sock.close()
            
            if verbose:
                logger.debug("Network: Online")
            
            self._notify_state_change(ConnectionState.ONLINE)
            self.last_check_time = time.time()
            return True
            
        except OSError as e:
            if verbose:
                logger.debug(f"Network: Offline - {e}")
            
            self._notify_state_change(ConnectionState.OFFLINE)
            self.last_check_time = time.time()
            return False
    
    def is_online(self, force_check: bool = False) -> bool:
        """
        Check if online (uses cache if recent).
        
        Args:
            force_check: Skip cache and check immediately
            
        Returns:
            True if likely online, False otherwise
        """
        now = time.time()
        
        # Use cached result if fresh
        if not force_check and (now - self.last_check_time) < self.check_interval:
            return self._state == ConnectionState.ONLINE
        
        # Perform new check
        return self.check_connectivity()
    
    def require_connection(self, operation_name: str = "This operation") -> bool:
        """
        Verify internet connection, show error if offline.
        
        Args:
            operation_name: Name of operation requiring internet
            
        Returns:
            True if online, False if offline
        """
        if not self.is_online():
            logger.error(f"{operation_name} requires internet connection")
            logger.info("Please check your network and try again")
            return False
        return True
    
    def retry_with_backoff(
        self,
        func: Callable,
        max_retries: int = 3,
        initial_delay: float = 1.0,
        backoff_factor: float = 2.0,
        *args,
        **kwargs
    ) -> Optional[Any]:
        """
        Retry function with exponential backoff.
        
        Args:
            func: Function to retry
            max_retries: Maximum retry attempts
            initial_delay: Initial delay in seconds
            backoff_factor: Multiplier for each retry
            *args, **kwargs: Arguments for func
            
        Returns:
            Function result or None if all retries failed
        """
        delay = initial_delay
        verbose = os.environ.get("MERGEN_VERBOSE") == "1"
        
        for attempt in range(max_retries):
            try:
                result = func(*args, **kwargs)
                return result
                
            except (OSError, ConnectionError, TimeoutError) as e:
                if attempt < max_retries - 1:
                    if verbose:
                        logger.warning(f"Retry {attempt + 1}/{max_retries} after {delay:.1f}s: {e}")
                    time.sleep(delay)
                    delay *= backoff_factor
                else:
                    if verbose:
                        logger.error(f"All retries failed: {e}")
                    raise
        
        return None


# Global instance
_network_manager: Optional[NetworkManager] = None


def get_network_manager() -> NetworkManager:
    """Get or create global NetworkManager instance"""
    global _network_manager
    if _network_manager is None:
        _network_manager = NetworkManager()
    return _network_manager
