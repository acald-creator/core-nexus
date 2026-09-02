FROM cgr.dev/chainguard/python:latest-dev

WORKDIR /home/nonroot

ENV PATH="/home/nonroot/.local/bin:${PATH}"

# Copy requirements and install JupyterLab + data science tools
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create work directory for PVC mount
RUN mkdir -p /home/nonroot/work

COPY mcp_client_example.ipynb /home/nonroot/work/

EXPOSE 8888

USER nonroot

ENTRYPOINT ["jupyter", "lab", "--ip=0.0.0.0", "--port=8888", "--no-browser", "--NotebookApp.token=''", "--NotebookApp.password=''", "--NotebookApp.notebook_dir='/home/nonroot/work'"]
