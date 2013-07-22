scalrr
======

resolution reduction code.
This runs as a web app powered by Python using Flask. It currently
doesn't run on the web, I'm working on that.

***How to run scalrr***
scalrr consists of 2 python scripts:
scalrr_front.py
scalrr_back.py

They are meant to be run the front and back-ends, respectively.
Both need to be running at the same time for scalrr to function.
To run them, simply run "python scalrr_front.py" or
"python scalrr_back.py" on the command line. sclarr_back.py is meant
to be run on the machine hosting the database (modis in our case).
However, scalrr_back.py should be able to access remote databases
with minimal modification (just changing the database access
information in scalrr_back.py).

There are some necessary python libraries for scalrr_front.py
and scalrr_back.py:

scalrr_front.py:
	
	-------VIRTUAL ENVIROMENT METHOD----------
    python 2.7
    	wget http://www.python.org/ftp/python/2.7.2/Python-2.7.2.tgz
    	./configure --prefix /projects/db8/matt/python2.7 --enable-shared
    	make
    	make install
	virtualenv
		wget https://raw.github.com/pypa/virtualenv/master/virtualenv.py
		/path/to/python virtualenv.py --no-site-packages scalrr
		. scalrr/bin/activate
		
		pip install numpy matplotlib simplejson flask 
		
		deactivate
		
		
pip install pil

	apache http 2.4
		/projects/db8/build/
		/projects/db8/conf/httpd.conf
		
	
	
	
	
	setuptools
		wget http://pypi.python.org/packages/2.7/s/setuptools/setuptools-0.6c11-py2.7.egg#md5=fe1f997bc722265116870bc7919059ea
		ln -s /path/to/python2.7 python2.7
		PATH=.:$PATH sh setuptools-0.6c11-py2.7.egg --prefix=/projects/db8/matt/
		rm python2.7
    numpy 1.4 or later
    	wget http://sourceforge.net/projects/numpy/files/NumPy/1.6.2/numpy-1.6.2.tar.gz/download
	libpng
		wget http://prdownloads.sourceforge.net/libpng/libpng-1.5.13.tar.gz?download
	freetype
		wget http://sourceforge.net/projects/freetype/files/freetype2/2.4.11/freetype-2.4.11.tar.gz/download
		./configure --prefex /projects/db8/matt/
    	make
    	make install
    matplotlib 1.2.0 
        wget https://github.com/downloads/matplotlib/matplotlib/matplotlib-1.2.0.tar.gz
    simplejson
    	wget http://pypi.python.org/packages/source/s/simplejson/simplejson-3.0.4.tar.gz
    	/path/to/python/python2.7 setup.py install
	flask
		wget http://pypi.python.org/packages/source/F/Flask/Flask-0.9.tar.gz
		/path/to/python/python2.7 setup.py install
    	
    PIL 
        http://www.pythonware.com/products/pil/
        Installing - python setup.py install
    
    basemap 
        http://matplotlib.org/basemap/
        Installing - http://matplotlib.org/basemap/users/installing.html
        
    GEOS (Geometry Engine - Open Source) library 3.1.1 or later (comes with basemap)
        see basemap install
    PROJ4 Cartographic Projections Library. (comes with basemap)
        see basemap install

    
scalrr_back.py:scidbapi (installed by general SciDB installation),
    simplejson

You can install these libraries globally on your machine, or you can
use virtualenv to install them in a virtual environment.

I recommend installing pip for easy installation of python libraries.
You can typically do "sudo pip install [python library]" and pip will
do the rest.

***How to interact with scalrr locally***
After getting scalrr_front.py and scalrr_back.py running, go to
"http://localhost:5000/index2.html" in your web browser
of choice (I did almost all the development using only firefox, so I
would recommend using that for best results).

NOTE: scalrr works fine when being accessed by separate browsers.
However, if you have 2 windows/tabs running scalrr within the same
browser, scalrr will break. Flask sessions are maintained per browser
(same cookie is used for the windows/tabs)

***How to make changes to scalrr and test***
Just stop whichever part of the system you are modifying (backend
or frontend, ctrl-c on the command line is fine). Make your changes,
and then re-start that part of the system. scalrr_front.py and
scalrr_back.py run independently of each other so stopping both of
them is not necessary. However, if they are communicating when you
kill one of them, you could potentially crash the other (I haven't
put in code to catch exceptions yet).
