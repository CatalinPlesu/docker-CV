##!/bin/bash

# If your resume.tex is in the current directory
# podman run --rm -v $(pwd):/latex latex-compiler pdflatex main.tex

# Or for an interactive session
podman run --rm -it -v $(pwd):/latex latex-compiler /bin/bash
