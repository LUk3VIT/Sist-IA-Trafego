from ultralytics import YOLO
import cv2
import tkinter as tk
from tkinter import filedialog
from datetime import datetime
import os
import time

model = YOLO('best.pt')

LOG_FILE = os.path.join(os.path.dirname(__file__), "detections_log.txt")

DETECTION_COOLDOWN = 3
last_seen = {}

def save_log(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {message}\n"

    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line)
    except:
        pass

while True:

    root = tk.Tk()
    root.title("Selecionar arquivo")
    root.geometry("300x100")
    root.resizable(False, False)

    def escolher_arquivo():
        path = filedialog.askopenfilename(
            title="Selecione imagem ou vídeo",
            filetypes=[
                ("Arquivos suportados", "*.mp4 *.avi *.mov *.mkv *.jpg *.jpeg *.png *.bmp *.tiff"),
                ("Todos os arquivos", "*")
            ]
        )

        if path:
            root.selected_file = path
            root.destroy()

    btn = tk.Button(root, text="Selecionar arquivo", command=escolher_arquivo)
    btn.pack(expand=True)

    root.selected_file = None
    root.mainloop()

    video_path = getattr(root, "selected_file", None)

    try:
        root.destroy()
    except:
        pass

    if not video_path:
        print("Nenhum arquivo selecionado.")
        break

    ext = os.path.splitext(video_path)[1].lower()

    is_image = ext in (
        ".jpg",
        ".jpeg",
        ".png",
        ".bmp",
        ".tiff"
    )

    control = tk.Tk()
    control.title("Painel de Controle")
    control.geometry("500x420")
    control.resizable(False, False)

    cancel = {
        "stop": False,
        "return": False
    }

    chat_frame = tk.Frame(control)
    chat_frame.pack(fill="both", expand=True, padx=5, pady=(5, 0))

    scrollbar = tk.Scrollbar(chat_frame)
    scrollbar.pack(side="right", fill="y")

    chat = tk.Text(
        chat_frame,
        wrap="word",
        height=10,
        yscrollcommand=scrollbar.set,
        state="disabled"
    )

    chat.pack(side="left", fill="both", expand=True)
    scrollbar.config(command=chat.yview)

    signs_label = tk.Label(
        control,
        text="Placas detectadas",
        font=("Arial", 10, "bold")
    )

    signs_label.pack(pady=(10, 0))

    signs_frame = tk.Frame(control)
    signs_frame.pack(fill="both", expand=False, padx=5, pady=5)

    signs_scroll = tk.Scrollbar(signs_frame)
    signs_scroll.pack(side="right", fill="y")

    signs_listbox = tk.Listbox(
        signs_frame,
        height=8,
        yscrollcommand=signs_scroll.set
    )

    signs_listbox.pack(side="left", fill="both", expand=True)
    signs_scroll.config(command=signs_listbox.yview)

    def append_and_log(message: str):

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        line = f"[{timestamp}] {message}\n"

        try:
            chat.config(state="normal")
            chat.insert("end", line)
            chat.see("end")
            chat.config(state="disabled")
        except:
            pass

        save_log(message)

    def cancelar_analise():
        cancel["stop"] = True

    def fechar_tudo_e_voltar():
        cancel["return"] = True

        try:
            control.destroy()
        except:
            pass

        try:
            cv2.destroyAllWindows()
        except:
            pass

    btn_cancel = tk.Button(
        control,
        text="Cancelar análise",
        command=cancelar_analise
    )

    btn_cancel.pack(fill="x", padx=10, pady=(5, 2))

    btn_return = tk.Button(
        control,
        text="Fechar tudo e voltar",
        command=fechar_tudo_e_voltar
    )

    btn_return.pack(fill="x", padx=10, pady=(0, 10))

    if is_image:

        img = cv2.imread(video_path)

        if img is None:
            append_and_log("Erro ao abrir imagem.")
            continue

        append_and_log(f"Analisando imagem: {video_path}")
        results = model(img)

        for r in results:

            for box in r.boxes:

                cls = int(box.cls[0])
                conf = float(box.conf[0])

                label = model.names[cls]

                message = f"{label} ({conf:.2f})"

                append_and_log(f"Placa detectada: {message}")

                signs_listbox.insert(
                    tk.END,
                    f"{datetime.now().strftime('%H:%M:%S')} - {message}"
                )

        annotated = results[0].plot()
        window_name = "Detecção Inteligente"
        cv2.imshow(window_name, annotated)

        while True:

            try:
                control.update()
            except tk.TclError:
                break

            if cancel["stop"]:
                append_and_log("Análise cancelada.")
                break

            if cancel["return"]:
                break

            if cv2.waitKey(100) & 0xFF == ord("q"):
                append_and_log("Encerrado com tecla Q.")
                break

            try:
                if cv2.getWindowProperty(window_name, cv2.WND_PROP_VISIBLE) < 1:
                    break
            except:
                break

            time.sleep(0.05)

        try:
            cv2.destroyAllWindows()
        except:
            pass

        try:
            control.destroy()
        except:
            pass

        continue

    cap = cv2.VideoCapture(video_path)

    append_and_log(f"Iniciando análise do vídeo: {video_path}")

    try:

        while True:

            if not cap.isOpened():
                append_and_log("Erro ao abrir vídeo.")
                break

            success, frame = cap.read()

            if not success:
                append_and_log("Fim do vídeo.")
                break

            results = model(frame)

            for r in results:

                for box in r.boxes:

                    cls = int(box.cls[0])
                    conf = float(box.conf[0])

                    label = model.names[cls]

                    current_time = time.time()

                    if label not in last_seen:
                        last_seen[label] = 0

                    if current_time - last_seen[label] >= DETECTION_COOLDOWN:

                        last_seen[label] = current_time

                        message = f"{label} ({conf:.2f})"

                        append_and_log(
                            f"Placa detectada: {message}"
                        )

                        signs_listbox.insert(
                            tk.END,
                            f"{datetime.now().strftime('%H:%M:%S')} - {message}"
                        )

                        signs_listbox.see(tk.END)

                        try:

                            x1, y1, x2, y2 = map(
                                int,
                                box.xyxy[0]
                            )

                            crop = frame[y1:y2, x1:x2]

                            screenshots_dir = os.path.join(
                                os.path.dirname(__file__),
                                "detections"
                            )

                            os.makedirs(
                                screenshots_dir,
                                exist_ok=True
                            )

                            filename = f"{label}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"

                            save_path = os.path.join(
                                screenshots_dir,
                                filename
                            )

                            cv2.imwrite(save_path, crop)

                        except:
                            pass

            annotated_frame = results[0].plot()

            cv2.imshow(
                "Detecção Inteligente",
                annotated_frame
            )

            try:
                control.update()
            except tk.TclError:
                cancel["stop"] = True

            if cancel["stop"]:
                append_and_log("Análise cancelada pelo usuário.")
                break

            if cancel["return"]:
                break

            if cv2.waitKey(1) & 0xFF == ord("q"):
                append_and_log("Encerrado com tecla Q.")
                break

    finally:

        cap.release()

        try:
            cv2.destroyAllWindows()
        except:
            pass

        try:
            control.destroy()
        except:
            pass

    append_and_log("Retornando para seleção de arquivo...")