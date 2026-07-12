# ML.NET with Docker: Regression and Forecasting Models

This project demonstrates how to run ML.NET regression and forecasting models using Docker. It includes setup instructions, explanations of the process, and troubleshooting tips.

## Prerequisites

- Docker installed on your machine
- Basic knowledge of Docker and ML.NET
- Your dataset file (e.g., `Indicator_1h.csv`)

## Project Structure
mlnet-docker-project/
│
├── Dockerfile
├── run_models.sh
├── Indicator_1h.csv
└── README.md

## Setup and Running Instructions

### Step 1: Create the Dockerfile

Create a file named `Dockerfile` in your project directory with the following content:

```dockerfile
FROM mcr.microsoft.com/dotnet/sdk:6.0

# Install .NET Core 3.1
RUN wget https://packages.microsoft.com/config/debian/11/packages-microsoft-prod.deb -O packages-microsoft-prod.deb && \
    dpkg -i packages-microsoft-prod.deb && \
    apt-get update && \
    apt-get install -y dotnet-sdk-3.1

# Install ML.NET CLI and other necessary tools
RUN dotnet tool install -g mlnet && \
    apt-get install -y wget gnupg2 software-properties-common

# Install OpenBLAS as an alternative to MKL
RUN apt-get update && \
    apt-get install -y libopenblas-dev liblapack-dev libgomp1

# Set up environment variables
ENV PATH="${PATH}:/root/.dotnet/tools"
ENV LD_LIBRARY_PATH="/usr/lib/x86_64-linux-gnu:${LD_LIBRARY_PATH}"

WORKDIR /app

# Copy the dataset and the shell script into the container
COPY Indicator_1h.csv .
COPY run_models.sh .

# Make the shell script executable
RUN chmod +x run_models.sh

# Debug: List contents of the working directory and show first few lines of the CSV
RUN ls -la && head -n 5 Indicator_1h.csv

# Run the shell script
CMD ["/bin/bash", "run_models.sh"]

```
### Open terminal and run commands
docker build -t mlnet-docker-project .
docker run --rm -v $(pwd):/app mlnet-docker-project