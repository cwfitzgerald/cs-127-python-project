import ctypes

database = ctypes.CDLL("./libdatabase.so")

database.iindex_build_database.restype = None

# database.iindex_build_database(b"offenders.csv")
# database.iindex_build_database(b"gutenberg.csv")
database.iindex_search.restype = ctypes.c_int;
print(database.iindex_search(ctypes.c_int(0), b"hello"));
print(database.iindex_search(ctypes.c_int(0), b"god"));
print(database.iindex_search(ctypes.c_int(0), b"help"));
print(database.iindex_search(ctypes.c_int(0), b"save"));