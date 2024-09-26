import torch
import numpy as np
from PIL import Image
from transformers import AutoModelForMaskGeneration, AutoProcessor, pipeline
import requests
from typing import List, Tuple, Union, Optional, Dict, Any
import cv2
from dataclasses import dataclass
import json
import matplotlib.pyplot as plt
from flask import Flask, request, jsonify
import base64

app = Flask(__name__)

class BoundingBox:
    def __init__(self, xmin, ymin, xmax, ymax): 
        self.xmin = xmin
        self.ymin = ymin
        self.xmax = xmax
        self.ymax = ymax
    xmin: int
    ymin: int
    xmax: int
    ymax: int

    @property
    def xyxy(self) -> List[float]:
        return [self.xmin, self.ymin, self.xmax, self.ymax]
@dataclass
class DetectionResult:
    score: float
    label: str
    box: BoundingBox
    mask: Optional[np.array] = None

    @classmethod
    def from_dict(cls, detection_dict: Dict) -> 'DetectionResult':
        return cls(score=detection_dict['score'],
                   label=detection_dict['label'],
                   box=BoundingBox(xmin=detection_dict['box']['xmin'],
                                   ymin=detection_dict['box']['ymin'],
                                   xmax=detection_dict['box']['xmax'],
                                   ymax=detection_dict['box']['ymax']))
def load_image(image_str: str) -> Image.Image:
    if image_str.startswith("http"):
        image = Image.open(requests.get(image_str, stream=True).raw).convert("RGB")
    else:
        image = Image.open(image_str).convert("RGB")
    return image

# This function aims to enhance the quality of the image generated by the segmentation model
def refine_masks(masks: torch.BoolTensor, polygon_refinement: bool = False) -> List[np.ndarray]:
    masks = masks.cpu().float()
    masks = masks.permute(0, 2, 3, 1)
    masks = masks.mean(axis=-1)
    masks = (masks > 0).int()
    masks = masks.numpy().astype(np.uint8)
    masks = list(masks)

    if polygon_refinement:
        for idx, mask in enumerate(masks):
            shape = mask.shape
            polygon = mask_to_polygon(mask)
            mask = polygon_to_mask(polygon, shape)
            masks[idx] = mask

    return masks

# Converts a mask to a polygon representation.
def mask_to_polygon(mask: np.ndarray) -> List[List[int]]:
    contours, _ = cv2.findContours(mask.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    largest_contour = max(contours, key=cv2.contourArea)
    polygon = largest_contour.reshape(-1, 2).tolist()
    return polygon

# Converts a polygon to a mask representation.
def polygon_to_mask(polygon: List[Tuple[int, int]], image_shape: Tuple[int, int]) -> np.ndarray:
    mask = np.zeros(image_shape, dtype=np.uint8)
    pts = np.array(polygon, dtype=np.int32)
    cv2.fillPoly(mask, [pts], color=(255,))
    return mask

# Detects objects in an image using a zero-shot object detection model (Grounding DINO).
def detect(image: Image.Image, labels: List[str], threshold: float = 0.3, detector_id: Optional[str] = None) -> List[Dict[str, Any]]:
    device = "cuda" if torch.cuda.is_available() else "cpu"
    detector_id = detector_id if detector_id is not None else "IDEA-Research/grounding-dino-tiny"
    object_detector = pipeline(model=detector_id, task="zero-shot-object-detection", device=device)

    labels = [label if label.endswith(".") else label + "." for label in labels]

    results = object_detector(image, candidate_labels=labels, threshold=threshold)
    results = [DetectionResult.from_dict(result) for result in results]

    return results

# Segments detected objects using a segmentation model (SAM).
def segment(image: Image.Image, detection_results: List[Dict[str, Any]], polygon_refinement: bool = False, segmenter_id: Optional[str] = None) -> List[DetectionResult]:
    device = "cuda" if torch.cuda.is_available() else "cpu"
    segmenter_id = segmenter_id if segmenter_id is not None else "facebook/sam-vit-base"

    segmentator = AutoModelForMaskGeneration.from_pretrained(segmenter_id).to(device)
    processor = AutoProcessor.from_pretrained(segmenter_id)

    boxes = get_boxes(detection_results)
    inputs = processor(images=image, input_boxes=boxes, return_tensors="pt").to(device)

    outputs = segmentator(**inputs)
    masks = processor.post_process_masks(
        masks=outputs.pred_masks,
        original_sizes=inputs.original_sizes,
        reshaped_input_sizes=inputs.reshaped_input_sizes
    )[0]

    masks = refine_masks(masks, polygon_refinement)

    for detection_result, mask in zip(detection_results, masks):
        detection_result.mask = mask

    return detection_results

# Combines detection and segmentation for grounded segmentation.
def grounded_segmentation(image: Union[Image.Image, str], labels: List[str], threshold: float = 0.3, polygon_refinement: bool = False, detector_id: Optional[str] = None, segmenter_id: Optional[str] = None) -> Tuple[np.ndarray, List[DetectionResult]]:
    if isinstance(image, str):
        image = load_image(image)

    detections = detect(image, labels, threshold, detector_id)
    detections = segment(image, detections, polygon_refinement, segmenter_id)

    return np.array(image), detections

#  Extracts bounding boxes from detection results.
def get_boxes(results: DetectionResult) -> List[List[float]]:
    boxes = []
    for result in results:
        xyxy = result.box.xyxy
        boxes.append(xyxy)
    return [boxes]

def numpy_to_base64(image_array):

    # Convert the image array to a BGR format (if necessary)
    if image_array.shape[-1] == 3:
        image_array = cv2.cvtColor(image_array, cv2.COLOR_RGB2BGR)

    _, encoded_image = cv2.imencode('.jpg', image_array)

    # Convert the encoded image to Base64
    base64_string = base64.b64encode(encoded_image).decode('utf-8')

    return base64_string

@app.route('/process_images', methods=['POST'])
def process_images():
    json_data=request.get_json()
    if json_data is None:
      return jsonify({'error': 'No JSON data provided'}), 400
    
    categoryname = json_data.get('categoryname')
    if categoryname is None:
        return jsonify({'error': 'Category name is not provided'}), 400
    categoryname=categoryname.capitalize()

    image_urls = []
    for image in json_data.get('images', []):
      image_url = image.get('url')
      if image_url:
          image_urls.append(image_url)

    labels = [f"{categoryname}."]  
    threshold = 0.3

    detector_id = "IDEA-Research/grounding-dino-tiny"
    segmenter_id = "facebook/sam-vit-base"
    processed_image=[]
    for i in image_urls:
        image_array, detections = grounded_segmentation(image=i, labels=labels, threshold=threshold, polygon_refinement=True, detector_id=detector_id, segmenter_id=segmenter_id)

        img=image_array

        for detection in detections: 
            m=detection.mask
            try:
                url=f"https://newbackend.ayatrio.com/api/fetchProductsByCategory/{categoryname}"
                response = requests.get(url)
                response.raise_for_status() 
                data=json.loads(response.text)
                product_image_url=data[0]['productImages'][0]['images'][0]
                product_response = requests.get(product_image_url, stream=True)
                product_response.raise_for_status()
                new_image = np.frombuffer(product_response.content, np.uint8)
                new_image=cv2.cvtColor(new_image,cv2.COLOR_BGR2RGB)
                x, y, w, h = cv2.boundingRect(m.astype(np.uint8))
                resized_new_image=cv2.resize(new_image,(w,h))
                img[y:y+h, x:x+w] = np.where(m[y:y+h, x:x+w, np.newaxis], resized_new_image, img[y:y+h, x:x+w])
            except Exception as e:
                print(e)
            base64_encoded_image1=numpy_to_base64(img)
            processed_image.append(base64_encoded_image1)
    return jsonify({'processed_image1': processed_image[0], 'processed_image2':processed_image[1]})
    
if __name__ == '__main__':
  app.run(debug=True, port=5000)