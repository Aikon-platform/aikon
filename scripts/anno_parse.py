import timeit
import re
from typing import Dict, Tuple, Optional

# Sample data
sample_anno = {
    "on": "https://aikon.enpc.fr/aikon/iiif/v2/wit5_man7_anno20/canvas/c101.json#xywh=117,183,1265,2008"
}


# Original approach
def original_approach(anno: Dict) -> Optional[Tuple[str, str]]:
    on_value = anno["on"]
    canvas = on_value.split("/canvas/c")[1].split(".json")[0]
    canvas_num = int(canvas)
    xywh = on_value.split("xywh=")[1]
    return canvas, xywh


# Regex approach
CANVAS_PATTERN = re.compile(r"/canvas/c(\d+)\.json#")


def regex_approach(anno: Dict) -> Optional[Tuple[str, str]]:
    on_value = anno["on"]
    match = CANVAS_PATTERN.search(on_value)
    if not match:
        return None
    canvas = match.group(1)
    canvas_num = int(canvas)
    xywh = on_value.split("#xywh=")[1]
    return canvas, xywh


# New approach: using str.find() and slicing
def find_slice_approach(anno: Dict) -> Optional[Tuple[str, str]]:
    on_value = anno["on"]
    start = on_value.find("/canvas/c") + 9
    end = on_value.find(".json", start)
    if start == 8 or end == -1:  # "/canvas/c" not found or ".json" not found
        return None
    canvas = on_value[start:end]
    canvas_num = int(canvas)
    xywh = on_value[on_value.find("#xywh=") + 6 :]
    return canvas, xywh


# Benchmark function
def benchmark(func, name):
    time = timeit.timeit(lambda: func(sample_anno), number=1000000)
    print(f"{name}: {time:.6f} seconds")


# Run benchmarks
if __name__ == "__main__":
    print("Running benchmarks (1,000,000 iterations each):")
    benchmark(original_approach, "Original Approach")
    benchmark(regex_approach, "Regex Approach")
    benchmark(find_slice_approach, "Find & Slice Approach")

    # Verify correctness
    print("\nVerifying correctness:")
    print(f"Original: {original_approach(sample_anno)}")
    print(f"Regex: {regex_approach(sample_anno)}")
    print(f"Find & Slice: {find_slice_approach(sample_anno)}")
