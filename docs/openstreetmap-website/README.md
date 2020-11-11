# openstreetmap-website ("The Rails Port")
>
## **Semi-Automatic Installation (Development Environment)**

openstreetmap-website installation with a decoupled postgres db running in a container

1. Build `docker image build --build-arg VERSION='0.1.0' --build-arg BUILD_DATE=$((Get-Date).toString("yyyy-MM-ddTHH:mm:ss.ffZ")) -t core/osm-web:v1 .`
2. Create a docker network and add a postgres container to it ([See below](#Docker-Network-&-Postgres-Container))
3. Run `docker run -e POSTGRES_HOST=POSTGRES_HOST -e POSTGRES_DB=POSTGRES_DB -e POSTGRES_USER=POSTGRES_USER -e POSTGRES_PASSWORD=POSTGRES_PASSWORD -d -it --name osm-web --network some-network -p 3000:3000 core/osm-web:v1`
4. Run `docker exec -it osm-web /bin/bash`
5. In the container run config & run server script `./start.sh`

## **Configure iD editor**

* Log into your Rails Port instance - e.g. <http://localhost:3000> (if ran on docker <http://DOCKER-MACHINE-IP:3000>)
* Click on your user name to go to your user page
* Click on "my settings" on the user page
* Click on "oauth settings" on the My settings page
* Click on 'Register your application'.
* Unless you have set up alternatives, use Name: "Local iD" and URL: "http://localhost:3000"
* Check the 'modify the map' box.
* Everything else can be left with the default blank values.
* Click the "Register" button
* On the next page, copy the "consumer key"
* Edit config/settings.local.yml in your rails tree
* Add the "id_key" configuration key and the consumer key as the value
* Restart your rails server

## **Manual Installation (Development Environment)**

For original instructions see - [INSTALL.md](https://github.com/openstreetmap/openstreetmap-website/blob/master/INSTALL.md)
Development environment configurations are in *italics*

### Part I - Dependencies Image

1. docker pull ubuntu:bionic
2. docker run -it ubuntu:bionic
3. apt-get update
4. DEBIAN_FRONTEND="noninteractive" TZ="Asia/Jerusalem" apt-get install -y ruby2.5 libruby2.5 ruby2.5-dev bundler \
        libmagickwand-dev libxml2-dev libxslt1-dev nodejs \
        apache2 apache2-dev build-essential git-core firefox-geckodriver \
        postgresql postgresql-contrib libpq-dev libsasl2-dev \
        imagemagick libffi-dev libgd-dev libarchive-dev libbz2-dev
5. gem2.5 install bundler
6. exit
7. docker ps -a # copy container id
8. docker commit <container_id> core/ubuntu-rails-deps

### Part II - Repo Installation

9. git clone --depth=1 <https://github.com/openstreetmap/openstreetmap-website.git> # shallow clone
10. cd openstreetmap-website
11. bundle install # if there is an error try: rm Gemfile.lock - <https://github.com/rubygems/bundler/illssues/6227#issuecomment-520171632>
12. curl -sL <https://deb.nodesource.com/setup_10.x> | sudo -E bash - # at least node 10 is needed
13. sudo apt-get install -y nodejs
14. curl -sS <https://dl.yarnpkg.com/debian/pubkey.gpg> | sudo apt-key add -
15. echo "deb <https://dl.yarnpkg.com/debian/> stable main" | sudo tee /etc/apt/sources.list.d/yarn.list
16. sudo apt update && sudo apt install yarn
17. bundle exec rake yarn:install
18. touch config/settings.local.yml - here you should config the local osm deployment, probably with deployment env vars
19. cp config/example.storage.yml config/storage.yml
20. cp config/example.database.yml config/database.yml
21. Edit config/database.yml with a running postgres connection properties - here you should config the postgresql deployment, probably with deployment env vars
22. adduser --disabled-password --gecos "" osm - you can skip the prompts
23. usermod -aG sudo osm
24. /etc/init.d/postgresql start
25. cd .. && chown -R osm ./openstreetmap-website
26. su osm
27. sudo -u postgres -i
28. createuser -s osm
29. exit
30. bundle exec rake db:create
31. psql -d openstreetmap -c "CREATE EXTENSION btree_gist" (in postgres container)
32. psql -d openstreetmap -f db/functions/functions.sql (in postgres container - download git and openstreetmap-website repo. apt update && apt install git && git clone --depth=1 <https://github.com/openstreetmap/openstreetmap-website.git> && su postgres && psql ...)
33. bundle exec rake db:migrate
34. docker ps -a # copy container id
35. docker commit <container_id> core/rails-port

### Part III - Run Service

36. docker run -p 3000:3000 -it core/rails-port
37. sudo service postgresql start # run postgreslq service
38. cd openstreetmap-website
39. bundle exec rails server -b 0.0.0.0

## Configure

For original instructions see - [CONFIGURE.md](https://github.com/openstreetmap/openstreetmap-website/blob/34dd2293db85e28b7e5df0889b0b778a685306bb/CONFIGURE.md)

### Using iD Editor

Follow instructions to set up iD editor as mentioned above, but **give all permmisions** ([ref](https://help.openstreetmap.org/questions/62954/id-editor-error-in-my-own-server-no-route-matches-get-landhtml))

## Docker Network & Postgres Container

1. docker network create some-network
2. docker pull postgres:10.12 (compatible with the version in "the rails post")
3. docker run --network some-network --name postgres10.12 -e POSTGRES_PASSWORD=postgres -d postgres:10.12 -c listen_addresses='*'
