from ultralytics import YOLO
import cv2

# Carrega o modelo pré-treinado
model = YOLO('yolov8n.pt') 

# Captura de vídeo (pode ser um arquivo ou a webcam)
cap = cv2.VideoCapture('semafaro.mp4')

try:
    while True:
        if not cap.isOpened():
            print("Erro ao abrir vídeo/câmera.")
            break

        success, frame = cap.read()
        if not success:
            print("Fim do vídeo ou frame não lido.")
            break

        # Roda a detecção
        results = model(frame)

        for r in results:
            for box in r.boxes:
                # Pegar a classe do objeto (0 é pessoa, 9 é semáforo no dataset COCO)
                cls = int(box.cls[0])
                if cls == 0:
                    print("Pedestre detectado!")
                elif cls == 9:
                    print("Semáforo detectado! Iniciando análise de cor...")
                    # Aqui extrair coordenadas do semáforo (box.xyxy) e usar OpenCV para a cor

        # Visualizar o resultado se houver
        if len(results) > 0:
            annotated_frame = results[0].plot()
            cv2.imshow("Detecção Inteligente", annotated_frame)
        else:
            cv2.imshow("Detecção Inteligente", frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break
finally:
    cap.release()
    cv2.destroyAllWindows()