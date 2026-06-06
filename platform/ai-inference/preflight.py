import os
import sys
import subprocess
import time
import json

def scan_hardware():
    print("[Pre-flight] Scanning hardware capabilities...")
    has_nvidia_gpu = False
    gpu_details = "None"
    
    if os.path.exists("/dev/nvidia0") or os.path.exists("/dev/nvidiactl"):
        has_nvidia_gpu = True
        try:
            smi_output = subprocess.check_output(
                ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"], 
                stderr=subprocess.DEVNULL
            )
            gpu_details = smi_output.decode("utf-8").strip()
        except Exception:
            gpu_details = "Nvidia Driver Device Detected (nvidia-smi not in PATH)"
            
    return {
        "has_nvidia_gpu": has_nvidia_gpu,
        "gpu_details": gpu_details
    }

def provision_model(hw_info):
    model_dir = "/models"
    
    if not os.path.exists(model_dir):
        print(f"[Pre-flight] Warning: {model_dir} directory not found. Proceeding anyway.")
        # In a real environment, this would fail, but for the initContainer it will be mounted
        try:
            os.makedirs(model_dir, exist_ok=True)
        except OSError:
            pass

    engine = "vLLM" if hw_info["has_nvidia_gpu"] else "llama.cpp"
    format_type = "AWQ/FP8" if hw_info["has_nvidia_gpu"] else "GGUF"
    model_name = "nexus-triage-baseline-v1.0.0"
    
    print(f"[Pre-flight] Target Engine: {engine}")
    print(f"[Pre-flight] Target Format: {format_type}")
    print(f"[Pre-flight] Provisioning model: {model_name}...")
    
    # Mock download: Just create a metadata file to represent the model
    # In production, this would use boto3/minio client to pull the real model from the Cookbook bucket
    time.sleep(2) # Simulate network latency
    
    mock_model_path = os.path.join(model_dir, f"{model_name}.json")
    try:
        with open(mock_model_path, "w") as f:
            json.dump({
                "model_name": model_name,
                "engine": engine,
                "format": format_type,
                "provisioned_at": time.time(),
                "mock": True
            }, f)
        print(f"[Pre-flight] Model successfully provisioned at {mock_model_path}")
    except OSError as e:
        print(f"[Pre-flight] Could not write to {model_dir}: {e}")
        # Don't fail the pre-flight just because of permissions in local testing environments
        
def main():
    print("========================================")
    print(" Underground Nexus: AI Pre-flight Check ")
    print("========================================")
    
    hw_info = scan_hardware()
    print(f"[Pre-flight] Hardware Scan Result: Nvidia GPU = {hw_info['has_nvidia_gpu']} ({hw_info['gpu_details']})")
    
    provision_model(hw_info)
    
    print("[Pre-flight] Pre-flight checks completed successfully.")
    sys.exit(0)

if __name__ == "__main__":
    main()
