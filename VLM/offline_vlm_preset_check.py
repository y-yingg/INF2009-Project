import os
import cv2
import torch
from PIL import Image
from transformers import AutoProcessor, AutoModelForImageTextToText

MODEL_DIR = "models/SmolVLM-500M-Instruct"

PRESET_QUESTIONS = {
    "1": {
        "label": "check if studying/reading",
        "question": (
            "Look at the person in the image. "
            "Are they studying or reading? "
            "Answer in exactly this format:\n"
            "Answer: yes/no/unclear\n"
            "Reason: <short reason>"
        ),
    },
    "2": {
        "label": "check if using phone/computer",
        "question": (
            "Look at the person in the image. "
            "Are they using a phone or computer? "
            "Answer in exactly this format:\n"
            "Answer: yes/no/unclear\n"
            "Reason: <short reason>"
        ),
    },
    "3": {
        "label": "check if in distress",
        "question": (
            "Look at the person in the image. "
            "Does the person appear to be in distress? "
            "Answer in exactly this format:\n"
            "Answer: yes/no/unclear\n"
            "Reason: <short reason>"
        ),
    },
    "4": {
        "label": "check if sleeping",
        "question": (
            "Look at the person in the image. "
            "Does the person appear to be sleeping? "
            "Answer in exactly this format:\n"
            "Answer: yes/no/unclear\n"
            "Reason: <short reason>"
        ),
    },
    "5": {
        "label": "check if eating",
        "question": (
            "Look at the person in the image. "
            "Does the person appear to be eating? "
            "Answer in exactly this format:\n"
            "Answer: yes/no/unclear\n"
            "Reason: <short reason>"
        ),
    },


  "6": {
        "label": "check if injured",
        "question": (
            "Look at the person in the image. "
            "Does the person appear to be injured or have fell down? "
            "Answer in exactly this format:\n"
            "Answer: yes/no/unclear\n"
            "Reason: <short reason>"
        ),
    },


    "7": {
        "label": "rank most likely activity within the above 6 options",
        "question": (
            "Look at the main person in the image. "
            "Estimate how likely each of the following activities is: "
            "falling, sleeping, studying, reading, using phone, using computer, eating, playing, none of the above. "
            "Give a score from 0 to 100 for each activity. "
            "Then choose the single most likely activity. "
            "Answer in exactly this format:\n"
            "Falling: <0-100>\n"
            "Sleeping: <0-100>\n"
            "Studying/Reading: <0-100>\n"
            "Using Phone: <0-100>\n"
            "Using Computer: <0-100>\n"
            "Eating: <0-100>\n"
            "Playing: <0-100>\n"
            "Top Activity: <one label>\n"
            "Reason: <short reason>"
        ),
    },



}


def load_local_vlm():
    if not os.path.exists(MODEL_DIR):
        raise RuntimeError(
            f"Local model folder not found: {MODEL_DIR}\n"
            "Download the model first into models/SmolVLM-500M-Instruct"
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

            cv2.imshow("Offline VLM Preset Check", display)
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
            max_new_tokens=80,
            do_sample=False
        )

    generated_text = processor.batch_decode(output_ids, skip_special_tokens=True)[0]

    if "Assistant:" in generated_text:
        generated_text = generated_text.split("Assistant:", 1)[-1].strip()

    return generated_text.strip()


def choose_preset():
    print("\nChoose a preset check:")
    for key, item in PRESET_QUESTIONS.items():
        print(f"{key}. {item['label']}")

    while True:
        choice = input("\nEnter number (1-5): ").strip()
        if choice in PRESET_QUESTIONS:
            return choice
        print("[WARN] Invalid choice. Please enter 1, 2, 3, 4, or 5.")


def main():
    processor, model, device = load_local_vlm()
    print("[OK] Offline VLM preset checker ready.")

    while True:
        choice = choose_preset()
        selected = PRESET_QUESTIONS[choice]

        print(f"\n[INFO] Selected: {selected['label']}")

        frame = capture_frame()

        if frame is None:
            again = input("\nNo scene analysed. Analyse another scene? (y/n): ").strip().lower()
            if again != "y":
                break
            continue

        print("[INFO] Running local VLM inference...")

        try:
            answer = ask_local_vlm(processor, model, device, frame, selected["question"])
        except Exception as e:
            print(f"[ERROR] Local VLM failed: {e}")
            again = input("\nAnalyse another scene? (y/n): ").strip().lower()
            if again != "y":
                break
            continue

        print("\n===== OFFLINE VLM RESULT =====")
        print(f"Check:  {selected['label']}")
        print(f"Answer: {answer}")
        print("================================")

        again = input("\nAnalyse another scene? (y/n): ").strip().lower()
        if again != "y":
            break

    print("[DONE] Exiting.")


if __name__ == "__main__":
    main()
