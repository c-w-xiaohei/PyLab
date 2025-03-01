import os
from setuptools import setup
from Cython.Build import cythonize

py_files = [f for f in os.listdir('.') if f.endswith('.py') and f != 'setup.py']

if py_files:
    setup(
        ext_modules = cythonize(py_files)
    )
else:
    print("没有找到需要编译的 Python 文件")