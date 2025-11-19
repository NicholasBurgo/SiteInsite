"""
PDF configuration for pdfkit.
Handles wkhtmltopdf binary path configuration.
"""
import os
import pdfkit


def get_pdfkit_config():
    """
    Get pdfkit configuration with optional custom wkhtmltopdf path.
    
    Users can set WKHTMLTOPDF_PATH environment variable to specify
    the path to the wkhtmltopdf binary if it's not on PATH.
    
    Example:
        export WKHTMLTOPDF_PATH="/usr/bin/wkhtmltopdf"
    """
    wkhtml_path = os.getenv("WKHTMLTOPDF_PATH")
    if wkhtml_path:
        return pdfkit.configuration(wkhtmltopdf=wkhtml_path)
    # Assume wkhtmltopdf is on PATH
    return pdfkit.configuration()

