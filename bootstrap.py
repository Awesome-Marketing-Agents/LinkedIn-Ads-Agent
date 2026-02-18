import os
import sys

# Ensure the `src` directory is in the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.join(current_dir, 'src')
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)