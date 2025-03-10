import os
from setuptools import setup, Extension
from Cython.Build import cythonize

py_files = [f for f in os.listdir('.') if f.endswith('.py') and f != 'setup.py']

if py_files:
    extensions = [
        Extension(
            os.path.splitext(source)[0],  
            sources=[source],             
            language='c',                 
        )
        for source in py_files
    ]

    setup(
        name='lab_submission',
        ext_modules=cythonize(
            extensions,
            compiler_directives={
                'language_level': '3',     
                'embedsignature': True,    # 保留函数签名
            }
        ),
        options={
            'build_ext': {
                'inplace': True,
                'force': True,
            }
        }
    )
else:
    print("没有找到需要编译的 Python 文件")