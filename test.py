import pyopencl as cl

def list_opencl_devices():
    platforms = cl.get_platforms()
    if not platforms:
        print("No OpenCL platforms found.")
        return

    for platform in platforms:
        print(f"Platform: {platform.name}")
        devices = platform.get_devices(cl.device_type.ALL)
        if not devices:
            print(f"  No devices found for platform {platform.name}.")
        for device in devices:
            print(f"  Device: {device.name}")
            print(f"    Type: {cl.device_type.to_string(device.type)}")
            print(f"    Compute Units: {device.max_compute_units}")
            print(f"    Global Memory Size: {device.global_mem_size / (1024**2)} MB")

if __name__ == "__main__":
    list_opencl_devices()
