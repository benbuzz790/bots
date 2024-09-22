from setuptools import setup, find_packages
import os

# Read the long description from README.md
with open(os.path.join(os.path.dirname(__file__), 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='bots',
    version='0.1',
    author='Ben Rinauto',
    author_email='ben.rinauto@gmail.com',
    description='A framework for LLM tool use',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/benbuzz790/bots',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    packages=find_packages(),  # Automatically find all packages including 'bots' and its sub-packages
    install_requires=[
        'anthropic',
        'openai',
        'astor',
        'typing_extensions',
    ],
    extras_require={
        'dev': ['pytest'],
    },
    python_requires='>=3.6',  # Specify Python version compatibility
)
