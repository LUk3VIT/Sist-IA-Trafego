from ultralytics import YOLO
import cv2
import tkinter as tk
from tkinter import filedialog
import sys
from datetime import datetime
import os

# Carrega o modelo pré-treinado
model = YOLO('yolov8n.pt')

LOG_FILE = os.path.join(os.path.dirname(__file__), "detections_log.txt")

while True:
    # Janela simples para escolher o video
    root = tk.Tk()
    root.title("Selecionar video para análise")
    root.geometry("300x100")
    root.resizable(False, False)

    def escolher_arquivo():
        path = filedialog.askopenfilename(
            title="Selecione o arquivo de video",
            filetypes=[("Arquivos de video", "*.mp4 *.avi *.mov *.mkv"), ("Todos os arquivos", "*")]
        )
        if path:
            root.selected_file = path
            root.destroy()

    btn = tk.Button(root, text="Selecionar video", command=escolher_arquivo)
    btn.pack(expand=True)
    root.selected_file = None
    root.mainloop()

    video_path = getattr(root, "selected_file", None)
    try:
        root.destroy()
    except:
        pass

    if not video_path:
        print("Nenhum arquivo selecionado. Saindo.")
        break

    # Verifica extensão do arquivo
    ext = os.path.splitext(video_path)[1].lower()
    if ext in (".jpg", ".jpeg", ".png", ".bmp", ".tiff"):
        # Trata como imagem estática (mantendo chat/controle semelhante ao vídeo)
        img = cv2.imread(video_path)
        if img is None:
            append_and_log = None  # ...existing code fallback...
            print("Erro ao abrir a imagem.")
            with open(LOG_FILE, "a", encoding="utf-8") as f:
                f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Erro ao abrir a imagem: {video_path}\n")
            continue

        # Roda a detecção uma vez
        results = model(img)
        annotated = results[0].plot() if len(results) > 0 else img

        # Janela de controle com chat semelhante ao vídeo
        control = tk.Tk()
        control.title("Controles da Imagem")
        control.geometry("420x320")
        control.resizable(False, False)
        cancel = {"stop": False, "return": False}

        # Text widget (chat) com scrollbar
        txt_frame = tk.Frame(control)
        txt_frame.pack(fill="both", expand=True, padx=5, pady=(5,0))

        scrollbar = tk.Scrollbar(txt_frame)
        scrollbar.pack(side="right", fill="y")

        chat = tk.Text(txt_frame, wrap="word", height=12, yscrollcommand=scrollbar.set, state="disabled")
        chat.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=chat.yview)

        # Função para inserir mensagem no chat e gravar no arquivo
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
            try:
                with open(LOG_FILE, "a", encoding="utf-8") as f:
                    f.write(line)
            except:
                pass

        # Botões: manter chat ou fechar tudo e voltar
        def cancelar_imagem():
            cancel["stop"] = True
            append_and_log("Visualização interrompida pelo usuário (chat permanece).")

        def fechar_tudo_e_voltar():
            cancel["return"] = True
            append_and_log("Fechando chat e retornando à seleção de arquivos.")
            try:
                control.destroy()
            except:
                pass
            try:
                cv2.destroyWindow(winname)
            except:
                pass

        btn_cancel = tk.Button(control, text="Cancelar (manter chat)", command=cancelar_imagem)
        btn_cancel.pack(fill="x", padx=10, pady=(8,2))

        btn_close_all = tk.Button(control, text="Fechar tudo e voltar", command=fechar_tudo_e_voltar)
        btn_close_all.pack(fill="x", padx=10, pady=(0,8))

        # Log inicial e mensagens baseadas nas detecções (mensagens claras)
        append_and_log(f"Iniciando análise da imagem: {video_path}")
        if len(results) > 0:
            for r in results:
                for box in r.boxes:
                    cls = int(box.cls[0])
                    if cls == 0:
                        append_and_log("Identifiquei uma pessoa.")
                    elif cls == 9:
                        append_and_log("Identifiquei um semáforo.")
                    else:
                        append_and_log(f"Identifiquei objeto classe {cls}.")
        else:
            append_and_log("Nenhuma detecção encontrada na imagem.")

        # Mostra a imagem anotada
        winname = "Detecção Inteligente - Imagem"
        cv2.imshow(winname, annotated)

        # Loop interativo: mantém o chat responsivo e espera ação do usuário
        try:
            import time
        except:
            pass

        while True:
            # Processa eventos Tkinter (mantém o chat responsivo)
            try:
                control.update()
            except tk.TclError:
                # control fechado manualmente -> considerar retorno
                cancel["return"] = True

            # Verifica flags
            if cancel.get("stop", False):
                append_and_log("Visualização pausada pelo usuário. Chat permanece aberto.")
                break
            if cancel.get("return", False):
                append_and_log("Retornando à seleção de arquivos.")
                break

            # 'q' ou fechamento da janela OpenCV fecha a visualização
            if cv2.waitKey(100) & 0xFF == ord("q"):
                append_and_log("Usuário pressionou 'q' — retornando à seleção.")
                break
            try:
                if cv2.getWindowProperty(winname, cv2.WND_PROP_VISIBLE) < 1:
                    append_and_log("Janela da imagem fechada — retornando à seleção.")
                    break
            except:
                break

            time.sleep(0.05)

        # Fecha a janela da imagem (se ainda aberta)
        try:
            cv2.destroyWindow(winname)
        except:
            pass

        # Se o usuário pediu apenas cancelar (manter chat), aguarda o fechamento pelo botão "Fechar tudo e voltar"
        if not cancel.get("return", False):
            append_and_log("Aguardando ação do usuário: clique 'Fechar tudo e voltar' para escolher outro arquivo.")
            while True:
                try:
                    control.update()
                except tk.TclError:
                    break
                if cancel.get("return", False):
                    break
                time.sleep(0.05)

        # Fecha control (se não fechado) e volta para seleção
        try:
            control.destroy()
        except:
            pass

        append_and_log("Retornando para seleção de arquivo...")
        continue

    # Captura de vídeo (arquivo escolhido)
    cap = cv2.VideoCapture(video_path)

    # Janela de controle com botão para cancelar o vídeo atual + chat de logs
    control = tk.Tk()
    control.title("Controles do Vídeo")
    control.geometry("420x300")
    control.resizable(False, False)
    cancel = {"stop": False}

    # Text widget (chat) com scrollbar
    txt_frame = tk.Frame(control)
    txt_frame.pack(fill="both", expand=True, padx=5, pady=(5,0))

    scrollbar = tk.Scrollbar(txt_frame)
    scrollbar.pack(side="right", fill="y")

    chat = tk.Text(txt_frame, wrap="word", height=10, yscrollcommand=scrollbar.set, state="disabled")
    chat.pack(side="left", fill="both", expand=True)
    scrollbar.config(command=chat.yview)

    # Função para inserir mensagem no chat e gravar no arquivo
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
        try:
            with open(LOG_FILE, "a", encoding="utf-8") as f:
                f.write(line)
        except:
            pass

    # Botão cancelar
    def cancelar_video():
        cancel["stop"] = True
        try:
            control.destroy()
        except:
            pass

    btn_cancel = tk.Button(control, text="Cancelar vídeo e voltar", command=cancelar_video)
    btn_cancel.pack(fill="x", padx=10, pady=8)

    # Exibe caminho do vídeo no chat no início
    append_and_log(f"Iniciando análise do vídeo: {video_path}")

    try:
        while True:
            if not cap.isOpened():
                append_and_log("Erro ao abrir vídeo/câmera.")
                break

            success, frame = cap.read()
            if not success:
                append_and_log("Fim do vídeo ou frame não lido.")
                break

            # Roda a detecção
            results = model(frame)

            for r in results:
                for box in r.boxes:
                    # Pegar a classe do objeto (0 é pessoa, 9 é semáforo no dataset COCO)
                    cls = int(box.cls[0])
                    if cls == 0:
                        append_and_log("Pedestre detectado!")
                    elif cls == 9:
                        append_and_log("Semáforo detectado! Iniciando análise de cor...")
                        # Aqui extrair coordenadas do semáforo (box.xyxy) e usar OpenCV para a cor

            # Visualizar o resultado se houver
            if len(results) > 0:
                annotated_frame = results[0].plot()
                cv2.imshow("Detecção Inteligente", annotated_frame)
            else:
                cv2.imshow("Detecção Inteligente", frame)

            # Processa eventos da janela de controle Tkinter (não bloquear)
            try:
                control.update()
            except tk.TclError:
                # Se a janela foi fechada manualmente, considerar cancelamento
                cancel["stop"] = True

            # Se botão de cancelar foi clicado, sai da reprodução atual
            if cancel["stop"]:
                append_and_log("Análise cancelada pelo usuário. Retornando à seleção.")
                break

            # Tecla 'q' também encerra a reprodução atual
            if cv2.waitKey(1) & 0xFF == ord("q"):
                append_and_log("Encerrado com 'q'. Retornando à seleção de vídeo.")
                break
    finally:
        cap.release()
        cv2.destroyAllWindows()
        try:
            control.destroy()
        except:
            pass

    append_and_log("Retornando para seleção de vídeo...")