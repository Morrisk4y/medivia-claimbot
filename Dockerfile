# Use the official Ubuntu 22.04 image as the base
FROM ubuntu:22.04

# Install dependencies
RUN apt-get update && apt-get install -y \
    nano \
    curl \
    git \
    golang \
    sudo \
    vim \
    wget \
    build-essential \
    zlib1g-dev \
    libssl-dev \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Set working directory to /app
WORKDIR /app

# Download and extract Python source code
RUN wget https://www.python.org/ftp/python/3.12.3/Python-3.12.3.tgz \
    && tar -xzf Python-3.12.3.tgz \
    && rm Python-3.12.3.tgz

# Build Python from source
RUN cd Python-3.12.3 \
    && ./configure --enable-optimizations \
    && make -j $(nproc) \
    && make install

# Cleanup the build directory to reduce image size
RUN rm -rf /app/Python-3.12.3

# Upgrade pip and install required Python packages
COPY requirements.txt .
RUN python3 -m pip install --upgrade pip \
    && python3 -m pip install --no-cache-dir -r requirements.txt

# Add application code (assuming your app code resides in the same directory as Dockerfile)
COPY . .

# Command to run the application
CMD ["python3", "app.py"]
