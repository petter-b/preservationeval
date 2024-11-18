"""Download and parse preservation calculator JavaScript code.

This module handles downloading and parsing of the JavaScript code from
dpcalc.org, used during installation and validation testing.
"""
# tools/common/download.py
from .paths import get_dp_js_path

def download_dp_js(url: str = DP_JS_URL, force: bool = False) -> str:
    """Download and optionally cache the dpcalc JavaScript code.
    
    Args:
        url: URL to download from
        force: If True, download even if cached file exists
        
    Returns:
        The JavaScript code as string
    """
    dp_js_path = get_dp_js_path()
    
    # Use cached file if it exists and force is False
    if not force and dp_js_path.exists():
        return dp_js_path.read_text()
        
    # Download and optionally cache
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    
    dp_js_path.write_text(response.text)
    return response.text