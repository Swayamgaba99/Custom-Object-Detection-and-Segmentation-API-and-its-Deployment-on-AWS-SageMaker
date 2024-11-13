# Custom Object Detection and Segmentation API and its Deployment on AWS SageMaker
This documentation provides a complete overview of the project, including the application's structure, code functionality, deployment in Docker, and instructions for deploying the Docker image to AWS ECR and creating an AWS SageMaker endpoint for inference.

## Project Overview
This project builds an API for object detection and segmentation using the Hugging Face Transformers and computer vision libraries. It allows for the segmentation of objects in images based on specified labels, applies mask refinements, and overlays segmented areas with a tiling effect using custom images based on the object category.

## 1. Application Files
### 1.1) app.py - This file contains the Flask application, handling the image processing, segmentation, and object detection.
### Imports
- Core libraries for image processing (torch, numpy, PIL, cv2, transformers).
- Flask for API handling.
- Custom utility classes and functions for bounding box manipulation, mask generation, and segmentation.

### Classes and Data Classes

#### 1. BoundingBox

##### Description: Defines the bounding box for detected objects.

##### Attributes:
- xmin: X-coordinate of the bounding box's top-left corner.
- ymin: Y-coordinate of the bounding box's top-left corner.
- xmax: X-coordinate of the bounding box's bottom-right corner.
- ymax: Y-coordinate of the bounding box's bottom-right corner.
##### Method:
- xyxy: Returns the bounding box in [xmin, ymin, xmax, ymax] format.
  
#### 2. DetectionResult

##### Description: Stores detection results with associated bounding boxes and optional segmentation masks.

##### Attributes:
- score: Confidence score for the detected object.
- label: Label of the detected object.
- box: Instance of BoundingBox containing the detected bounding box.
- mask: Optional mask of the detected object as a numpy array.
##### Method:
- from_dict: Converts a dictionary into a DetectionResult instance.
  

### Functions
- load_image: Loads an image from either a URL or a file path.
- refine_masks: Refines segmentation masks with an option for polygon refinement.
- mask_to_polygon: Converts a binary mask to a polygon representation using contours.
- polygon_to_mask: Converts a polygon representation back to a mask.
- detect: Uses a zero-shot object detection model to detect objects in an image based on specified labels.
- segment: Applies segmentation masks to detected objects.
- grounded_segmentation: Combines object detection and segmentation for full image processing.
- get_boxes: Extracts bounding boxes from detection results.
- numpy_to_base64: Encodes an image to Base64 format.
- tile_image: Tiles an image to fit specified dimensions.
- process_images_handler: Main function for handling image processing requests, used in API endpoints.
  
### API Endpoints

#### 1. /ping (GET)
- Description: Health check endpoint to verify that the API is running.
- Response: Returns a status 200 with the message Healthy.

#### /invocations (POST)
- Description: Primary endpoint for image processing. Accepts a JSON payload containing category information and image URLs, detects specified objects, segments them, fetches an appropriate product image, and overlays it onto the detected area.

**Request Payload:**

```json
{
  "categoryname": "Categoryname",
  "roomName": "RoomName",
  "images": [
    {
      "url": "url of image",
      "_id": "66d2cd2cc7341cafc78cadd2"
    }
  ]
}

{
  "processed_images": [
    "**Placeholder for Base64 Image 1**"
  ]
}
#### We can pass multiple images together in it as a list.
```
### 1.2) Dockerfile - Docker Configuration
- The Dockerfile defines the container environment, installs system and Python dependencies, and configures the Flask application to run with Gunicorn, a production-grade WSGI server.
- Base Image: The python:3.11-slim-buster image offers a minimal, efficient environment.
- System Dependencies: Libraries such as libgl1-mesa-glx and ffmpeg are required for OpenCV and image processing.
- Node.js Installation: Included for optional web service functionality, allowing for additional JavaScript-based interactions if necessary.
- Entrypoint: Specifies entrypoint.sh as the entry script, which configures Gunicorn for serving the app.

### 1.3) entrypoint.sh - Entrypoint Script
- The entrypoint script configures the Gunicorn server to run the Flask app on container startup.
- Configuration: Starts the Gunicorn server on port 8080 with a timeout of 3000 seconds for lengthy processing tasks.
- Command Execution: Executes any additional command passed as an argument (exec "$@"), allowing flexibility for custom commands during container initialization.

### 1.4) requirements.txt - Python Dependencies
Specifies all Python libraries required for image processing, web handling, data manipulation, and integration with the Hugging Face library.

## 2. Deployment on AWS SageMaker  
#### 1. Authenticate Docker to ECR repository.
```bash
aws ecr get-login-password --region <your-region> | docker login --username AWS --password-stdin <your-ecr-repository-uri>
```
#### 2. Build and Tag the Docker Image.
``` bash
docker build -t <repository-name> .
docker tag <repository-name>:latest <account-id>.dkr.ecr.<region>.amazonaws.com/<repository-name>:latest
```
#### 3. Push the Docker Image to ECR:
```bash
docker push <account-id>.dkr.ecr.<region>.amazonaws.com/<repository-name>:latest
```
## 3. Deploying the Model to AWS SageMaker

##### 3.1) Set Up IAM Role for SageMaker.
##### 3.2) Create a model from inferenece in sagemaker.
##### 3.3) Create the endpoint configuration specifying suitable instance and the model created.
##### 3.4) Create a SageMaker Model Endpoint.

## 4. API Usage
Once deployed, the SageMaker endpoint will accept HTTP POST requests with JSON payloads as specified. It will perform detection and segmentation on the input images and return processed images encoded in Base64 format.

## Conclusion 
This project provides a complete framework for creating a custom segmentation API, packaging it in a Docker image, and deploying it to SageMaker.






 

