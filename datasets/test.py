import ctypes

database = ctypes.CDLL("./libdatabase.so")

database.iindex_build_database.restype = None

database.iindex_build_database(b"gutenberg.csv")
