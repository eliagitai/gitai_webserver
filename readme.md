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
$ ssh gitai-hub@192.168.99.63 (or your own IP or git clone)
$ cd ~
~$ sudo apt-get update
~$ sudo apt-get install python-pip
~$ sudo apt-get install python-dev
~$ sudo pip install virtualenv
~$ sudo pip install Django
~$ sudo pip install mysqlclient
~$ virtualenv gitai_webserver
~$ cd gitai_webserver
~/gitai_webserver $ source bin/activate
```
Now in virtual environment, install the project.
```
(gitai_webserver)~/gitai_webserver $ django-admin.py startproject mysite
(gitai_webserver)~/gitai_webserver $ mv /home/gitai-hub/webserver/mysite /home/gitai-hub/gitai_webserver/workspace
```
If you have an existing project, add this line in terminal:
```
(gitai_webserver)~/gitai_webserver $ pip install -r requirements.txt && cd workspace
```
In ~/gitai_webserver/workspace/mysite/settings.py, add allowed hosts and convert database from SQLite to MySQL MariaDB with these edits.
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
(gitai_webserver)~/gitai_webserver/workspace $ uwsgi --http :8000 --wsgi-file test.py
```
In your browser, go to localhost:8000 or public ip:8000 and if test is successful, it'll load the text from the test.py file.


## Django
Django is a Python framework. Now test uwsgi with it.
```
the web client <-> uWSGI <-> Django
```
Now in terminal, type:
```
(gitai_webserver)~/gitai_webserver/workspace $ pip install django && pip install mysqlclient
(gitai_webserver)~/gitai_webserver/workspace $ python manage.py runserver 0.0.0.0:8000
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
(gitai_webserver)~/gitai_webserver/workspace $ sudo apt-get install nginx
(gitai_webserver)~/gitai_webserver/workspace $ sudo /etc/init.d/nginx start
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
    server unix:///home/gitai-hub/gitai_webserver/workspace/mysite.sock; # for a file socket
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
        alias /home/gitai-hub/gitai_webserver/workspace/media/;  # your Django project's media files - amend as required
    }

    location /static {
        autoindex on;
        alias /home/gitai-hub/gitai_webserver/workspace/static; # your Django project's static files - amend as required
    }

    # Finally, send all non-media requests to the Django server.
    location / {
        uwsgi_pass  django;
        include     /home/gitai-hub/gitai_webserver/workspace/uwsgi_params; # the uwsgi_params file you installed
    }
}
```
This conf file tells nginx to serve up media and static files from the filesystem, as well as handle requests that require Django’s intervention.

Symlink to this file from /etc/nginx/sites-enabled so nginx can see it:
```
sudo ln -s ~/home/gitai-hub/gitai_webserver/workspace/mysite_nginx.conf /etc/nginx/sites-enabled/
```
### Deploying static files
Before running nginx, you have to collect all Django static files in the static folder. First of all you have to edit mysite/settings.py adding:
```
STATIC_ROOT = os.path.join(BASE_DIR, "static/")
```
Now run in terminal:
```
(gitai_webserver)~/gitai_webserver/workspace $ python manage.py collectstatic
```
You will have a static folder for with admin assets now.

Restart nginx now.
```
(gitai_webserver)~/gitai_webserver/workspace $ sudo /etc/init.d/nginx restart
```
You can run command below and test if admin and media files are uploaded as well.
```
(gitai_webserver)~/gitai_webserver/workspace $ uwsgi --http :8000 --module mysite.wsgi
```
Visit localhost:8000/admin and localhost:8000/media to see if those are working correctly.

## nginx, uwsgi, and test.py
Now let's connect nginx, uwsgi, and test.py, in terminal type:
```
(gitai_webserver)~/gitai_webserver/workspace $ uwsgi --socket mysite.sock --wsgi-file test.py --chmod-socket=666
```
In another terminal, restart nginx with command:
```
$ sudo /etc/init.d/nginx restart
```
Now check localhost to see the Nginx page is working. Then go to localhost:8000 or ip:8000 to see if it loads the text in text.py file.

Repeat process for loading Django app, make sure you restart nginx after running the command below too.

```
~/gitai_webserver/workspace $ uwsgi --socket mysite.sock --module mysite.wsgi --chmod-socket=666
```

## Install uWSGI system wide
Since Django project works inside virtual environment, we will now have UWSGI serve on the web instead a lightweight development server. We will get out of the virtual environment to do that.
```
(gitai_webserver)~/gitai_webserver $ deactivate
```
Now run these commands to test if Django works on the web using socket.
```
gitai_webserver/workspace $ sudo pip install uwsgi
gitai_webserver/workspace $ uwsgi --socket mysite.sock --module mysite.wsgi --chmod-socket=666
```
Go to localhost:8000 and your public ip:8000 to see if the Django installation is successful.

Now to save these settings in an initial configuration, we create a .ini file and then launch it.
```
gitai_webserver/workspace $ sudo touch mysite.ini
gitai_webserver/workspace $ sudo vim mysite.ini

OR 

gitai_webserver/workspace $ sudo nano /etc/uwsgi/sites/hello.ini

OR 
gitai_webserver/workspace $ sudo xdg-open /etc/uwsgi/sites/hello.ini
```
The mysite.ini contents are:
```
[uwsgi]
# if using this, uncomment in mysite_nginx.conf, the upstream django server unix socket line
socket          = /home/gitai-hub/gitai_webserver/workspace/mysite.sock 
# if using this, uncomment in mysite_nginx.conf, the upstream django server port line
# socket = 127.0.0.1:7000 

workers         = 3
master          = true
chmod-socket    = 666
module          = mysite.wsgi
chdir           = /home/gitai-hub/gitai_webserver/workspace

```
Test if this works with command:
```
gitai_webserver/workspace $ uwsgi --ini mysite.ini
```
If this works fine, you'll be open up browser localhost:8000 or ip:8000 and see the Django app loaded on there.

## Emperor Mode
uWSGI can run in ‘emperor’ mode. where a watch is setup on directory of uWSGI config files. It will spawn instances (‘vassals’) for each one it finds.

Whenever a config file is changed, the emperor will automatically restart the vassal.
```
# create a directory for the vassals
sudo mkdir /etc/uwsgi
sudo mkdir /etc/uwsgi/vassals
# symlink from the default config directory to your config file
sudo ln -s /home/gitai-hub/gitai_webserver/workspace/mysite.ini /etc/uwsgi/vassals/
# run the emperor
sudo uwsgi --emperor /etc/uwsgi/vassals --uid www-data --gid www-data
```
You can then go to localhost:8000 and view the Django app normally if it is successful.

## Make uWSGI startup when the system boots
The last step is to make it all happen automatically at system startup time.

One way to do that is to add line below to rc.local file before the line “exit 0”.

```
/usr/local/bin/uwsgi --emperor /etc/uwsgi/vassals --uid www-data --gid www-data --daemonize /var/log/uwsgi-emperor.log
```

## Deploying Flask
Flask is a popular Python web microframework.

Save the following example as myflaskapp.py:

```
from flask import Flask

app = Flask(__name__)

@app.route('/')
def index():
    return "<span style='color:red'>I am app 1</span>"
```


### GROUP
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

## Summary Terminal Commands
nginx test
```
$ sudo /etc/init.d/nginx restart
```

django test
```
~/gitai_webserver/workspace $ python manage.py runserver 0.0.0.0:8000
```

port tests
```
# test.py
~/gitai_webserver/workspace $ uwsgi --http :8000 --wsgi-file test.py

# Django app test
~/gitai_webserver/workspace $ uwsgi --http :8000 --module mysite.wsgi
```

socket tests
```
# test.py with socket port 8000
uwsgi --socket :7000 --wsgi-file test.py

# test.py with mysite.sock
~/gitai_webserver/workspace $ uwsgi --socket mysite.sock --wsgi-file test.py --chmod-socket=666

# Django app
~/gitai_webserver/workspace $ uwsgi --socket mysite.sock --module mysite.wsgi --chmod-socket=666

# Django app with stats
~/gitai_webserver/workspace $ uwsgi --socket :7000 --stats :9000 --module mysite.wsgi --master --processes 8 --chmod-socket=666

# then in another terminal, run this:
$ uwsgi --connect-and-read 127.0.0.1:9000
```
flask test
```
~/gitai_webserver/workspace $ uwsgi --socket mysite.sock --wsgi-file myflaskapp.py --callable app --processes 4 --threads 2
```

# FAQ
Question 1: 
 - I get this error when launching uwsgi socket:
```
$ uwsgi --socket :7000 --wsgi-file test.py 

invalid request block size: 21573 (max 4096)...skip
```
 
Answer 1: 
 - Adjust the parameters with this command:
```
uwsgi --socket :8000 --wsgi-file test.py --protocol=http
```
 - Or listen to the server port 8000 from mysite_nginx.conf on your browser as localhost:8000 instead of port 7000 shown below:
```
server {
    # the port your site will be served on
    listen      8000;
    .
    .
    .
}
```

Question 2: 
 - I get error of disallowed hosts when launching uwsgi.

 
Answer 2: 
 - Add "localhost" and your public ip in the "ALLOWED_HOSTS" in hello/hello/settings.py

Question 3: 
 - I get error of when launching uwsgi .ini file.
```
~/our-project/hello$ uwsgi --ini hello.ini

Fatal Python error: Py_Initialize: Unable to get the locale encoding
ModuleNotFoundError: No module named 'encodings'
```

 
Answer 3: 
 - Make sure the path names are correct for socket and chdir shown below:
 

```
socket = /home/gitai-hub/gitai_webserver/workspace/mysite.sock 

chdir = /home/gitai-hub/gitai_webserver/workspace
```

Question 4: 
- When I launch Nginx, it has error of "Bad Gateway".

Answer 4: 
- Remove mysite.sock file in workspace folder. Start uWSGI first then NGINX. If error persists, check error log at folder with command where -f tag shows real time errors: 
```
/var/log/nginx $ tail -f error.log
```
- Make sure you have the mysite_nginx.conf upstream django desingation correct for the command you are running below:
```
In terminal
 $ uwsgi --socket mysite.sock --module mysite.wsgi --chmod-socket=666

mysite_nginx.conf file
upstream django {
  server unix:///home/gitai-hub/gitai_webserver/workspace/mysite.sock; # for a file socket
}
 ```
- Other things to try is to remove the virtual environment pip install Django, pip install mysqlclient.

Question 5: 
- When I launch uWSGI and restart NGINX, it has error of "Connection Refused" at localhost:8000 or ip:8000.

Answer 5: 
- Check symbolic link in the folder /etc/nginx/sites-enabled/ and recreate connection (may have to delete old file there) with command:
```
sudo ln -s ~/path/to/your/mysite/mysite_nginx.conf /etc/nginx/sites-enabled/
```

Question 6: 
- I get error that port is already in use.

Answer 6: 
- Run this command for that port 8000.
```
$ sudo fuser -k 8000/tcp
```
- Then check your mysite_nginx.conf file and then if test if you run sockeet or port commands. If you run port, then make sure this field is uncommented:

```
upstream django {
    server 127.0.0.1:7000; # for a web port socket (we'll use this first)
}

```
- If you are testing with socket, then uncomment this line:
```
upstream django {
    server unix:///home/gitai-hub/gitai_webserver/workspace/mysite.sock;
}
 
```
Question 7: 
- I get a failed start error when I start Nginx below:
```
$ sudo /etc/init.d/nginx restart

[....] Restarting nginx (via systemctl): nginx.serviceJob for nginx.service failed because the control process exited with error code. See "systemctl status nginx.service" and "journalctl -xe" for details.
 failed!
```
Answer 7: 
- Make sure another terminal running a server isn't running. Close that terminal/port.




# References
- [uWSGI Official Tutorial](https://uwsgi.readthedocs.io/en/latest/tutorials/Django_and_nginx.html#basic-nginx)
- [Monik Quickstart with Ubuntu 16.04.XX](http://monik.in/a-quick-guide-to-getting-a-django-uwsgi-nginx-server-up-on-ubuntu-16-04-aws-ec2/)
- [Error: Uwsgi invalid request block size](https://stackoverflow.com/questions/15878176/uwsgi-invalid-request-block-size)
- [Error: No module 'encodings'](https://stackoverflow.com/questions/16272542/uwsgi-fails-with-no-module-named-encoding-error)