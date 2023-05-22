from setuptools import setup

setup(name='rctools',
      version='1.6.4',
      description='Common ReadiCharge python function',
      url='https://thenewfoundry.com',
      author='NewFoundry',
      author_email='company@thenewfoundry.com',
      license='Proprietary. All Rights Reserved',
      packages=['rctools', 'rctools.alerts', 'rctools.aws', 'rctools.models'],
      install_requires=[
        'boto3',
        'mergedeep',
        'requests',
        'pydantic',
        'pyjwt'
      ],
      exclude=['tests'],
      zip_safe=True)
