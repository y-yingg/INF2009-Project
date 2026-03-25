import os
import cv2
import torch
from PIL import Image
from transformers import AutoProcessor, AutoModelForImageTextToText

MODEL_DIR = "models/SmolVLM-500M-Instruct"

def load_local_vlm():
    if not os.path.exists(MODEL_DIR):
        raise RuntimeError(
            f"Local model folder not found: {MODEL_DIR}\n"
            "Download it first with:\n"
            "huggingface-cli download HuggingFaceTB/SmolVLM-500M-Instruct --local-dir models/SmolVLM-500M-Instruct"
        )

    device = "cuda" if torch.cuda.is_available() else "cpu"
    dtype = torch.float16 if device == "cuda" else torch.float32

    print("[INFO] Loading local VLM. This may take a while...")
    processor = AutoProcessor.from_pretrained(MODEL_DIR, local_files_only=True)
    model = AutoModelForImageTextToText.from_pretrained(
        MODEL_DIR,
        torch_dtype=dtype,
        local_files_only=True,
        low_cpu_mem_usage=True,
    ).to(device)

    return processor, model, device

def capture_frame():
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    if not cap.isOpened():
        raise RuntimeError("Could not open camera.")

    print("\n[INFO] Camera opened.")
    print("[INFO] Press SPACE to capture the current scene.")
    print("[INFO] Press q to cancel.")

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                raise RuntimeError("Failed to read frame from camera.")

            display = frame.copy()
            cv2.putText(
                display,
                "SPACE = capture | q = cancel",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2
            )

            cv2.imshow("Offline VLM", display)
            key = cv2.waitKey(1) & 0xFF

            if key == ord(" "):
                print("[INFO] Captured frame.")
                return frame

            if key == ord("q"):
                return None
    finally:
        cap.release()
        cv2.destroyAllWindows()
def capture_frame():
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    if not cap.isOpened():
        raise RuntimeError("Could not open camera.")

    print("\n[INFO] Camera opened.")
    print("[INFO] Press SPACE to capture the current scene.")
    print("[INFO] Press q to cancel.")

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                raise RuntimeError("Failed to read frame from camera.")

            display = frame.copy()
            cv2.putText(
                display,
                "SPACE = capture | q = cancel",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2
            )

            cv2.imshow("Offline VLM", display)
            key = cv2.waitKey(1) & 0xFF

            if key == ord(" "):
                print("[INFO] Captured frame.")
                return frame

            if key == ord("q"):
                return None
    finally:
        cap.release()
        cv2.destroyAllWindows()

def ask_local_vlm(processor, model, device, frame_bgr, question):
    frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
    image = Image.fromarray(frame_rgb)

    messages = [
        {
            "role": "user",
            "content": [
                {"type": "image"},
                {"type": "text", "text": question}
            ]
        }
    ]

    prompt = processor.apply_chat_template(messages, add_generation_prompt=True)

    inputs = processor(
        text=prompt,
        images=[image],
        return_tensors="pt"
    )

    inputs = {k: v.to(device) for k, v in inputs.items()}

    with torch.no_grad():
        output_ids = model.generate(
            **inputs,
            max_new_tokens=120,
            do_sample=False
        )

    generated_text = processor.batch_decode(output_ids, skip_special_tokens=True)[0]

    # Try to remove the prompt if the model echoes it
    if "Assistant:" in generated_text:
        generated_text = generated_text.split("Assistant:", 1)[-1].strip()

    return generated_text.strip()

def main():
    processor, model, device = load_local_vlm()
    print("[OK] Offline VLM ready.")

    while True:
        question = input(
            "\nEnter your question for the scene\n"
            "(example: Is the person reading a book?)\n> "
        ).strip()

        if not question:
            print("[WARN] Question cannot be empty.")
            continue

        frame = capture_frame()

        if frame is None:
            again = input("\nNo scene analysed. Analyse another scene? (y/n): ").strip().lower()
            if again != "y":
                break
            continue

        print("[INFO] Running local VLM inference...")

        try:
            answer = ask_local_vlm(processor, model, device, frame, question)
        except Exception as e:
            print(f"[ERROR] Local VLM failed: {e}")
            again = input("\nAnalyse another scene? (y/n): ").strip().lower()
            if again != "y":
                break
            continue

        print("\n===== OFFLINE VLM ANSWER =====")
        print(f"Question: {question}")
        print(f"Answer:   {answer}")
        print("================================")

        again = input("\nAnalyse another scene? (y/n): ").strip().lower()
        if again != "y":
            break

    print("[DONE] Exiting.")

if __name__ == "__main__":
    main()
