"""
Performance measurement utilities for advanced sampling and consistency checks.
"""
import asyncio
import statistics
from typing import List, Dict, Any, Optional, Literal
from time import perf_counter
import aiohttp
from urllib.parse import urlparse


async def preflight_ping_test(
    base_url: str,
    session: aiohttp.ClientSession,
    num_samples: int = 7
) -> Dict[str, Any]:
    """
    Run pre-flight ping test to measure network baseline RTT.
    
    Args:
        base_url: Base URL to test
        session: aiohttp session to use
        num_samples: Number of samples (default 7, between 5-10)
    
    Returns:
        Dictionary with ping test results
    """
    parsed = urlparse(base_url)
    test_url = f"{parsed.scheme}://{parsed.netloc}/"
    
    rtt_times: List[float] = []
    
    for i in range(num_samples):
        try:
            start_time = perf_counter()
            async with session.head(test_url, allow_redirects=True) as response:
                await response.read()  # Read to completion
                end_time = perf_counter()
                rtt_ms = (end_time - start_time) * 1000
                rtt_times.append(rtt_ms)
        except Exception as e:
            print(f"Pre-flight ping sample {i+1} failed: {e}")
            continue
    
    if not rtt_times:
        return {
            "samples": 0,
            "avg_rtt_ms": None,
            "min_rtt_ms": None,
            "max_rtt_ms": None
        }
    
    return {
        "samples": len(rtt_times),
        "avg_rtt_ms": round(statistics.mean(rtt_times), 2),
        "min_rtt_ms": round(min(rtt_times), 2),
        "max_rtt_ms": round(max(rtt_times), 2)
    }


def simulate_bandwidth_throttling(
    measured_time_ms: float,
    content_length_bytes: int,
    bandwidth_mbps: float = 5.0
) -> float:
    """
    Simulate bandwidth throttling by adding network transfer time.
    
    Args:
        measured_time_ms: Actual measured fetch time in milliseconds
        content_length_bytes: Size of content in bytes
        bandwidth_mbps: Simulated bandwidth in Mbps (default 5.0)
    
    Returns:
        Effective load time including simulated network transfer
    """
    # Convert Mbps to bytes per second
    bytes_per_second = (bandwidth_mbps * 1_000_000) / 8
    
    # Calculate additional network time
    if content_length_bytes > 0:
        simulated_network_seconds = content_length_bytes / bytes_per_second
        simulated_network_ms = simulated_network_seconds * 1000
    else:
        simulated_network_ms = 0
    
    # Effective load time = measured time + simulated network time
    effective_load_ms = measured_time_ms + simulated_network_ms
    
    return effective_load_ms


def compute_performance_consistency(
    load_times: List[float],
    min_samples: int = 5
) -> tuple[str, str]:
    """
    Compute performance consistency based on variance.
    
    Args:
        load_times: List of load times in milliseconds
        min_samples: Minimum samples required for consistency check
    
    Returns:
        Tuple of (consistency_level, note)
    """
    if len(load_times) < min_samples:
        return ("unknown", "Insufficient samples for consistency check")
    
    avg = statistics.mean(load_times)
    if avg <= 0:
        return ("unknown", "Invalid average load time")
    
    stdev = statistics.stdev(load_times) if len(load_times) > 1 else 0.0
    variance_ratio = stdev / avg if avg > 0 else 0.0
    
    if variance_ratio > 0.4:
        consistency = "unstable"
        note = "Load times fluctuate significantly between requests"
    elif variance_ratio > 0.2:
        consistency = "moderate"
        note = "Load times show moderate variability across pages"
    else:
        consistency = "stable"
        note = "Measurements stable across pages"
    
    return (consistency, note)


def aggregate_performance_samples(
    samples: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Aggregate performance samples for a single page.
    
    Args:
        samples: List of sample dictionaries with load_ms, ttfb_ms, render_mode
    
    Returns:
        Aggregated metrics dictionary
    """
    if not samples:
        return {}
    
    load_times = [s.get("load_ms", 0) for s in samples if s.get("load_ms") is not None]
    ttfb_times = [s.get("ttfb_ms", 0) for s in samples if s.get("ttfb_ms") is not None]
    
    if not load_times:
        return {}
    
    result = {
        "sample_count": len(samples),
        "avg_load_ms": round(statistics.mean(load_times), 2),
        "median_load_ms": round(statistics.median(load_times), 2),
        "min_load_ms": round(min(load_times), 2),
        "max_load_ms": round(max(load_times), 2),
    }
    
    if len(load_times) > 1:
        result["stdev_load_ms"] = round(statistics.stdev(load_times), 2)
    else:
        result["stdev_load_ms"] = 0.0
    
    if ttfb_times:
        result["avg_ttfb_ms"] = round(statistics.mean(ttfb_times), 2)
        result["min_ttfb_ms"] = round(min(ttfb_times), 2)
        result["max_ttfb_ms"] = round(max(ttfb_times), 2)
    
    # Determine render mode (all samples should have same mode for a page)
    render_modes = [s.get("render_mode", "raw") for s in samples]
    if render_modes:
        result["render_mode"] = render_modes[0]  # All samples should be same mode
    
    return result

