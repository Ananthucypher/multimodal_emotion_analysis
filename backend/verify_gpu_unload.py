import torch
import time
import gc

def print_gpu_memory():
    if torch.cuda.is_available():
        allocated = torch.cuda.memory_allocated() / 1024**3
        reserved = torch.cuda.memory_reserved() / 1024**3
        print(f"GPU Memory: Allocated={allocated:.2f}GB, Reserved={reserved:.2f}GB")
    else:
        print("No GPU available.")

def verify_unload():
    print("--- Initial State ---")
    print_gpu_memory()
    
    print("\n--- Loading Dummy Tensor (1GB) ---")
    # Allocate ~1GB float32 tensor
    x = torch.ones(256*1024*1024, device='cuda') 
    time.sleep(1)
    print_gpu_memory()
    
    print("\n--- Deleting Tensor & Emptying Cache ---")
    del x
    gc.collect()
    torch.cuda.empty_cache()
    time.sleep(1)
    print_gpu_memory()
    
    print("\n--- Verification Complete ---")

if __name__ == "__main__":
    try:
        if torch.cuda.is_available():
            verify_unload()
        else:
            print("Skipping test: No GPU.")
    except Exception as e:
        print(f"Test failed: {e}")
