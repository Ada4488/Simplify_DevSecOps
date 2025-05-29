# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set environment variables for Terraform version and allow overriding target architecture
ARG TERRAFORM_VERSION=1.7.5
ARG TARGETARCH

# Determine actual architecture if TARGETARCH is not set (for older Docker versions or non-buildkit)
# and default to amd64. For modern Docker with buildkit, TARGETARCH is typically set automatically.
RUN if [ -z "$TARGETARCH" ]; then \
        echo "TARGETARCH not set, determining architecture..."; \
        case "$(uname -m)" in \
            x86_64) ARCH=amd64 ;; \
            aarch64) ARCH=arm64 ;; \
            armv7l) ARCH=arm ;; \
            *) echo "Unsupported architecture: $(uname -m)"; exit 1 ;; \
        esac; \
    else \
        ARCH=$TARGETARCH; \
    fi; \
    echo "Using architecture: $ARCH"; \
    # Install dependencies for Terraform download and system utilities
    # Also install gnupg for potential signature verification in future, though not used now
    apt-get update && apt-get install -y --no-install-recommends \
    wget \
    unzip \
    gnupg \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/* && \
    # Download and install Terraform
    # Using ARCH variable determined above
    wget "https://releases.hashicorp.com/terraform/${TERRAFORM_VERSION}/terraform_${TERRAFORM_VERSION}_linux_${ARCH}.zip" && \
    wget "https://releases.hashicorp.com/terraform/${TERRAFORM_VERSION}/terraform_${TERRAFORM_VERSION}_SHA256SUMS" && \
    wget "https://releases.hashicorp.com/terraform/${TERRAFORM_VERSION}/terraform_${TERRAFORM_VERSION}_SHA256SUMS.sig" && \
    # Simple checksum verification (signature verification would require importing HashiCorp's GPG key)
    grep "terraform_${TERRAFORM_VERSION}_linux_${ARCH}.zip" terraform_${TERRAFORM_VERSION}_SHA256SUMS | sha256sum -c - && \
    unzip "terraform_${TERRAFORM_VERSION}_linux_${ARCH}.zip" -d /usr/local/bin && \
    chmod +x /usr/local/bin/terraform && \
    # Clean up downloaded files
    rm -f "terraform_${TERRAFORM_VERSION}_linux_${ARCH}.zip" \
           "terraform_${TERRAFORM_VERSION}_SHA256SUMS" \
           "terraform_${TERRAFORM_VERSION}_SHA256SUMS.sig"

# Verify Terraform installation
RUN terraform version

# Set the working directory in the container
WORKDIR /app

# Copy the dependencies file to the working directory
COPY requirements.txt .

# Install any needed dependencies specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the content of the local src directory to the working directory
COPY . .

# Command to run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
