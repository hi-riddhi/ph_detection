import cv2
import numpy as np
import os
import csv
import math

# ========== Calibration Section ========== #

ref_points = []
img_copy = None

def click_event(event, x, y, flags, param):
    global ref_points, img_copy
    if event == cv2.EVENT_LBUTTONDOWN:
        ref_points.append((x, y))
        cv2.circle(img_copy, (x, y), 5, (0, 255, 0), -1)
        cv2.imshow("Select Two Points", img_copy)

        if len(ref_points) == 2:
            cv2.line(img_copy, ref_points[0], ref_points[1], (255, 0, 0), 2)
            cv2.imshow("Select Two Points", img_copy)

            px_distance = math.dist(ref_points[0], ref_points[1])
            print(f"Pixel distance between selected points: {px_distance:.2f} pixels")

            real_cm = float(input("Enter the real-world distance between the points (in cm): "))
            ratio = px_distance / real_cm
            print(f"Estimated pixel-to-cm ratio: {ratio:.4f} pixels/cm")
            cv2.destroyAllWindows()

            global pixel_to_cm_ratio
            pixel_to_cm_ratio = ratio

#def calibrate_image(image_path):



# ========== Pothole Detection Section ========== #

def detect_potholes_with_size(image_path, output_dir='outputs/', min_area=500, pixel_to_cm_ratio=None):
    image = cv2.imread(image_path)
    orig = image.copy()
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Blur and Edge Detection
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blurred, 30, 100)

    # Morphological operations
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    dilated = cv2.dilate(edges, kernel, iterations=2)

    # Find contours
    contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    pothole_info = []
    pothole_count = 0

    for contour in contours:
        area = cv2.contourArea(contour)
        if area > min_area:
            pothole_count += 1
            x, y, w, h = cv2.boundingRect(contour)
            cv2.rectangle(orig, (x, y), (x + w, y + h), (0, 0, 255), 2)

            area_cm = (area / (pixel_to_cm_ratio**2)) if pixel_to_cm_ratio else None
            label = f'Pothole {pothole_count}'
            size_label = f"{area:.0f}px" if not area_cm else f"{area_cm:.2f}cm²"

            cv2.putText(orig, f"{label} - {size_label}", (x, y - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 1)

            pothole_info.append({
                'pothole_id': pothole_count,
                'area_pixels': round(area),
                'area_cm2': round(area_cm, 2) if area_cm else None,
                'bounding_box': (x, y, w, h)
            })

    # Save image and CSV
    os.makedirs(output_dir, exist_ok=True)
    out_path = os.path.join(output_dir, os.path.basename(image_path))
    cv2.imwrite(out_path, orig)

    csv_out = os.path.join(output_dir, os.path.splitext(os.path.basename(image_path))[0] + "_data.csv")
    with open(csv_out, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['pothole_id', 'area_pixels', 'area_cm2', 'bounding_box'])
        writer.writeheader()
        writer.writerows(pothole_info)

    print(f"Detected {pothole_count} potholes in {image_path}")
    return pothole_info


# ========== Main Script Section ========== #

if __name__ == "__main__":
    input_folder = 'input_images/'
    output_folder = 'outputs/'

    image_files = [f for f in os.listdir(input_folder) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
    if not image_files:
        print("No images found in the input folder.")
        exit()

    # Ask user if they want to calibrate
    first_image = os.path.join(input_folder, image_files[0])
    print(f"\nFirst image for calibration: {first_image}")
    use_calibration = input("Do you want to calibrate using this image? (y/n): ").strip().lower()

    if use_calibration == 'y':
        ratio = calibrate_image(first_image)
    else:
        ratio = float(input("Enter known pixel-to-cm ratio manually: "))

    # Process all images
    for file in image_files:
        detect_potholes_with_size(os.path.join(input_folder, file),
                                  output_dir=output_folder,
                                  pixel_to_cm_ratio=ratio)
