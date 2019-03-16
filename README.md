# snakrAWS
Custom short URL generator + usage analytics, ported from Google Cloud/Python 2 to AWS/Postgres RDS/Python 3

### Custom Settings
| Setting | Description |
| --- | --- |
| SHORTURL_HOST | The custom domain (host) to use for your short URLs. Mine is "bret.guru", generating short URLs that look like  http://bret.guru/aBc43d |
| SITE_MODE | "dev" or "prod". When set to "dev", sets SHORTHOST_URL to "localhost" or "localhost:portnumber", your call.|
| DATABASE_MODE | Separate "dev" or "prod" setting for the db backend. "Dev" should point to a localhost Postgres instance in the DATABASES config; "prod" should point to your AWS RDB Postgres instance. You can set SITE_MODE and DATABASE_MODE to "dev"/"dev", "dev"/"prod", or "prod"/"prod", depending on how you are testing.|
| ENABLE_ANALYTICS | If "True", populates the various dimension and FactEvent tables when short URLs are created and used, including geolocation of the user. If "False", only the ShortURL and LongURL tables are populated and no geolocation occurs. |
| VERBOSE_LOGGING | If "True", adds additional logging information. |
| SHORTENING_POSTBACK | The URL path fragment that leads to the web page from which you can shorten URLs. For example, if SHORTURL_HOST is set to "my.site" and SHORTENING_POSTBACK is set to "shorten", the UI form from which to shorten URLs will be located at "http://my.site/shorten". (TBD: If SSL_ENABLED = "True", this will be "https://my.site/shorten". THIS FEATURE IS TBD.) |
| ADMIN_POSTBACK | The URL path fragment that leads to the Django admin page. Works like the SHORTENING_POSTBACK. |
| JET_POSTBACK | Used by django-jet. Don't alter this. |
| JET_DASHBOARD_POSTBACK | Used by django-jet. Don't alter this. |
| INDEX_HTML | The "home page" to return if the user browses to SHORTURL_HOST with no additional path. |
| ENABLE_FAST_PROFANITY_CHECKING | If "True", turns on checking of URLs for profanity (not the target content, just the URL.) FAST uses a quality score/machine learning check that is quick, but has a higher miss rate than the DEEP method (see below). |
| ENABLE_DEEP_PROFANITY_CHECKING | If "True", turns on checking of URLs for profanity (not the target content, just URL.) DEEP uses a blacklist lookup check that is slower than the FAST method, but is more thorough, though still imperfect. |
| ENABLE_LONG_URL_PROFANITY_CHECKING | If either of the above settings is "True", AND this setting is "True", it turns on profanity checking for the long URL (not it s content, just the URL itself). If either of the above settings is "True", AND this setting is "False", only the generated short URL is checked. |
| GEOLOCATION_API_URL | SnakrAWS uses IPStack (www.ipstack.com) for geolocation lookup of the user if ENABLE_ANALYTICS = "True". This setting holds URL of the API call to make to IPStack to perform geolocation, includiong the IPStack API key value (get yours at the IPStack site). |
| SHORTURL_PATH_SIZE | The size of the short URL path to generate; set it to no less than 5. For example, if set to 6, short URLs will look like "http://my.site/a6yEw4" or "http://my.site/9ueRTT". Does not affect the size of custom "vanity" URLs if the vanity path is supplied on the short URL form; any vanity size can be used up to 40 characters. Changing this value does not affect short URLs already generated; they can continue to be used and will work as-is. You can make this value bigger or smaller anytime you want. |
| SHORTURL_PATH_ALPHABET | Specifies the characters allowed in short URLs. These must be URL-safe characters. Defaults to all digits, a-z, and A-Z, except the easily-confused characters "0", "O", "o", "1", and "l". |
| CANONICAL_MESSAGES | List of messages that can be returned by Snakr. |
| BADBOTLIST | List of known bots that are 403d by Snakr. You should really use a front-end solution for this. |
