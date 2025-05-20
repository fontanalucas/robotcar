import cv2
import numpy as np
import matplotlib.pyplot as plt

def simulate_rays_from_bottom_center(image_path, num_rays=15, max_length=300):
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"Image introuvable : {image_path}")

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)

    height, width = binary.shape
    origin = (width // 2, height - 1)  # bas-centre

    ray_distances = []

    # ✅ angle 0 = vers le haut, on veut -90° (gauche) à +90° (droite) donc pi à 0
    angles = np.linspace(np.pi, 0, num_rays)

    plt.figure()
    plt.imshow(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    plt.title("Raycast Simulation")

    for angle in angles:
        hit = False
        for r in range(1, max_length):
            x = int(origin[0] + r * np.cos(angle))
            y = int(origin[1] - r * np.sin(angle))  # vers le haut

            if x < 0 or x >= width or y < 0 or y >= height:
                break
            if binary[y, x] > 200:
                ray_distances.append(r)
                plt.plot([origin[0], x], [origin[1], y], color='blue')
                plt.scatter(x, y, color='red')
                hit = True
                break
        if not hit:
            ray_distances.append(max_length)
            x = int(origin[0] + max_length * np.cos(angle))
            y = int(origin[1] - max_length * np.sin(angle))
            plt.plot([origin[0], x], [origin[1], y], color='blue')

    plt.scatter(*origin, color='cyan')
    plt.axis("equal")
    plt.xlim(0, width)
    plt.ylim(height, 0)
    plt.show()

    return ray_distances

# Test
image_path = "car0_Raycast_frame2.png"
distances = simulate_rays_from_bottom_center(image_path, num_rays=15)
print("Distances des rayons :", distances)
