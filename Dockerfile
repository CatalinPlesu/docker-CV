# Use Ubuntu as base image
FROM ubuntu:22.04

# Set environment variables to avoid interactive prompts during installation
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=UTC

# Update package list and install essential packages
RUN apt-get update && apt-get install -y \
    # Core LaTeX distribution
    texlive-latex-base \
    texlive-latex-recommended \
    texlive-latex-extra \
    texlive-fonts-recommended \
    texlive-fonts-extra \
    # FontAwesome package
    texlive-font-utils \
    # Additional packages that might be needed
    texlive-lang-english \
    texlive-science \
    texlive-pictures \
    texlive-plain-generic \
    # PDF tools (pdflatex is included in texlive-latex-base)
    texlive-binaries \
    # Git for version control (optional)
    git \
    # Wget/curl for downloading files (optional)
    wget \
    curl \
    # Clean up to reduce image size
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install additional LaTeX packages via tlmgr if needed
RUN tlmgr init-local || echo "tlmgr not available, using system packages"

# Set working directory
WORKDIR /latex

COPY compiler.py /latex/

# Create a volume mount point for LaTeX files
VOLUME ["/latex"]

# Default command to run the compiler server
CMD ["python3", "compiler.py"]
