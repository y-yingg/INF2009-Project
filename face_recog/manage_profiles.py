import json
import os

PROFILES_PATH = "profiles.json"

DEFAULT_PROFILES = {
    "Taylor Swift": {
        "risk": "High",
        "style": "Gentle",
        "robot_response": "Escalate quickly if distress"
    },
    "Michael Jordan": {
        "risk": "Medium",
        "style": "Normal",
        "robot_response": "Ask what help is needed"
    },
    "Tom Cruise": {
        "risk": "Low",
        "style": "Playful",
        "robot_response": "Observe first before escalating"
    },
    "Unknown": {
        "risk": "Unknown",
        "style": "Cautious",
        "robot_response": "Do not personalise yet"
    }
}

def load_profiles():
    if not os.path.exists(PROFILES_PATH):
        with open(PROFILES_PATH, "w") as f:
            json.dump(DEFAULT_PROFILES, f, indent=2)
        return DEFAULT_PROFILES.copy()

    with open(PROFILES_PATH, "r") as f:
        return json.load(f)

def save_profiles(profiles):
    with open(PROFILES_PATH, "w") as f:
        json.dump(profiles, f, indent=2)

def list_profiles(profiles):
    print("\nCurrent profiles:")
    for name, info in profiles.items():
        print(f"- {name}: risk={info['risk']}, style={info['style']}, response={info['robot_response']}")

def add_or_update_profile(profiles):
    print("\nAdd / Update Profile")
    name = input("Name: ").strip()
    if not name:
        print("[WARN] Name cannot be empty.")
        return

    risk = input("Risk level (e.g. High / Medium / Low): ").strip() or "Unknown"
    style = input("Style (e.g. Gentle / Playful / Normal): ").strip() or "Unknown"
    robot_response = input("Robot response: ").strip() or "No response defined"

    profiles[name] = {
        "risk": risk,
        "style": style,
        "robot_response": robot_response
    }

    save_profiles(profiles)
    print(f"[OK] Profile saved for {name}.")

def delete_profile(profiles):
    print("\nDelete Profile")
    name = input("Enter name to delete: ").strip()

    if name == "Unknown":
        print("[WARN] 'Unknown' should not be deleted.")
        return

    if name in profiles:
        del profiles[name]
        save_profiles(profiles)
        print(f"[OK] Deleted profile: {name}")
    else:
        print("[WARN] Profile not found.")

def main():
    profiles = load_profiles()

    while True:
        print("\n=== Profile Manager ===")
        print("1. List profiles")
        print("2. Add / update profile")
        print("3. Delete profile")
        print("4. Exit")

        choice = input("Choose an option: ").strip()

        if choice == "1":
            list_profiles(profiles)
        elif choice == "2":
            add_or_update_profile(profiles)
            profiles = load_profiles()
        elif choice == "3":
            delete_profile(profiles)
            profiles = load_profiles()
        elif choice == "4":
            print("[DONE] Exiting profile manager.")
            break
        else:
            print("[WARN] Invalid option.")

if __name__ == "__main__":
    main()