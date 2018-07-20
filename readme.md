# Setting up Django and your web server with uWSGI and nginx
This is a quick guide to build a web server with Nginx uWSGI Django on Ubuntu 16.04.XX using this [uWSGI tutorial](https://uwsgi.readthedocs.io/en/latest/tutorials/Django_and_nginx.html#basic-nginx).

The concept of the web server is that several parts need to talk to each other to make it work. The stack of components looks like this:
```
the web client <-> the web server (nginx) <-> the socket <-> uwsgi <-> Django
```
The web client is the web browser, web server is Nginx, socket allows for communication between browser and server, uwsgi (universal web server gateway interface) provides connection to Django, and Django is a Python language framework.

## Ubuntu 
These terminal instructions below are for Linux Ubuntu distribution version 16.04.XX. Commands include if you are logging remotely with ssh and setting up a virtual environment to make sure you are using a development server that fulfills the installation version requirements for this web server to work.
```
$ ssh gitai-hub@192.168.99.63 (or your own IP)
$ cd ~
~$ sudo apt-get update
~$ sudo apt-get install python-dev
~$ sudo apt-get install python-pip
~$ virtualenv webserver
~$ cd webserver
~/webserver $ pip install virtualenv
~/webserver $ source bin/activate
```
Now in virtual environment, install the project.
```
(webserver)~/webserver $ django-admin.py startproject mysite
(webserver)~/webserver $ mv /home/gitai-hub/webserver/mysite /home/gitai-hub/webserver/workspace
```
If you have an existing project, add this line in terminal:
```
(webserver)~/webserver $ pip install -r requirements.txt && cd workspace
```
In ~/webserver/workspace/mysite/settings.py, add allowed hosts and convert database from SQLite to MySQL MariaDB with these edits.
```
ALLOWED_HOSTS = ['192.168.99.63'(your IP), 'localhost']

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'mysite',
        'USER': 'mysiteuser',
        'PASSWORD': 'password',
        'HOST': 'localhost',
        'PORT': '',
    }
}
```
## UWSGI (Universal Web Server Gateway Interface)
uwsgi connects Python to the web client.
```
the web client <-> uWSGI <-> Python
```

Create a file called test.py in workspace folder.
```
# test.py
def application(env, start_response):
    start_response('200 OK', [('Content-Type','text/html')])
    return [b"Hello World"] # python3
    #return ["Hello World"] # python2
```
Run in terminal:
```
(webserver)~/webserver/workspace $ uwsgi --http :8000 --wsgi-file test.py
```
In your browser, go to localhost:8000 or public ip:8000 and if test is successful, it'll load the text from the test.py file.


## Django
Django is a Python framework. Now test uwsgi with it.
```
the web client <-> uWSGI <-> Django
```
Now in terminal, type:
```
(webserver)~/webserver/workspace $ pip install django && pip install mysqlclient
(webserver)~/webserver/workspace $ python manage.py runserver 0.0.0.0:8000
```

You will then see Django is installed with a rocket ship on localhost:8000 and public ip:8000 if test is successful.

Now normally we won’t have the browser speaking directly to uWSGI. That’s a job for the webserver (nginx), which will act as a go-between.

## NGINX
nginx is a web server between browser and uwsgi.
```
web client <-> web server
```
In terminal, type:
```
(webserver)~/webserver/workspace $ sudo apt-get install nginx
(webserver)~/webserver/workspace $ sudo /etc/init.d/nginx start
```
Now, go to localhost:80 or just localhost, you will see a "Welcome to nginx!" page.

### Configure nginx for your site
You will need the ```uwsgi_params``` file, which is available in the nginx directory of the uWSGI distribution, or from https://github.com/nginx/nginx/blob/master/conf/uwsgi_params

Copy it into your project directory.

Now create a file called mysite_nginx.conf, and put this in it:

```
# mysite_nginx.conf

# the upstream component nginx needs to connect to
upstream django {
    server unix:///home/gitai-hub/webserver/workspace/mysite.sock; # for a file socket
    # server 127.0.0.1:7000; # for a web port socket (we'll use this first)
}

# configuration of the server
server {
    # the port your site will be served on
    listen      8000;
    # the domain name it will serve for
    server_name 192.168.99.63; # substitute your machine's IP address or FQDN
    charset     utf-8;

    # max upload size
    client_max_body_size 75M;   # adjust to taste

    # Django media
    location /media  {
        autoindex on;
        alias /home/gitai-hub/webserver/workspace/media/;  # your Django project's media files - amend as required
    }

    location /static {
        autoindex on;
        alias /home/gitai-hub/webserver/workspace/static; # your Django project's static files - amend as required
    }

    # Finally, send all non-media requests to the Django server.
    location / {
        uwsgi_pass  django;
        include     /home/gitai-hub/webserver/workspace/uwsgi_params; # the uwsgi_params file you installed
    }
}
```
This conf file tells nginx to serve up media and static files from the filesystem, as well as handle requests that require Django’s intervention.

Symlink to this file from /etc/nginx/sites-enabled so nginx can see it:
```
sudo ln -s ~/home/gitai-hub/webserver/workspace/mysite_nginx.conf /etc/nginx/sites-enabled/
```
### Deploying static files
Before running nginx, you have to collect all Django static files in the static folder. First of all you have to edit mysite/settings.py adding:
```
STATIC_ROOT = os.path.join(BASE_DIR, "static/")
```
Now run in terminal:
```
(webserver)~/webserver/workspace $ python manage.py collectstatic
```
You will have a static folder for with admin assets now.

Restart nginx now.
```
(webserver)~/webserver/workspace $ sudo /etc/init.d/nginx restart
```

## nginx, uwsgi, and test.py
Now let's connect nginx, uwsgi, and test.py, in terminal type:
```
(webserver)~/webserver/workspace $ uwsgi --socket mysite.sock --wsgi-file test.py --chmod-socket=666 # (very permissive)
```

## UWSGI (Universal Web Server Gateway Interface)
Since Django project works inside virtual environment, we will now have UWSGI serve on the web instead a lightweight development server. We will get out of the virtual environment to do that.
```
(webserver)~/webserver $ deactivate
```
Now run these commands to test if Django works on the web.
```
our-project/hello $ sudo pip install uwsgi
our-project/hello $ uwsgi --http :8000 --home /home/gitai-hub/our-project/venv --chdir /home/gitai-hub/our-project/hello -w hello.wsgi
```
Go to localhost:8000 and your public ip:8000 to see if the Django installation is successful.

Now to save these settings in an initial configuration, we create a .ini file and then launch it.
```
our-project/hello $ sudo mkdir /etc/uwsgi/sites
our-project/hello $ sudo vim /etc/uwsgi/sites/hello.ini

OR 

our-project/hello $ sudo nano /etc/uwsgi/sites/hello.ini

OR 

our-project/hello $ sudo xdg-open /etc/uwsgi/sites/hello.ini
```
The hello.ini contents are:
```
[uwsgi]
 
chdir = /home/gitai-hub/our-project/hello #same as above
home = /home/gitai-hub/our-project/venv #same as above
module = hello.wsgi:application #same as above
 
master = true
processes = 5 #more processes, more computing power
 
socket = /run/uwsgi/hello.sock #SOCKET_LOC
chown-socket = ubuntu:www-data #user and user's group
chmod-socket = 660
vacuum = true #delete the socket after process ends
harakiri = 30 #respawn the process if it takes more than 30 secs
```
Test if this works with command:
```
our-project/hello $ uwsgi --ini /etc/uwsgi/sites/hello.ini
```
If this works fine, you’ll see a couple of lines and status that 5 or some number of processes have been spawned.


GROUP
You may also have to add your user to nginx’s group (which is probably www-data), or vice-versa, so that nginx can read and write to your socket properly.
To do that, go to:
```
$ cd /etc/nginx/
/etc/nginx $ sudo xdg-open nginx.conf
```
In the file, at top of it, add this line for gitai-hub:
```
user www-data;
```


# FAQ
Question 1: I get this error when launching uwsgi socket:
```
$ uwsgi --socket :8001 --wsgi-file test.py 

invalid request block size: 21573 (max 4096)...skip
```
 
Answer 1: Adjust the parameters with this command:
```
uwsgi --socket :8052 --wsgi-file demo_wsgi.py --protocol=http
```


Question 2: I get error of disallowed hosts when launching uwsgi.

 
Answer 2: Add "localhost" and your public ip in the "ALLOWED_HOSTS" in hello/hello/settings.py

Question 3: I get error of when launching uwsgi .ini file.
```
~/our-project/hello$ uwsgi --ini hello.ini

Fatal Python error: Py_Initialize: Unable to get the locale encoding
ModuleNotFoundError: No module named 'encodings'

```

 
Answer 3: For Python-3 try removing virtual environment files. And resetting it up.

```
rm -rf venv
virtualenv -p /usr/bin/python3 venv/
source venv/bin/activate
pip install -r requirements.txt
```

Question 4: When I launch Nginx, it has error of "Bad Gateway".

Answer 4: Start uWSGI first then uWSGI.


# References
- [uWSGI Official Tutorial](https://uwsgi.readthedocs.io/en/latest/tutorials/Django_and_nginx.html#basic-nginx)
- [Monik Quickstart with Ubuntu 16.04.XX](http://monik.in/a-quick-guide-to-getting-a-django-uwsgi-nginx-server-up-on-ubuntu-16-04-aws-ec2/)
- [Error: Uwsgi invalid request block size](https://stackoverflow.com/questions/15878176/uwsgi-invalid-request-block-size)
- [Error: No module 'encodings'](https://stackoverflow.com/questions/38132755/importerror-no-module-named-encodings)