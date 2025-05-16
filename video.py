import depthai as dai
import cv2

pipeline = dai.Pipeline()

cam_rgb = pipeline.create(dai.node.ColorCamera)
cam_rgb.setPreviewSize(1280, 720)
cam_rgb.setInterleaved(False)
cam_rgb.setColorOrder(dai.ColorCameraProperties.ColorOrder.BGR)
xout_rgb = pipeline.create(dai.node.XLinkOut)
xout_rgb.setStreamName("rgb")
cam_rgb.preview.link(xout_rgb.input)
try:
    with dai.Device(pipeline) as device:
        print("Connexion à la caméra OAK-D Lite réussie")
        q_rgb = device.getOutputQueue(name="rgb", maxSize=4, blocking=False)
        while True:
            in_rgb = q_rgb.get()
            frame = in_rgb.getCvFrame()
            cv2.imshow("OAK-D Lite RGB", frame)
            if cv2.waitKey(1) == ord('q'):
                break
except Exception as e:
    print(f"Erreur : {e}")
finally:
    cv2.destroyAllWindows()
    print("Flux vidéo arrêté")