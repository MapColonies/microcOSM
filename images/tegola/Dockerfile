FROM gospatial/tegola:v0.12.1
# Volume
ENV CACHEDATA /mnt/data
RUN mkdir -p "$CACHEDATA" && \
  chmod 777 "$CACHEDATA" && \
  apk update && \
  apk add --no-cache python3

COPY ./requirements.txt .
RUN pip3 install -r requirements.txt
VOLUME /mnt/data
COPY ./config/config.toml /opt/tegola_config/config.toml
COPY ./start.py .
RUN chmod a+x ./start.py
CMD ./start.py
ENTRYPOINT [ "./start.py" ]
