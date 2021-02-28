FROM ubuntu:20.04
ENV workdir /var/www

# Production OSM setup
ENV RAILS_ENV=production
ENV EXECJS_RUNTIME=Node

# installation dependencies
RUN apt-get update && apt-get install -y wget gnupg2 apt-transport-https ca-certificates dirmngr

# Install the openstreetmap-website dependencies and passenger dependencies
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y ruby2.7 libruby2.7 ruby2.7-dev \
  libmagickwand-dev libxml2-dev libxslt1-dev libpqxx-dev\
  apache2 apache2-dev build-essential git-core \
  libsasl2-dev imagemagick libffi-dev curl libgd-dev libarchive-dev libbz2-dev libsasl2-dev
RUN gem2.7 install bundler

# Install node for some images process dependencies
RUN curl -sL https://deb.nodesource.com/setup_12.x | bash
RUN apt-get install -y nodejs
RUN ln -s "$(which node)" /usr/bin/nodejs


# Fixing image_optim issues, installing a bush of libraries from : https://github.com/toy/image_optim#pngout-installation-optional
RUN apt-get install -y advancecomp gifsicle jhead jpegoptim optipng
RUN git clone -b 2.12.2 https://github.com/kornelski/pngquant.git && \
  cd pngquant && \
  ./configure && \
  make && \
  make install
RUN git clone https://github.com/tjko/jpeginfo.git && \
  cd jpeginfo && \
  git checkout 743b1b15002f05298a0672e9d0f23ada240ababf && \
  ./configure && \
  make && \
  make strip && \
  make install
RUN wget http://iweb.dl.sourceforge.net/project/pmt/pngcrush/1.8.12/pngcrush-1.8.12.tar.gz && \
  tar zxf pngcrush-1.8.12.tar.gz && \
  cd pngcrush-1.8.12 && \
  make && cp -f pngcrush /usr/local/bin
RUN npm install -g svgo



# Install the PGP key
RUN apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys 561F9B9CAC40B2F7

# Add the APT repository
RUN sh -c 'echo deb https://oss-binaries.phusionpassenger.com/apt/passenger focal main > /etc/apt/sources.list.d/passenger.list'
RUN apt-get update

# Install Passenger + Apache module
RUN apt-get install -y libapache2-mod-passenger

# Enable the Passenger Apache module and restart Apache
RUN echo "ServerName $(cat /etc/hostname)" >> /etc/apache2/apache2.conf
RUN a2enmod passenger
RUN apache2ctl restart

# Check installation
RUN /usr/bin/passenger-config validate-install
RUN /usr/sbin/passenger-memory-stats

# Clone the openstreetmap-website
RUN rm -rf $workdir && git clone https://github.com/openstreetmap/openstreetmap-website.git $workdir 
WORKDIR $workdir
# gitsha ab31e016a348a13afa289b3a1c3acc4e4acfd8c4 at Sep 21, 2020
RUN git checkout ab31e016a348a13afa289b3a1c3acc4e4acfd8c4

## add yarn source
RUN curl -sS https://dl.yarnpkg.com/debian/pubkey.gpg | apt-key add -  && \
  echo "deb https://dl.yarnpkg.com/debian/ stable main" | tee /etc/apt/sources.list.d/yarn.list

# Install the yarn and tzinfo-data
RUN apt-get update && apt-get install -y libv8-dev yarn
RUN echo "gem 'tzinfo-data'" >> Gemfile

# Install node again, as for unknown reason it gets deleted
RUN apt-get install -y nodejs

# Install app dependencies
RUN bundle update listen && bundle install && bundle exec rake yarn:install && \
  touch config/settings.local.yml

# Configure database.yml, application.yml and secrets.yml
ADD config/database.yml $workdir/config/database.yml
ADD config/application.yml $workdir/config/settings.yml
ADD config/storage.yml $workdir/config/storage.yml
RUN echo "#session key \n\
  production: \n\
  secret_key_base: $(bundle exec rake secret)" > $workdir/config/secrets.yml

# Protect sensitive information
RUN chmod 600 $workdir/config/database.yml $workdir/config/settings.yml $workdir/config/secrets.yml

# Configure ActionMailer SMTP settings, Replace config/initializers/action_mailer.rb with our configurations
ADD config/action_mailer.rb config/initializers/action_mailer.rb

# Precompile the website assets
RUN rake i18n:js:export assets:precompile
# The rack interface requires a `tmp` directory to use openstreetmap-cgimap
RUN ln -s /tmp /var/www/tmp

# Add Apache configuration file
ADD config/production.conf /etc/apache2/sites-available/production.conf
RUN a2dissite 000-default
RUN a2ensite production

# Enable required apache modules for the cgimap Apache service
RUN a2enmod proxy proxy_http rewrite

# Config the virtual host apache2
# ADD config/cgimap.conf /tmp/
# RUN sed -e 's/RewriteRule ^(.*)/#RewriteRule ^(.*)/' \
#   -e 's/\/var\/www/\/var\/www\/public/g' \
#   /tmp/cgimap.conf > /etc/apache2/sites-available/cgimap.conf
# RUN chmod 644 /etc/apache2/sites-available/cgimap.conf
# RUN a2ensite cgimap
RUN apache2ctl configtest

# permissions for logs folder
RUN chown -R www-data:www-data /var/log/web && chmod -R 775 /var/log/web

# Set Permissions for www-data
RUN chown -R www-data: /var/www

# Script to start the app
ADD start.sh $workdir/start.sh

CMD $workdir/start.sh