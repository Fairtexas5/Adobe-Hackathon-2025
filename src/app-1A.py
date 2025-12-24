import cv2
import torch
from doclayout_yolo import YOLOv10

# Load model
model = YOLOv10("models/last.pt")

# Input image path
img_path = "/Users/adityasingh/Desktop/ejbfe.png"
img = cv2.imread(img_path)

# Run prediction
det_res = model.predict(
    img_path,
    imgsz=1024,
    conf=0.2,
    device="cpu"
)

# Get first result
result = det_res[0]
boxes = result.boxes

# Extract data
bbox_list = boxes.xyxy.cpu().numpy()
class_ids = boxes.cls.cpu().numpy().astype(int)
confidences = boxes.conf.cpu().numpy()
id2label = model.model.names

# Draw on image
for i in range(len(bbox_list)):
    x1, y1, x2, y2 = map(int, bbox_list[i])
    label = id2label[class_ids[i]]
    conf = confidences[i]

    # Draw rectangle
    cv2.rectangle(img, (x1, y1), (x2, y2), color=(0, 255, 0), thickness=2)

    # Draw label
    text = f"{label} ({conf:.2f})"
    cv2.putText(img, text, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX,
                0.4, (0, 0, 255), 1, lineType=cv2.LINE_AA)

output_path = "./output/annotated_result3.jpg"
cv2.imwrite(output_path, img)
print(f"Saved annotated image to {output_path}")
