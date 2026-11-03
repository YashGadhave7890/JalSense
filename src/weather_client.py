"""
JalSense: Weather API Client Module
Connects to Open-Meteo for live, forecast, and historical weather data.
Implements robust disk-based caching to prevent redundant API calls.
"""

import os
import json
import time
import hashlib
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import requests
import pandas as pd

from src.config import BASE_DIR, OPEN_METEO_BASE_URL, OPEN_METEO_ARCHIVE_URL

logger = logging.getLogger(__name__)

CACHE_DIR = BASE_DIR / "data" / "cache" / "weather"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# Cache TTLs in seconds
FORECAST_CACHE_TTL = 3600       # 1 hour for forecasts
HISTORICAL_CACHE_TTL = 86400 * 30  # 30 days for historical weather records


class WeatherClient:
    """
    Open-Meteo Weather API Client with local disk caching.
    Supports current/forecast weather and historical archive weather.
    """

    def __init__(self, cache_dir: Path = CACHE_DIR):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _get_cache_key(self, endpoint: str, params: Dict[str, Any]) -> str:
        """Generates a deterministic hash key for a request."""
        # Sort params for consistency
        sorted_params = json.dumps(params, sort_keys=True, default=str)
        key_str = f"{endpoint}:{sorted_params}"
        return hashlib.md5(key_str.encode("utf-8")).hexdigest()

    def _get_cached_data(self, cache_key: str, ttl_seconds: int) -> Optional[Dict[str, Any]]:
        """Retrieves cached response if valid and not expired."""
        cache_file = self.cache_dir / f"{cache_key}.json"
        if not cache_file.exists():
            return None
        
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                payload = json.load(f)
            
            cached_at = payload.get("cached_at", 0)
            if (time.time() - cached_at) < ttl_seconds:
                logger.info(f"Loaded weather from cache [{cache_key[:8]}]")
                return payload.get("data")
            else:
                logger.info(f"Weather cache expired for [{cache_key[:8]}]")
                return None
        except Exception as e:
            logger.warning(f"Failed to read cache file {cache_file}: {e}")
            return None

    def _save_to_cache(self, cache_key: str, data: Dict[str, Any]) -> None:
        """Stores response data in cache file."""
        cache_file = self.cache_dir / f"{cache_key}.json"
        try:
            payload = {
                "cached_at": time.time(),
                "cached_at_iso": datetime.utcnow().isoformat(),
                "data": data
            }
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2)
            logger.info(f"Saved weather to cache [{cache_key[:8]}]")
        except Exception as e:
            logger.warning(f"Failed to write cache file {cache_file}: {e}")

    def fetch_current_and_forecast(
        self,
        latitude: float,
        longitude: float,
        days: int = 7,
        force_refresh: bool = False
    ) -> Dict[str, Any]:
        """
        Fetches current and multi-day forecast weather from Open-Meteo.
        Cached with 1-hour TTL to prevent repeated dashboard requests.
        """
        params = {
            "latitude": round(latitude, 4),
            "longitude": round(longitude, 4),
            "daily": [
                "temperature_2m_max",
                "temperature_2m_min",
                "precipitation_sum",
                "relative_humidity_2m_mean"
            ],
            "timezone": "auto",
            "forecast_days": days
        }

        cache_key = self._get_cache_key("forecast", params)
        if not force_refresh:
            cached = self._get_cached_data(cache_key, FORECAST_CACHE_TTL)
            if cached is not None:
                cached["cache_hit"] = True
                return cached

        try:
            logger.info(f"Calling Open-Meteo Forecast API for ({latitude}, {longitude})...")
            response = requests.get(OPEN_METEO_BASE_URL, params=params, timeout=10)
            response.raise_for_status()
            raw_data = response.json()
            daily = raw_data.get("daily", {})

            records = []
            for i, dt in enumerate(daily.get("time", [])):
                t_max = daily.get("temperature_2m_max", [])[i]
                t_min = daily.get("temperature_2m_min", [])[i]
                precip = daily.get("precipitation_sum", [])[i]
                humidity = daily.get("relative_humidity_2m_mean", [])[i]
                t_mean = round((t_max + t_min) / 2.0, 2) if (t_max is not None and t_min is not None) else 25.0

                records.append({
                    "date": dt,
                    "temp_max": t_max,
                    "temp_min": t_min,
                    "temp_mean": t_mean,
                    "rainfall_mm": precip if precip is not None else 0.0,
                    "humidity_pct": humidity if humidity is not None else 50.0
                })

            result = {
                "source": "Open-Meteo Live API",
                "latitude": latitude,
                "longitude": longitude,
                "cache_hit": False,
                "fetched_at": datetime.utcnow().isoformat(),
                "forecast": records
            }

            self._save_to_cache(cache_key, result)
            return result

        except Exception as e:
            logger.warning(f"Open-Meteo Forecast API error: {e}. Checking expired cache or generating fallback.")
            # If network error, try using expired cache before fallback
            cache_file = self.cache_dir / f"{cache_key}.json"
            if cache_file.exists():
                try:
                    with open(cache_file, "r", encoding="utf-8") as f:
                        fallback_cached = json.load(f).get("data", {})
                        fallback_cached["source"] = "Open-Meteo (Stale Cache)"
                        fallback_cached["cache_hit"] = True
                        return fallback_cached
                except Exception:
                    pass

            # Fallback
            fallback_records = []
            now = datetime.now()
            for i in range(days):
                fallback_records.append({
                    "date": (now + timedelta(days=i)).strftime("%Y-%m-%d"),
                    "temp_max": 32.0,
                    "temp_min": 22.0,
                    "temp_mean": 27.0,
                    "rainfall_mm": 0.0,
                    "humidity_pct": 55.0
                })
            return {
                "source": "Offline Fallback",
                "latitude": latitude,
                "longitude": longitude,
                "cache_hit": False,
                "forecast": fallback_records
            }

    def fetch_historical_weather(
        self,
        latitude: float,
        longitude: float,
        start_date: str,
        end_date: str,
        force_refresh: bool = False
    ) -> pd.DataFrame:
        """
        Fetches historical daily weather records from Open-Meteo Archive API.
        Cached with 30-day TTL since historical meteorological data is static.
        """
        params = {
            "latitude": round(latitude, 4),
            "longitude": round(longitude, 4),
            "start_date": start_date,
            "end_date": end_date,
            "daily": [
                "temperature_2m_max",
                "temperature_2m_min",
                "precipitation_sum",
                "relative_humidity_2m_mean"
            ],
            "timezone": "auto"
        }

        cache_key = self._get_cache_key("archive", params)
        if not force_refresh:
            cached = self._get_cached_data(cache_key, HISTORICAL_CACHE_TTL)
            if cached is not None:
                return pd.DataFrame(cached.get("records", []))

        try:
            logger.info(f"Calling Open-Meteo Archive API for ({latitude}, {longitude}) from {start_date} to {end_date}...")
            response = requests.get(OPEN_METEO_ARCHIVE_URL, params=params, timeout=15)
            response.raise_for_status()
            raw_data = response.json()
            daily = raw_data.get("daily", {})

            records = []
            dates = daily.get("time", [])
            t_max_list = daily.get("temperature_2m_max", [])
            t_min_list = daily.get("temperature_2m_min", [])
            precip_list = daily.get("precipitation_sum", [])
            hum_list = daily.get("relative_humidity_2m_mean", [])

            for i, dt in enumerate(dates):
                t_max = t_max_list[i] if i < len(t_max_list) else None
                t_min = t_min_list[i] if i < len(t_min_list) else None
                precip = precip_list[i] if i < len(precip_list) else 0.0
                hum = hum_list[i] if i < len(hum_list) else 50.0

                t_mean = (t_max + t_min) / 2.0 if (t_max is not None and t_min is not None) else 25.0

                records.append({
                    "date": dt,
                    "temp_max": t_max,
                    "temp_min": t_min,
                    "temp_mean": round(t_mean, 2),
                    "rainfall_mm": precip if precip is not None else 0.0,
                    "humidity_pct": hum if hum is not None else 50.0
                })

            # Save to cache
            self._save_to_cache(cache_key, {"records": records})
            return pd.DataFrame(records)

        except Exception as e:
            logger.warning(f"Open-Meteo Archive API error: {e}. Returning simulated historical weather.")
            dt_range = pd.date_range(start=start_date, end=end_date, freq="D")
            sim_records = []
            for dt in dt_range:
                sim_records.append({
                    "date": dt.strftime("%Y-%m-%d"),
                    "temp_max": 28.0,
                    "temp_min": 18.0,
                    "temp_mean": 23.0,
                    "rainfall_mm": 0.0,
                    "humidity_pct": 55.0
                })
            return pd.DataFrame(sim_records)


# Global default client instance
weather_client = WeatherClient()
