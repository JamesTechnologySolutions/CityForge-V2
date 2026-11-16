cmake_minimum_required(VERSION 3.15)
project(cityforge_core CXX)

find_package(pybind11 REQUIRED)

pybind11_add_module(
    cityforge_core
    src/cityforge_core.cpp
)
