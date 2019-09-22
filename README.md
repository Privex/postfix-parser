
Privex's Postfix Log Parser + Web UI
=====================================

This is a small application designed to parse the log output of the Postfix SMTP server (usually `/var/log/mail.log`),
and convert it into easily queryable data inside of [RethinkDB](https://rethinkdb.com/).

It includes a Web UI built with [Quart](https://github.com/pgjones/quart) and [VueJS](https://vuejs.org/) - allowing
for easily navigating and filtering the log data straight from your browser.

**DISCLAIMER:** The Web UI only includes a very basic password prompt which reads the password from the `.env` file.
This application is NOT intended to be public facing - we strongly recommend for production use-cases that it's
kept restricted within a corporate VPN / LAN.

There's also no requirement to run both the Web UI and the actual log parser/importer on the same server, as the
parsed data is kept in RethinkDB - thus you can run the WebUI on a separate server as long as it has access to the
RethinkDB server.


![Screenshot of Log View Web UI](https://cdn.privex.io/github/postfix-parser/postfix-parser.png)

![Screenshot of Email Show Modal](https://cdn.privex.io/github/postfix-parser/postfix-parser-modal.png)

Install
========

**Pre-requisites**

 - [RethinkDB](https://rethinkdb.com/) (for storing the queryable log data)
 - Python 3.7 MINIMUM (will not work on earlier versions)
 - Pipenv (`python3.7 -m pip install pipenv`) - for creating a virtualenv + installing dependencies


```

apt update -y
apt install -y python3.7 python3.7-dev python3-pip

python3.7 -m pip install -U pipenv

adduser --gecos "" --disabled-password mailparser
# To ensure that the parser is able to read the mail.log, add the user to the appropriate groups
gpasswd -a mailparser syslog adm postfix

su - mailparser

git clone https://github.com/Privex/postfix-parser.git
cd postfix-parser
pipenv install

cp example.env .env
# Adjust the example .env as needed. Make sure you set SECRET_KEY to a long random string, and change ADMIN_PASS 
# to the password you want to use to log into the web application.
nano .env

# Add a crontab entry to run the parse/import script every minute or so
# You should use a file lock utility such as `flock` (included by default on Ubuntu) or `lckdo` to prevent the
# cron overlapping if there's a lot to parse.

crontab -e
# *  *   *   *   *    flock /tmp/lck_mailparser /home/mailparser/postfix-parser/run.sh cron

####
# DEVELOPMENT
####

./run.sh dev         # Run the development server with automatic restart on edits
./run.sh parse       # Import MAIL_LOG immediately

####
# PRODUCTION
####

exit

# (AS ROOT)

# Production systemd service for the WebUI
install -m 644 /home/mailparser/postfix-parser/postfix-parser.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable postfix-parser.service

```

# License

This project is licensed under the **GNU AGPL v3**

For full details, please see `LICENSE.txt` and `AGPL-3.0.txt`.

Here's the important parts:

 - If you use this software (or substantial parts of it) to run a public service (including any separate user interfaces 
   which use it's API), **you must display a link to this software's source code wherever it is used**.
   
   Example: **This website uses the open source [Privex Postfix Parser](https://github.com/Privex/postfix-parser)
   created by [Privex Inc.](https://www.privex.io)**
   
 - If you modify this software (or substantial portions of it) and make it available to the public in some 
   form (whether it's just the source code, running it as a public service, or part of one) 
    - The modified software (or portion) must remain under the GNU AGPL v3, i.e. same rules apply, public services must
      display a link back to the modified source code.
    - You must attribute us as the original authors, with a link back to the original source code
    - You must keep our copyright notice intact in the LICENSE.txt file

 - Some people interpret the GNU AGPL v3 "linking" rules to mean that you must release any application that interacts
   with our project under the GNU AGPL v3.
   
   To clarify our stance on those rules: 
   
   - If you have a completely separate application which simply sends API requests to a copy of Privex Postfix Parser
     that you run, you do not have to release your application under the GNU AGPL v3. 
   - However, you ARE required to place a notice on your application, informing your users that your application
     uses Privex Postfix Parser, with a clear link to the source code (see our example at the top)
   - If your application's source code **is inside of Privex Postfix Parser**, i.e. you've added your own Python
     views, templates etc. to a copy of this project, then your application is considered a modification of this
     software, and thus you DO have to release your source code under the GNU AGPL v3.

 - There is no warranty. We're not responsible if you, or others incur any damages from using this software.
 
 - If you can't / don't want to comply with these license requirements, or are unsure about how it may affect
   your particular usage of the software, please [contact us](https://www.privex.io/contact/). 
   We may offer alternative licensing for parts of, or all of this software at our discretion.


# Contributing

We're very happy to accept pull requests, and work on any issues reported to us. 

Here's some important information:

**Reporting Issues:**

 - For bug reports, you should include the following information:
     - Version of the project you're using - `git log -n1`
     - The Python package versions you have installed - `pip3 freeze`
     - Your python3 version - `python3 -V`
     - Your operating system and OS version (e.g. Ubuntu 18.04, Debian 7)
 - For feature requests / changes
     - Clearly explain the feature/change that you would like to be added
     - Explain why the feature/change would be useful to us, or other users of the tool
     - Be aware that features/changes that are complicated to add, or we simply find un-necessary for our use of the tool 
       may not be added (but we may accept PRs)
    
**Pull Requests:**

 - We'll happily accept PRs that only add code comments or README changes
 - Use 4 spaces, not tabs when contributing to the code
 - You can use features from Python 3.4+ (we run Python 3.7+ for our projects)
    - Features that require a Python version that has not yet been released for the latest stable release
      of Ubuntu Server LTS (at this time, Ubuntu 18.04 Bionic) will not be accepted. 
 - Clearly explain the purpose of your pull request in the title and description
     - What changes have you made?
     - Why have you made these changes?
 - Please make sure that code contributions are appropriately commented - we won't accept changes that involve 
   uncommented, highly terse one-liners.

**Legal Disclaimer for Contributions**

Nobody wants to read a long document filled with legal text, so we've summed up the important parts here.

If you contribute content that you've created/own to projects that are created/owned by Privex, such as code or 
documentation, then you might automatically grant us unrestricted usage of your content, regardless of the open source 
license that applies to our project.

If you don't want to grant us unlimited usage of your content, you should make sure to place your content
in a separate file, making sure that the license of your content is clearly displayed at the start of the file 
(e.g. code comments), or inside of it's containing folder (e.g. a file named LICENSE). 

You should let us know in your pull request or issue that you've included files which are licensed
separately, so that we can make sure there's no license conflicts that might stop us being able
to accept your contribution.

If you'd rather read the whole legal text, it should be included as `privex_contribution_agreement.txt`.

# Thanks for reading!

**If this project has helped you, consider [grabbing a VPS or Dedicated Server from Privex](https://www.privex.io) - prices start at as little as US$8/mo (we take cryptocurrency!)**
