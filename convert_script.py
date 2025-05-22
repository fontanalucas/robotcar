import os
import cv2
import numpy as np
from tqdm import tqdm

# CONFIGURATION
culane_root = culane_root = os.path.expanduser('~/Downloads/driver_23_30frame(2)')
lines_folder = os.path.join(culane_root, 'driver_23_30frame')  # or other driver folder
output_mask_root = os.path.expanduser('~/Downloads/driver_23_30frame(2)/driver_23_30frame')

# CULane image size
IMAGE_HEIGHT, IMAGE_WIDTH = 590, 1640

def process_txt_to_mask(txt_path):
    mask = np.zeros((IMAGE_HEIGHT, IMAGE_WIDTH), dtype=np.uint8)

    with open(txt_path, 'r') as file:
        lines = file.read().strip().split('\n')  # each lane on one line

    for line in lines:
        parts = line.strip().split()
        points = []
        # Iterate in steps of 2 to get x,y pairs
        for i in range(0, len(parts), 2):
            x = float(parts[i])
            y = float(parts[i+1])
            points.append((int(x), int(y)))

        if len(points) > 1:
            cv2.polylines(mask, [np.array(points)], isClosed=False, color=255, thickness=5)

    return mask


# Walk through all .lines.txt files
for root, _, files in os.walk(lines_folder):
    for file in tqdm(files, desc="Processing .lines.txt"):
        if file.endswith('.lines.txt'):
            txt_path = os.path.join(root, file)

            # Create corresponding mask path
            rel_path = os.path.relpath(txt_path, lines_folder)
            mask_rel_path = rel_path.replace('.lines.txt', '_mask.png')
            mask_output_path = os.path.join(output_mask_root, mask_rel_path)

            # Ensure output directory exists
            os.makedirs(os.path.dirname(mask_output_path), exist_ok=True)

            # Create and save mask
            mask = process_txt_to_mask(txt_path)
            cv2.imwrite(mask_output_path, mask)
            print(f"Saved mask to {mask_output_path}")
