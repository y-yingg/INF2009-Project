import os
import cv2
import base64
from openai import OpenAI

OPENAI_MODEL = "gpt-4.1-mini"

def encode_frame_to_data_url(frame):
    ok, buffer = cv2.imencode(".jpg", frame)
    if not ok:
        raise RuntimeError("Failed to encode image.")
    image_b64 = base64.b64encode(buffer.tobytes()).decode("utf-8")
    return f"data:image/jpeg;base64,{image_b64}"

def ask_vlm(user_question, frame):
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY is not set in this terminal session.")

    client = OpenAI()
    image_data_url = encode_frame_to_data_url(frame)

    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {
                "role": "developer",
                "content": (
                    "You are a vision assistant for a home robot. "
                    "Answer the user's question based only on the image. "
                    "Be concise and practical. "
                    "If the image is unclear, say that it is unclear instead of guessing."
                ),
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": user_question
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": image_data_url,
                            "detail": "low"
                        }
                    }
                ]
            }
        ],
        temperature=0.2,
    )

    return response.choices[0].message.content.strip()

def capture_scene():
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

            cv2.imshow("VLM Question Check", display)
            key = cv2.waitKey(1) & 0xFF

            if key == ord(" "):
                print("[INFO] Captured frame.")
                return frame

            if key == ord("q"):
                return None
    finally:
        cap.release()
        cv2.destroyAllWindows()

def main():
    print("[OK] VLM question checker ready.")

    while True:
        user_question = input(
            "\nEnter your question for the scene\n"
            "(example: check if the person is reading):\n> "
        ).strip()

        if not user_question:
            print("[WARN] Question cannot be empty.")
            continue

        frame = capture_scene()

        if frame is None:
            again = input("\nNo scene analysed. Analyse another scene? (y/n): ").strip().lower()
            if again != "y":
                break
            continue

        print("[INFO] Sending image and question to VLM...")

        try:
            answer = ask_vlm(user_question, frame)
        except Exception as e:
            print(f"[ERROR] VLM request failed: {e}")
            again = input("\nAnalyse another scene? (y/n): ").strip().lower()
            if again != "y":
                break
            continue

        print("\n===== VLM ANSWER =====")
        print(f"Question: {user_question}")
        print(f"Answer: {answer}")
        print("======================")

        again = input("\nAnalyse another scene? (y/n): ").strip().lower()
        if again != "y":
            break

    print("[DONE] Exiting.")

if __name__ == "__main__":
    main()
