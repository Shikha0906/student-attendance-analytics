"""Cloud storage backends for Student Attendance Analytics.

Supported backends: AWS S3, Azure Blob Storage, GCP Cloud Storage.
Default is local JSON file storage.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
import uuid
import os