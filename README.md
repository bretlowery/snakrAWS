# snakrAWS
Custom short URL generator + usage analytics, ported from my original Snakr Google Cloud/Python 2/Django 1.6 repo to AWS/Postgres RDS/Python 3.6+/Django 2.1+

## Background 
URL shorteners are used to generate a smaller “abbreviated” version of a URL so that the smaller URL can be used as an alias in place of the longer URL. Subsequent calls to the smaller URL will redirect to the same resource originally identified by the longer URL, including all querystring parameters and other valid URL components. This is useful for several reasons:

Upside                                          | Reason
----------------------------------------------- | ------------------------------
Easier to use (“beautification”)               | It can be substantially easier to enter, copy, paste, manipulate, remember, or otherwise use a shorter URL rather than its longer version. Smaller is inherently “more beautiful” than longer.
Less prone to breakage                          | Longer URLs can be broken when embedded in documents, messages, etc. due to misentry, mispaste, line wrapping breakages, or cutoffs due to data length limitations in standards and tools like SMS or Twitter. Shorter URLs are less prone to these problems.
Less bandwidth used                             | Shorter URLs require less transmission sources that longer ones, a problem that increasingly manifests itself at scale.
Less storage used                               | If the URLs are stored, the shorter URL will use less space.

There are downsides to URL shorteners:

Downside                                                | Reason
------------------------------------------------------- | ------------------------------
Short URL as fraud enabler                              | Shorteners have been used to obfuscate the origin of traffic, beat blacklists, track user engagement activity surreptitiously, etc. Shortener services identified as trafficking in a lot of this can find themselves blacklisted, to the detriment of the service’s users and thus the service itself.
Short URLs can hide payload malfeasance in the long URL | URLs may contain payloads such as SQL injection, etc. in the query string or other components. A shortener that encodes and scrubs the URL first for safety can return a short URL that itself is guaranteed not to contain such issues (since it is generated), but return them to the caller when resolved to the long URL.
Negative effects on SEO, CTR, etc.                      | Shortened URLs may not rank as high or at all in search engine results versus their longer URL parents. This could pose problems is use cases where SEO matters. The same is true when short URLs are delivered via ads or links exposed to end users who may not recognize them and thus be less likely to clickthru, thereby affecting monetization, traffic, campaign optimization, future campaign targeting accuracy, etc.

## Features Provided 

1.	URLs can be shortened using either a form, or via a REST API. POST is used to turn a long URL into a shortened URL. A subsequent GET is used to redirect the shortened URL to its long URL target.
2.	URLs are cleansed and validate before shortening. Only valid URLs are recongnized. SSL/TLS is honored on both ends. HTTP long URLs create HTTP short URLs, while HTTPS long URLs create HTTPS short URLs. Ditto FTP and SFTP.
3. Per RFC 3986, schemas and domains/hosts/netlocs are treated as case-insensitive, while the rest of the URL is treated as case-sensitive. For example, three URLs identical in all aspects other than the schemas“http”, “hTtP”, and “HTTP” are all treated as identical and generate identical short URLs for the same.
4. The Python 3 design uses Unicode and i18n so global character sets and alternative languages are supported. L10n is supported but untested.
5. Duplicate long URLs submitted to the shortening service will generate only one short URL on the first call. Subsequent calls with the same long URL return the existing short URL.
6.	Short URL paths are generated from a random selection of URL-safe characters (A-Z, a-z-, and 0-9, although the exact set of characters used can be modified via a metadata change). 
7.	The number of characters used in shorturls defaults to 6; this is also modifiable up to 12 via a metadata change. "Vanity" custom short urls are allowed of 3 characters or more.
8.	Easily-confused character combinations are excluded. No short URLs are generated which contain both:
- A “0” (zero) and an “O” (uppercase letter ‘oh’), and/or;
- A “1” (one) and a “l” (lowercase letter ‘ell’).
9. SnakrAWS uses a FNV1a hashing implementation for performance. Both long and short URLs of any length are each hashed to 64bit FNV1a keys used for lookup and comparison purposes. If a collision is detected (a 2nd long url hash to the same short URL (1 in 1.886 billion odds, if FNV1A meets its assumed theorized collision resistance, etc.), the short URL is regenerated. This repeats until a unique short URL is generated. The number of max retries is set in the metadata as well, and defaults to 3. 
10. Increasing the size of the short URL generated by one in the MAXSIZE parameter in the metadata greatly increases the number of possible combinations at the expense of a short URL one character longer. If MAXSIZE is increased, old URLs using the smaller size still work, and you can even flip back to the old size later and both sizes will still resolve.
11.  Very basic bot and crawler blocking is available. A blacklist of known bot user agent strings is provided. Any request coming from a user agent containing one of the strings in the blacklist will be 403d. I *strongly* recommend you add something at the nginx, load balancer, or firewall layer to protect your Snakr site from abuse. There are good open source solutions for free, or you can use AWS's offerings, or whatever, but use something.

### Prerequisites for Installation
- An AWS account
- An AWS EC2 Ubuntu t2_micro or better instance up and running with the associated key pair (SnakrAWS has only been tested with Ubuntu)
- A RDS Postgres 10.6+ database up and running
- An AWS Security Group set up so that the instance and database can communicate with each other
- SSH shell access to your instance
- Google reCAPTCHA v3 public and private keys

### Installation

1. SSH to your instance as the ubuntu user;
2. Install the basic packages needed. This is an exercise left to the reader:
- Git
- Nginx
- Postgres 10.6+ client
- OpenSSL
- Python 3.7+
- Django 2.1+
3. Clone the repo:
```
$ sudo mkdir /var/www
$ sudo chown ubuntu:ubuntu /var/www
$ cd /var/www
$ git clone https://github.com/bretlowery/snakrAWS.git snakraws && cd snakraws
```
4. Create your inital SnakrAWS database in your RDS instance and load the tables with initial data. Use the PSQL command or your favorite SQL UI. These are example commands but may differ depending on your security setup:
```
$ psql -U postgres -d postgres -H your.aws.rds.host -P portnumber
> CREATE DATABASE snakraws;
> CREATE USER snakraws WITH PASSWORD 'your-really-strong-password-here';
> GRANT ALL ON DATABASE snakraws TO snakraws;
$ psql -U snakraws -d snakraws -H your.aws.rds.host -P portnumber -a -f install_snakraws.sql
Password: your-really-strong-password-here
```
5. Update local_settings.py and add your custom settings, after making a backup copy of it. Refer to the Settings section below if needed:
```
$ cp snakraws/local_settings.py local_settings.original.py
$ vim snakraws/local_settings.py
```
6. Create your Python 3.7 virtualenv and update pip first thing:
```
$ virtualenv venv -p python3
$ source venv/bin/activate
(venv) $ pip install -U pip
```
7. Install the prerequisite Python packages that SnakrAWS needs:
```
(venv) $ pip install -r requirements.txt
```
8. Install the Spacy english library:
```
(venv) $ python -m spacy download en
```
9. Install the Django admin tables and initial data, then deactivate your virtualenv:
```
(venv) $ ./manage.py migrate
(venv) $ deactivate
```
10. Configure and start nginx. Here is a basic conf script that you can modify. See the nginx docs online for more details, or for more examples see:
https://www.digitalocean.com/community/tutorials/how-to-serve-django-applications-with-uwsgi-and-nginx-on-ubuntu-16-04
```
sudo vim /etc/nginx/conf.d/your.snakraws.com-net-gov-whatever.conf
```
Conf file:
```
server {
    listen             80;
    server_tokens      off;
    server_name        your.snakraws.com-net-gov-whatever;
    return             301 http://your.snakraws.com-net-gov-whatever$request_uri;
}

server {
    listen                   80;
    server_name              snakraws.com-net-gov-whatever;
    client_max_body_size     10M;
    access_log               /var/log/your.snakraws.com-net-gov-whatever.access.log;
    error_log                /var/log/your.snakraws.com-net-gov-whatever.error.log;
   
    # -------------
    # Handle Django
    # -------------
    location / {
        proxy_pass       http://localhost:8081;
        proxy_set_header Upgrade            $http_upgrade;
        proxy_set_header Connection         "upgrade";
        proxy_set_header Host               $host;
        proxy_set_header X-Real-IP          $remote_addr;
        proxy_set_header X-Forwarded-For    $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto  $scheme;
    }
    
    # ------------------
    # serve static files
    # ------------------

    location /static/ {
        alias   /var/www/django/static/;
    }
    
    # -----------
    # Enable GZIP
    # -----------
    gzip               on;
    gzip_disable       "msie6";                                            
    gzip_vary          on;                                                     
    gzip_types         text/plain
                       text/css
                       application/json
                       application/javascript
                       application/x-javascript
                       text/xml
                       application/xml
                       application/xml+rss
                       text/javascript
                       image/svg+xml;
    gzip_proxied       any;
    gzip_comp_level    6;                                                
    gzip_buffers       16  8k;  
    gzip_http_version  1.0;   
    
    location ~* .(ogg|ogv|svg|svgz|eot|otf|woff|mp4|ttf|css
                  |rss|atom|js|jpg|jpeg|gif|png|ico|zip|tgz
                  |gz|rar|bz2|doc|xls|exe|ppt|tar|mid|midi
                  |wav|bmp|rtf)$ {
        expires max;
        log_not_found off;
        access_log off;
    }    
                                     
}
```
11. Test that conf before you deploy 'cause it's just the right thing to do:
```
$ sudo nginx -t
```
12. If you're Chloraseptic copasetic, start nginx with:
```
$ sudo service nginx start
```
13. Configure and start either uWSGI or gunicorn. Here, I'm using gunicorn. For more examples see:
https://www.digitalocean.com/community/tutorials/how-to-serve-django-applications-with-uwsgi-and-nginx-on-ubuntu-16-04
```
$ sudo mkdir /var/log/your.snakraws.com-net-gov-whatever
$ sudo chown www-data:www-data /var/log/your.snakraws.com-net-gov-whatever
$ sudo vim /etc/systemd/system/your.snakraws.com-net-gov-whatever.service
```
14. Set up your gunicorn conf file:
```
[Unit]
Description=your.snakraws.com-net-gov-whatever
Requires=nginx.service
Wants=nginx.service
After=nginx.service
[Service]
WorkingDirectory=/var/www/django
PIDFile=/var/run/your.snakraws.com-net-gov-whateverv.pid
Type=forking
KillMode=process
#Restart=on-failure
ExecStart=/var/www/django/venv/bin/gunicorn \
          --log-level debug \
          --group www-data \
          --user www-data \
          --timeout 120 \
          --workers 3 \
          --bind=127.0.0.1:8081 \
          --pid=/var/run/your.snakraws.com-net-gov-whatever.pid \ 
          --pythonpath=/var/www/django \
          --error-logfile=/var/log/your.snakraws.com-net-gov-whatever/errors.log \
          --daemon \
         snakraws.wsgi
[Install]
WantedBy=multi-user.target
```
15. Add it to systemctl and start the service:
```
$ sudo systemctl enable your.snakraws.com-net-gov-whatever.service
$ sudo systemctl start your.snakraws.com-net-gov-whatever
```
16. Finally, check the error log. If everything is running, test your site!
```
$ cat /var/log/your.snakraws.com-net-gov-whatever/errors.log
```

### Custom Settings
| Setting | Description |
| --- | --- |
| ADMIN_POSTBACK | The URL path fragment that leads to the Django admin page. Works like the SHORTENING_POSTBACK. |
| AWS_ELASTIC_IP | Your AWS Elastic IP address | 
| BADBOTLIST | List of known bots that are 403d by Snakr. You should really use a front-end solution for this. |
| CANONICAL_MESSAGES | List of messages that can be returned by Snakr. |
| DATABASE_MODE | Separate "dev" or "prod" setting for the db backend. "Dev" should point to a localhost Postgres instance in the DATABASES config; "prod" should point to your AWS RDB Postgres instance. You can set SITE_MODE and DATABASE_MODE to "dev"/"dev", "dev"/"prod", or "prod"/"prod", depending on how you are testing.|
| ENABLE_ANALYTICS | If "True", populates the various dimension and FactEvent tables when short URLs are created and used, including geolocation of the user. If "False", only the ShortURL and LongURL tables are populated and no geolocation occurs. |
| ENABLE_DEEP_PROFANITY_CHECKING | If "True", turns on checking of URLs for profanity (not the target content, just URL.) DEEP uses a blacklist lookup check that is slower than the FAST method, but is more thorough, though still imperfect. |
| ENABLE_FAST_PROFANITY_CHECKING | If "True", turns on checking of URLs for profanity (not the target content, just the URL.) FAST uses a quality score/machine learning check that is quick, but has a higher miss rate than the DEEP method (see below). |
| ENABLE_LONG_URL_PROFANITY_CHECKING | If either of the above settings is "True", AND this setting is "True", it turns on profanity checking for the long URL (not its content, just the URL itself). If either of the above settings is "True", AND this setting is "False", only the generated short URL is checked. |
| GEOLOCATION_API_URL | SnakrAWS uses IPStack (www.ipstack.com) for geolocation lookup of the user if ENABLE_ANALYTICS = "True". This setting holds URL of the API call to make to IPStack to perform geolocation, including the IPStack API key value (get yours at the IPStack site). |
| INDEX_HTML | The "home page" to return if the user browses to SHORTURL_HOST with no additional path. |
| JET_DASHBOARD_POSTBACK | Used by django-jet. Don't alter this. |
| JET_POSTBACK | Used by django-jet. Don't alter this. |
| RECAPTCHA_PRIVATE_KEY | Your Google reCAPTCHA v3 private key |
| RECAPTCHA_PUBLIC_KEY | Your Google reCAPTCHA v3 public key |
| RECAPTCHA_SCORE_THRESHOLD | Specifies the Google reCAPTCHA score below which a user is considered robotic (non-human). Ranges 0.0 = definitely bot to 1.0 = definitely human. OOTB default is 0.5. | 
| SHORTENING_POSTBACK | The URL path fragment that leads to the web page from which you can shorten URLs. For example, if SHORTURL_HOST is set to "my.site" and SHORTENING_POSTBACK is set to "shorten", the UI form from which to shorten URLs will be located at "http://my.site/shorten". (TBD: If SSL_ENABLED = "True", this will be "https://my.site/shorten". THIS FEATURE IS TBD.) |
| SHORTURL_HOST | The custom domain (host) to use for your short URLs. Mine is "bret.guru", generating short URLs that look like  http://bret.guru/aBc43d |
| SHORTURL_PATH_ALPHABET | Specifies the characters allowed in short URLs. These must be URL-safe characters. Defaults to all digits, a-z, and A-Z, except the easily-confused characters "0", "O", "o", "1", and "l". |
| SHORTURL_PATH_SIZE | The size of the short URL path to generate; set it to no less than 5. For example, if set to 6, short URLs will look like "http://my.site/a6yEw4" or "http://my.site/9ueRTT". Does not affect the size of custom "vanity" URLs if the vanity path is supplied on the short URL form; any vanity size can be used up to 40 characters. Changing this value does not affect short URLs already generated; they can continue to be used and will work as-is. You can make this value bigger or smaller anytime you want. |
| SITE_MODE | "dev" or "prod". When set to "dev", sets SHORTURL_HOST to "localhost" or "localhost:portnumber", your call.|
| VERBOSE_LOGGING | If "True", adds additional logging information. |
