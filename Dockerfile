FROM cccs/assemblyline-v4-service-base:latest

ENV SERVICE_PATH unpacme_al.UnpacMeAL

WORKDIR /opt/al_service

# Copy service code
COPY . .

# Switch to assemblyline user
USER assemblyline
