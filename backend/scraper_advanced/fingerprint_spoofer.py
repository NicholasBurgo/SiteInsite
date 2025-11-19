import random
import hashlib
import time
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import numpy as np

@dataclass
class BrowserFingerprint:
    """Complete browser fingerprint for spoofing"""
    user_agent: str
    screen_resolution: tuple
    viewport_size: tuple
    timezone: str
    language: str
    platform: str
    hardware_concurrency: int
    device_memory: float
    canvas_hash: str
    webgl_hash: str
    fonts: List[str]
    plugins: List[str]
    webdriver: bool = False

class FingerprintSpoofer:
    """Generate realistic browser fingerprints"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.screen_resolutions = [
            (1920, 1080), (1366, 768), (1536, 864), (1440, 900),
            (1280, 720), (1680, 1050), (1600, 900), (2560, 1440)
        ]

        self.timezones = [
            "America/New_York", "America/Los_Angeles", "America/Chicago",
            "America/Denver", "Europe/London", "Europe/Paris", "Asia/Tokyo",
            "Australia/Sydney", "Pacific/Auckland"
        ]

        self.languages = [
            "en-US", "en-GB", "en-CA", "en-AU", "fr-FR", "de-DE",
            "es-ES", "it-IT", "pt-BR", "ja-JP", "zh-CN"
        ]

        self.common_fonts = [
            "Arial", "Arial Black", "Arial Narrow", "Calibri", "Cambria",
            "Candara", "Comic Sans MS", "Consolas", "Constantia", "Corbel",
            "Courier New", "Franklin Gothic Medium", "Gabriola", "Gadugi",
            "Georgia", "Impact", "Lucida Console", "Lucida Sans Unicode",
            "Microsoft Sans Serif", "Palatino Linotype", "Segoe UI",
            "Segoe UI Light", "Segoe UI Semibold", "Segoe UI Symbol",
            "Tahoma", "Times New Roman", "Trebuchet MS", "Verdana"
        ]

        self.plugins = [
            "Chrome PDF Plugin", "Chrome PDF Viewer", "Native Client",
            "WebKit built-in PDF", "Chromium PDF Plugin"
        ]

    def generate_fingerprint(self, browser_profile: str = "chrome124") -> BrowserFingerprint:
        """Generate a complete browser fingerprint"""

        # Get base profile
        profile_config = self.config.get('browser_profiles', {}).get(browser_profile, {})

        # Randomize components
        screen_res = self._random_screen_resolution()
        viewport = self._random_viewport_size(screen_res)
        timezone = self._random_timezone()
        language = self._random_language()
        platform = profile_config.get('sec_ch_ua_platform', '"Windows"').strip('"')

        # Generate hardware specs
        hardware_concurrency = random.choice([4, 8, 12, 16])
        device_memory = random.choice([4, 8, 16, 32])

        # Generate canvas and WebGL noise
        canvas_hash = self._generate_canvas_hash() if self.config.get('canvas_noise', True) else ""
        webgl_hash = self._generate_webgl_hash() if self.config.get('webgl_noise', True) else ""

        # Random font subset
        fonts = self._random_font_subset()

        # Browser plugins
        plugins = self._random_plugin_subset()

        return BrowserFingerprint(
            user_agent=profile_config.get('user_agent', ''),
            screen_resolution=screen_res,
            viewport_size=viewport,
            timezone=timezone,
            language=language,
            platform=platform,
            hardware_concurrency=hardware_concurrency,
            device_memory=device_memory,
            canvas_hash=canvas_hash,
            webgl_hash=webgl_hash,
            fonts=fonts,
            plugins=plugins,
            webdriver=False
        )

    def _random_screen_resolution(self) -> tuple:
        """Get random screen resolution"""
        return random.choice(self.screen_resolutions)

    def _random_viewport_size(self, screen_res: tuple) -> tuple:
        """Generate viewport size based on screen resolution"""
        width, height = screen_res
        # Viewport is usually smaller than screen
        viewport_width = random.randint(int(width * 0.7), width)
        viewport_height = random.randint(int(height * 0.6), height)
        return (viewport_width, viewport_height)

    def _random_timezone(self) -> str:
        """Get random timezone"""
        if self.config.get('timezone_random', True):
            return random.choice(self.timezones)
        return "America/New_York"  # Default

    def _random_language(self) -> str:
        """Get random language"""
        if self.config.get('language_random', True):
            return random.choice(self.languages)
        return "en-US"

    def _generate_canvas_hash(self) -> str:
        """Generate unique canvas fingerprint hash"""
        # Simulate canvas fingerprinting by generating noise
        noise_data = {
            'timestamp': time.time(),
            'random_seed': random.random(),
            'noise_pattern': np.random.normal(0, 1, 100).tolist()
        }
        return hashlib.md5(json.dumps(noise_data, sort_keys=True).encode()).hexdigest()[:16]

    def _generate_webgl_hash(self) -> str:
        """Generate unique WebGL fingerprint hash"""
        webgl_data = {
            'vendor': random.choice(['Intel Inc.', 'NVIDIA Corporation', 'AMD']),
            'renderer': f'ANGLE ({random.choice(["Intel", "NVIDIA", "AMD"])} {random.choice(["HD Graphics", "GeForce", "Radeon"])})',
            'version': f'WebGL 1.0 (OpenGL ES 2.0 Chromium)',
            'extensions': random.sample([
                'ANGLE_instanced_arrays', 'EXT_blend_minmax', 'EXT_color_buffer_half_float',
                'EXT_disjoint_timer_query', 'EXT_float_blend', 'EXT_frag_depth'
            ], random.randint(3, 6))
        }
        return hashlib.md5(json.dumps(webgl_data, sort_keys=True).encode()).hexdigest()[:16]

    def _random_font_subset(self) -> List[str]:
        """Get random subset of fonts"""
        if not self.config.get('font_noise', True):
            return self.common_fonts[:10]  # Default subset

        num_fonts = random.randint(15, 25)
        return random.sample(self.common_fonts, num_fonts)

    def _random_plugin_subset(self) -> List[str]:
        """Get random subset of browser plugins"""
        num_plugins = random.randint(2, 5)
        return random.sample(self.plugins, num_plugins)

    def get_selenium_options(self, fingerprint: BrowserFingerprint) -> Dict[str, Any]:
        """Get Selenium options for the fingerprint"""
        options = {
            'user_agent': fingerprint.user_agent,
            'viewport_size': fingerprint.viewport_size,
            'timezone': fingerprint.timezone,
            'language': fingerprint.language,
            'platform': fingerprint.platform,
            'hardware_concurrency': fingerprint.hardware_concurrency,
            'device_memory': fingerprint.device_memory,
            'fonts': fingerprint.fonts,
            'plugins': fingerprint.plugins
        }
        return options

    def get_curl_cffi_headers(self, fingerprint: BrowserFingerprint) -> Dict[str, str]:
        """Get headers for curl_cffi requests"""
        return {
            'User-Agent': fingerprint.user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': f'{fingerprint.language};q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
        }

    def get_session_headers(self, fingerprint: BrowserFingerprint, referer: Optional[str] = None) -> Dict[str, str]:
        """Get headers for maintaining session consistency"""
        headers = self.get_curl_cffi_headers(fingerprint)

        if referer:
            headers['Referer'] = referer
            headers['Sec-Fetch-Site'] = 'same-origin'

        return headers
