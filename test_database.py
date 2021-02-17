from database import Database
import config.config as config


Database.initialize(config.BUCKET_NAME)

bitmap = Database.read(config.BUCKET_NAME, 'all_windows/window_2/bitmap_0')
all_windows = Database.read(config.BUCKET_NAME, 'all_windows')
print(all_windows)
print(all_windows[f"window_0"][f"fragment_0_6"])
print(bitmap)
