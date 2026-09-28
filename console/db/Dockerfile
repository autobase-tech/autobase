FROM debian:13-slim

ARG POSTGRES_VERSION
ENV POSTGRES_VERSION=${POSTGRES_VERSION:-16}

ARG POSTGRES_PORT
ENV POSTGRES_PORT=${POSTGRES_PORT:-5432}

ARG PGDATA
ENV PGDATA=${PGDATA:-"/var/lib/postgresql/${POSTGRES_VERSION}/main"}

ARG PG_UNIX_SOCKET_DIR
ENV PG_UNIX_SOCKET_DIR=${PG_UNIX_SOCKET_DIR:-"/var/run/postgresql"}

# Set SHELL to /bin/bash
SHELL ["/bin/bash", "-o", "pipefail", "-c"]

RUN apt-get clean && rm -rf /var/lib/apt/lists/partial \
   && apt-get update -o Acquire::CompressionTypes::Order::=gz \
   && DEBIAN_FRONTEND=noninteractive apt-get install --no-install-recommends -y \
      gnupg postgresql-common apt-transport-https lsb-release openssh-client ca-certificates wget curl vim-tiny sudo \
   # PostgreSQL
   && install -d /usr/share/postgresql-common/pgdg \
   && curl -o /usr/share/postgresql-common/pgdg/apt.postgresql.org.asc --fail https://www.postgresql.org/media/keys/ACCC4CF8.asc \
   && echo "deb [signed-by=/usr/share/postgresql-common/pgdg/apt.postgresql.org.asc] https://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list \
   && apt-get update -o Acquire::CompressionTypes::Order::=gz \
   && DEBIAN_FRONTEND=noninteractive apt-get install --no-install-recommends -y postgresql-${POSTGRES_VERSION} \
   && sed -i '/en_US.UTF-8/s/^# //g' /etc/locale.gen && locale-gen \
   && pg_dropcluster ${POSTGRES_VERSION} main \
   # TimescaleDB
   && wget --quiet -O - https://packagecloud.io/timescale/timescaledb/gpgkey | gpg --dearmor -o /etc/apt/trusted.gpg.d/timescaledb.gpg \
   && echo "deb https://packagecloud.io/timescale/timescaledb/debian/ $(lsb_release -cs) main" | tee /etc/apt/sources.list.d/timescaledb.list \
   && apt-get update -o Acquire::CompressionTypes::Order::=gz \
   && DEBIAN_FRONTEND=noninteractive apt-get install --no-install-recommends -y timescaledb-2-postgresql-${POSTGRES_VERSION}

# Clean up
RUN apt-get autoremove -y --purge gnupg wget \
   && apt-get clean -y autoclean \
   && rm -rf /var/lib/apt/lists/*

# Copy configuration files
COPY console/db/postgresql.conf /var/tmp/postgresql.conf
COPY console/db/pg_hba.conf /var/tmp/pg_hba.conf

# Copy pg_start.sh
COPY console/db/pg_start.sh /pg_start.sh
RUN chmod +x /pg_start.sh

VOLUME /var/lib/postgresql

EXPOSE ${POSTGRES_PORT}

CMD ["/pg_start.sh"]
