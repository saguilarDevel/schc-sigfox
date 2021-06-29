from time import perf_counter

from firebase_utils import *

t_i = perf_counter()
upload_blob("test", "test")
t_f = perf_counter()
print(f"Upload took {t_f - t_i} seconds")

t_i = perf_counter()
read_blob("test")
t_f = perf_counter()
print(f"Read took {t_f - t_i} seconds")

t_i = perf_counter()
delete_blob("test")
t_f = perf_counter()
print(f"Delete took {t_f - t_i} seconds")
