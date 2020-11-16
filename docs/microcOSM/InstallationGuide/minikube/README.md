# MicrocOSM on minikube

Easy installation for the OpenStreetMap software stack.

# Requirements

Please follow the requirements [here](/microcOSM/InstallationGuide/README.md) before you start installing microcOSM on minikube.

You will need `minikube` installed on your system.
- Installing `minikube`: https://minikube.sigs.k8s.io/docs/start/

make sure minikube is running before advancing.

_`minikube` extension for vscode extension for `zsh` are recommended._

# Installation

## Installing microcosm

Clone the microcosm repo:

```sh
git clone https://github.com/MapColonies/microcOSM.git
cd microcOSM/
```

Switch docker context to minikube:

```sh
eval $(minikube docker-env)
```

build all the images:

```sh
cd images
./build-containers.sh
cd ..
```

copy the `myvalues.example.yaml` file:

```sh
cd helm
cp microcosm/myvalues.example.yaml myvalues.yaml
```

get the node ip from minikube:

```sh
minikube ip
```

insert the ip into my values under the `domain.domainName` key.
edit any other values you need.

install the helm chart with your local values:

```sh
helm install -f myvalues.yaml microcosm ./microcosm
```

Once everything is running, you should be able to access the OpenStreetMap website (run `minikube service list` to get the url).

NOTE that downloading the data and populating the db is a process that runs behind the scenes, so not all the data should appear right away (it can take up to 20 minutes for israel).

## Setup pgAdmin4

pgAdmin4 is a web based UI for managing postgreSQL.

1. Add pgAdmin4 chart:

```sh
helm repo add runix https://helm.runix.net/
```

2. install the chart

```sh
helm install pgadmin runix/pgadmin4 \
--set env.password=SuperSecret \
--set env.email=email@example.com \
--set service.type=NodePort
```

Now you should be able to access pgAdmin4 website (run `minikube service list` to get the url).

3. Log in with the email and password from the previous command.

4. Right click on servers at the top left corner and click on create :arrow_right: new server.

5. fill the form with the following information.

> - NAME: openstreetmap
> - HOST: microcosm-web-db
> - PORT: 5432
> - USERNAME: postgres
> - PASSWORD: 1234

**Note**: If you changed the default values in the myvalues.yaml file, change the values above accordingly.

## Create OSM user

1. Go to the OSM website on your local machine `http://MINIKUBEIP`.
2. click `sign up` button on top right of the window.
3. Follow the instructions and create a new user.

At the end of the process you should be redirected to `http://MINIKUBEIP/user/save` and see Application error on screen.

4. On pgAdmin, Click on databases :arrow_right: openstreetmap :arrow_right: schemas :arrow_right: public :arrow_right: tables, and find the USERS table.

5. right click the USERS table and click View/Edit data :arrow_right: All Rows.

6. Find your user at the bottom table, double click the status column, and change the text to `active`.

7. Click execute (or press F6).

8. Go back to your openstreetmap application and log in with your activated user.

## Configure ID editor

1. Click on your user name on top right of the website and click `My Settings`.

2. Under the header `My Settings` click `oauth settings`.

3. Click `Register your application` and fill the form with the following information:

> - Name: WHATEVERYOUWANT
> - Main Application URL: http://MINIKUBEIP

4. Check all the boxes and click Register.

5. Copy the `Consumer Key` from the screen.

6. change the value of the `web.oauth.key` field in `myvalues.yaml` to the key you copied.

7. upgrade the helm chart:

```sh
helm upgrade -f myvalues.yaml microcosm ./microcosm
```

8. scale the web deployment:

```sh
kubectl scale deployment microcosm-web --replicas=0
kubectl scale deployment microcosm-web --replicas=1
```

### Done. now you can edit in openstreetmap :sunglasses:
![cat](https://i.kym-cdn.com/photos/images/original/001/879/958/fb1.gif)
