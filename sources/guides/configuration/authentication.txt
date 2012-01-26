Authentication Configuration Guide
======================================

Adding backends
---------------
Adding authentication backends in mobyle2 can be performed in the 
authentication settings of your web interface, accessible in the 
"auth>>Add a backend" menu at a URL similar to:
http://yourdomain.net/mobyle2/auths/@@add.
Of course, you have to have the required permission to add them.

The information you have to provide is:
- the name of the backend
- its description, for documentation purpose,
- and chose a type of backend: depending on this type, you will be
asked for further type-specific information (see in the corresponding
sections below).

Modifying the authentication settings requires that you restart your
 server.

Github authentication configuration guide
-----------------------------------------
The configuration of a Github authentication backend requires
a GitHub account. Once you are logged in, you have to register
your mobyle2 instance there: https://github.com/account/applications/ .

You can do this by clicking on "Register a new application". You are
then asked to provide:

1. a description (a label for your own use),
2. the URL of your application, i.e. the main URL of your
mobyle2 instance, which will look like http://yourdomain.net/mobyle2,
3. the callback URL to your application, i.e. the callback URL to
the velruse application on your mobyle2 instance, which will look like
http://yourdomain.net/velruse.

Once this is performed, you can add the Github authentication backend
to mobyle2. The github-specific information is:

1. the API key, which is the "Client ID" in the github interface,
2. the API secret, which is the "Client secret" in the github interface.

.. vim:set ft=rest sts=4 ts=4 et:
