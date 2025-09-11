# test_models.py
from models import get_directory_contents

dirs, files = get_directory_contents("root")
print("Directories:", dirs)
print("Files:", files)