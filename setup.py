import setuptools

with open('README.md', 'r', encoding='utf-8') as fh:
    long_description = fh.read()

setuptools.setup(
    name='pytdjson',
    version='0.1.0',
    author='Appuxif',
    author_email='app@mail.com',
    description='A Python package to build Telegram clients using TDLib',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/Appuxif/pytdjson',
    project_urls={
        'Bug Tracker': 'https://github.com/Appuxif/pytdjson/issues',
    },
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    package_dir={'': '.'},
    # packages=setuptools.find_packages(where='.'),
    packages=['telegram', 'telegram.types'],
    package_data={'telegram': ['lib/linux/*']},
    python_requires='>=3.6',
)
