import cv2 as cv
import numpy as np
import os

cap = cv.VideoCapture(0)
whT = 320
confThreshold = 0.5
nmsThreshold = 0.2

#### LOAD MODEL
base_path = os.path.dirname(os.path.abspath(__file__))
classesFile = os.path.join(base_path, "coco.names")
model_pairs = [
    ("yolov3-tiny.cfg", "yolov3-tiny.weights"),
    ("yolov3.cfg", "yolov3.weights"),
]
modelConfiguration = None
modelWeights = None

classNames = []
if os.path.exists(classesFile):
    with open(classesFile, 'rt') as f:
        classNames = f.read().rstrip('\n').split('\n')
else:
    print(f"File {classesFile} tidak dijumpai. Sila pastikan file ini wujud dalam folder yang sama dengan skrip.")
    exit(1)

for cfg_name, weights_name in model_pairs:
    cfg_path = os.path.join(base_path, cfg_name)
    weights_path = os.path.join(base_path, weights_name)
    if os.path.exists(cfg_path) and os.path.exists(weights_path):
        modelConfiguration = cfg_path
        modelWeights = weights_path
        break

if not (modelConfiguration and modelWeights):
    print("Fail konfigurasi atau berat model tidak dijumpai. Sila pastikan kedua-dua fail ini wujud.")
    exit(1)

net = cv.dnn.readNetFromDarknet(modelConfiguration, modelWeights)
net.setPreferableBackend(cv.dnn.DNN_BACKEND_OPENCV)
net.setPreferableTarget(cv.dnn.DNN_TARGET_CPU)

def findObjects(outputs, img):
    hT, wT, cT = img.shape
    bbox = []
    classIds = []
    confs = []
    for output in outputs:
        for det in output:
            scores = det[5:]
            classId = np.argmax(scores)
            confidence = scores[classId]
            if confidence > confThreshold:
                w, h = int(det[2]*wT), int(det[3]*hT)
                x, y = int((det[0]*wT)-w/2), int((det[1]*hT)-h/2)
                bbox.append([x, y, w, h])
                classIds.append(classId)
                confs.append(float(confidence))

    indices = cv.dnn.NMSBoxes(bbox, confs, confThreshold, nmsThreshold)

    for i in indices:
        i = i[0] if isinstance(i, (list, np.ndarray)) else i
        box = bbox[i]
        x, y, w, h = box[0], box[1], box[2], box[3]
        cv.rectangle(img, (x, y), (x+w, y+h), (255, 0, 255), 2)
        cv.putText(img, f'{classNames[classIds[i]].upper()} {int(confs[i]*100)}%',
                   (x, y-10), cv.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 255), 2)

while True:
    success, img = cap.read()
    if not success:
        print("Kamera tidak dapat diakses.")
        break
    blob = cv.dnn.blobFromImage(img, 1 / 255, (whT, whT), [0, 0, 0], 1, crop=False)
    net.setInput(blob)
    layersNames = net.getLayerNames()
    output_layers = net.getUnconnectedOutLayers()
    # Fix for OpenCV 3.x and 4.x compatibility
    if len(output_layers.shape) == 2:
        outputNames = [layersNames[i[0] - 1] for i in output_layers]
    else:
        outputNames = [layersNames[i - 1] for i in output_layers]
    outputs = net.forward(outputNames)
    findObjects(outputs, img)

    cv.imshow('Image', img)
    if cv.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv.destroyAllWindows()
