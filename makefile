WARNINGS=-fdiagnostics-color=always -Wall -Wcast-align -Wcast-qual -Wconversion -Wctor-dtor-privacy -Wdisabled-optimization -Wdouble-promotion -Wduplicated-branches -Wduplicated-cond -Wextra -Wformat=2 -Winit-self -Wlogical-op -Wmissing-include-dirs -Wno-sign-conversion -Wnoexcept -Wnull-dereference -Wold-style-cast -Woverloaded-virtual -Wpedantic -Wredundant-decls -Wrestrict -Wshadow -Wstrict-aliasing=1 -Wstrict-null-sentinel -Wstrict-overflow=5 -Wswitch-default -Wundef -Wno-unknown-pragmas -Wuseless-cast -Wno-unknown-warning-option
FLAGS=-g -fPIC -isystem third-party -isystem third-party/sparsehash/src -std=c++17 -O0

all: datasets/libdatabase.so

datasets/libdatabase.so: datasets/database.cpp
	$(CXX) $(WARNINGS) $(FLAGS) -shared -o datasets/libdatabase.so datasets/database.cpp -lsqlite3 -lpthread -licuio -licui18n -licuuc -licudata

clean:
	rm -f datasets/libdatabase.so