py -3.3-32 setup.py build -f
py -3.3 setup.py build -f
py -3.4-32 setup.py build -f
py -3.4 setup.py build -f
rd /s/q dist
py -3.4 setup.py bdist_egg
py -3.4 setup.py bdist_wininst