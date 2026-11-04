CXX ?= c++
CXXFLAGS ?= -std=c++20 -O2 -Wall -Wextra -Wpedantic

SOURCES := main.cpp checker.cpp
TARGET := build/w2d_checker

.PHONY: all clean test
all: $(TARGET)

$(TARGET): $(SOURCES) checker.hpp
	@mkdir -p build
	$(CXX) $(CXXFLAGS) $(SOURCES) -o $@

test: $(TARGET)
	python3 tests/test_checker.py

clean:
	python3 -c 'from pathlib import Path; import shutil; shutil.rmtree("build", ignore_errors=True)'
