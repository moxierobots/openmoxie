FROM emqx/emqx:5.6.0

# Copy EMQX configuration
COPY ./site/data/emqx.conf /opt/emqx/etc/emqx.conf
COPY ./site/data/log.conf /opt/emqx/etc/log.conf

# Create logs directory
RUN mkdir -p /opt/emqx/log

# Expose MQTT ports
EXPOSE 1883 8883 8083 8084 18083

# Set working directory
WORKDIR /opt/emqx

# Start EMQX
CMD ["/opt/emqx/bin/emqx", "foreground"]
