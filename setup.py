from setuptools import setup, find_packages

setup(
    name='bots',
    version='0.1',
    author='Ben Rinauto',
    author_email='ben.rinauto@gmail.com',
    description='A framework for llm tool use',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/benbuzz790/bots',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    package_dir={'': 'bots'},  # Adjust this to point to the new 'bots' directory
    packages=find_packages(where='bots'),  # Automatically find packages in 'bots'
    install_requires=[
        'anthropic',
        'openai',
        'astor',
        'typing_extensions',
    ],
    extras_require={
        'dev': ['pytest'],
    },
)
