"""
aria2 RPC Monitor - IDM-style dynamic download optimization

Monitors aria2 downloads in real-time and dynamically adds connections
when download speed is suboptimal.
"""

import asyncio
import logging
from typing import Dict, Optional

import aiohttp

from src.core.logger import get_logger

logger = get_logger(__name__)


class Aria2Monitor:
    """
    Monitor aria2 downloads and optimize dynamically.
    
    Features:
    - Real-time speed monitoring
    - Dynamic connection scaling (16 → 32 threads)
    - Per-connection speed analysis
    - Automatic optimization
    """
    
    def __init__(
        self,
        rpc_url: str = 'http://localhost:6800/jsonrpc',
        rpc_secret: str = 'mergen_secret'
    ):
        self.rpc_url = rpc_url
        self.rpc_secret = rpc_secret
        self.monitoring_tasks: Dict[str, asyncio.Task] = {}
        
    async def start_monitoring(self, gid: str, callback=None):
        """
        Start monitoring a download.
        
        Args:
            gid: aria2 download GID
            callback: Optional callback for status updates
        """
        if gid in self.monitoring_tasks:
            logger.warning(f"Already monitoring {gid}")
            return
        
        task = asyncio.create_task(self._monitor_loop(gid, callback))
        self.monitoring_tasks[gid] = task
        logger.info(f"📊 Started monitoring download: {gid}")
    
    async def stop_monitoring(self, gid: str):
        """Stop monitoring a download."""
        if gid in self.monitoring_tasks:
            self.monitoring_tasks[gid].cancel()
            del self.monitoring_tasks[gid]
            logger.info(f"⏹️ Stopped monitoring: {gid}")
    
    async def _monitor_loop(self, gid: str, callback=None):
        """Main monitoring loop."""
        try:
            while True:
                status = await self._get_status(gid)
                
                if not status:
                    logger.error(f"Failed to get status for {gid}")
                    break
                
                # Check if download is complete
                download_status = status.get('status', '')
                if download_status in ['complete', 'error', 'removed']:
                    logger.info(f"✅ Download {download_status}: {gid}")
                    break
                
                # Optimize connections
                await self._optimize_download(gid, status)
                
                # Call callback if provided
                if callback:
                    try:
                        # Handle both sync and async callbacks
                        if asyncio.iscoroutinefunction(callback):
                            await callback(status)
                        else:
                            callback(status)
                    except Exception as e:
                        logger.error(f"Callback error: {e}")
                
                # Check every second
                await asyncio.sleep(1.0)
                
        except asyncio.CancelledError:
            logger.debug(f"Monitoring cancelled for {gid}")
        except Exception as e:
            logger.error(f"Error monitoring {gid}: {e}")
        finally:
            if gid in self.monitoring_tasks:
                del self.monitoring_tasks[gid]
    
    async def _optimize_download(self, gid: str, status: dict):
        """
        IDM-style optimization: Add connections if download is slow.
        
        Algorithm:
        1. Check current speed vs potential speed
        2. If speed < 50% of potential, add more connections
        3. Max connections: 32 (from default 16)
        """
        try:
            # Get current metrics
            download_speed = int(status.get('downloadSpeed', 0))
            num_connections = int(status.get('numSeeders', 0))  # Active connections
            total_length = int(status.get('totalLength', 0))
            completed_length = int(status.get('completedLength', 0))
            
            if total_length == 0:
                return
            
            # Calculate potential speed (estimate based on connection count)
            # Assume each connection can do ~5 MB/s on average
            potential_speed = num_connections * 5_000_000
            
            # If we're downloading slower than 50% of potential
            if download_speed < potential_speed * 0.5 and num_connections < 32:
                # Add more connections
                new_max = min(num_connections + 4, 32)  # Add 4 at a time, max 32
                
                await self._rpc_call('aria2.changeOption', [
                    f'token:{self.rpc_secret}',
                    gid,
                    {
                        'max-connection-per-server': str(new_max),
                        'split': str(new_max)
                    }
                ])
                
                speed_mb = download_speed / 1_000_000
                logger.info(
                    f"⚡ Optimizing {gid}: "
                    f"{num_connections} → {new_max} connections "
                    f"(current speed: {speed_mb:.1f} MB/s)"
                )
                
        except Exception as e:
            logger.error(f"Error optimizing download: {e}")
    
    async def _get_status(self, gid: str) -> Optional[dict]:
        """Get download status from aria2."""
        try:
            result = await self._rpc_call('aria2.tellStatus', [
                f'token:{self.rpc_secret}',
                gid,
                [
                    'status',
                    'totalLength',
                    'completedLength',
                    'downloadSpeed',
                    'connections',
                    'numSeeders'
                ]
            ])
            return result
        except Exception as e:
            logger.error(f"Error getting status: {e}")
            return None
    
    async def _rpc_call(self, method: str, params: list):
        """
        Call aria2 RPC method.
        
        Args:
            method: RPC method name (e.g., 'aria2.tellStatus')
            params: Method parameters
            
        Returns:
            RPC result or None on error
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.rpc_url,
                    json={
                        'jsonrpc': '2.0',
                        'id': '1',
                        'method': method,
                        'params': params
                    },
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    data = await response.json()
                    
                    if 'error' in data:
                        logger.error(f"RPC error: {data['error']}")
                        return None
                    
                    return data.get('result')
                    
        except aiohttp.ClientError as e:
            logger.error(f"RPC connection error: {e}")
            return None
        except Exception as e:
            logger.error(f"RPC call error: {e}")
            return None
