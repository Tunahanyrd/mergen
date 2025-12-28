"""
Unit tests for network.py module.

Tests NetworkManager functionality:
- Connectivity checking
- Caching
- Retry logic
- State callbacks
"""

import time
import unittest
from unittest.mock import MagicMock, patch

from src.core.network import ConnectionState, NetworkManager, get_network_manager


class TestNetworkManager(unittest.TestCase):
    """Test NetworkManager class."""
    
    def setUp(self):
        """Create fresh NetworkManager for each test."""
        self.nm = NetworkManager(check_interval=1)
    
    def test_singleton_pattern(self):
        """Test get_network_manager returns same instance."""
        nm1 = get_network_manager()
        nm2 = get_network_manager()
        self.assertIs(nm1, nm2)
    
    @patch('socket.create_connection')
    def test_check_connectivity_online(self, mock_socket):
        """Test successful connectivity check."""
        mock_sock = MagicMock()
        mock_socket.return_value = mock_sock
        
        result = self.nm.check_connectivity()
        
        self.assertTrue(result)
        self.assertEqual(self.nm.state, ConnectionState.ONLINE)
        mock_socket.assert_called_once()
        mock_sock.close.assert_called_once()
    
    @patch('socket.create_connection')
    def test_check_connectivity_offline(self, mock_socket):
        """Test failed connectivity check."""
        mock_socket.side_effect = OSError("Network unreachable")
        
        result = self.nm.check_connectivity()
        
        self.assertFalse(result)
        self.assertEqual(self.nm.state, ConnectionState.OFFLINE)
    
    def test_caching(self):
        """Test result caching with check_interval."""
        with patch('socket.create_connection') as mock_socket:
            mock_sock = MagicMock()
            mock_socket.return_value = mock_sock
            
            # First check
            self.nm.is_online()
            self.assertEqual(mock_socket.call_count, 1)
            
            # Second check (should use cache)
            self.nm.is_online()
            self.assertEqual(mock_socket.call_count, 1)
            
            # Wait for cache expiry
            time.sleep(1.1)
            
            # Third check (should make new request)
            self.nm.is_online()
            self.assertEqual(mock_socket.call_count, 2)
    
    def test_force_check(self):
        """Test forcing check bypasses cache."""
        with patch('socket.create_connection') as mock_socket:
            mock_sock = MagicMock()
            mock_socket.return_value = mock_sock
            
            self.nm.is_online()
            self.assertEqual(mock_socket.call_count, 1)
            
            # Force check should bypass cache
            self.nm.is_online(force_check=True)
            self.assertEqual(mock_socket.call_count, 2)
    
    def test_state_callback(self):
        """Test state change callbacks."""
        callback = MagicMock()
        self.nm.add_state_callback(callback)
        
        with patch('socket.create_connection'):
            self.nm.check_connectivity()
        
        callback.assert_called_once_with(ConnectionState.ONLINE)
    
    @patch('socket.create_connection')
    def test_retry_with_backoff_success(self, mock_socket):
        """Test retry succeeds on second attempt."""
        mock_func = MagicMock()
        mock_func.side_effect = [ConnectionError("Failed"), "Success"]
        
        result = self.nm.retry_with_backoff(mock_func, max_retries=3, initial_delay=0.1)
        
        self.assertEqual(result, "Success")
        self.assertEqual(mock_func.call_count, 2)
    
    def test_retry_with_backoff_exhaust(self):
        """Test retry exhausts all attempts."""
        mock_func = MagicMock()
        mock_func.side_effect = ConnectionError("Always fails")
        
        with self.assertRaises(ConnectionError):
            self.nm.retry_with_backoff(mock_func, max_retries=2, initial_delay=0.05)
        
        self.assertEqual(mock_func.call_count, 2)


if __name__ == '__main__':
    unittest.main()
