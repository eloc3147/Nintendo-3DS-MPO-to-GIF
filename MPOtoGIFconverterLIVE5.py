import os
import sys
import tkinter as tk
from PIL import Image, ImageSequence, ImageTk
from datetime import datetime

# === CONFIGURATION ===
input_folder = r"C:\Users\1\Downloads\3DS-imagedump\All Jumbled Together\101NIN03"
output_folder = r"C:\Users\1\Downloads\3DS-imagedump\ManualEdits"

# === GLOBAL STATE ===
overlap = 0
frame_duration = 175
preview_interval = 0.05
crop = {"l": 0, "t": 0, "r": 0, "b": 0}
toggle = True
stop_preview = False
skip_file = False
exit_script = False
base_filename = ""  # Will be set dynamically

# === IMAGE PROCESSING ===
def process_images(mpo_path, overlap):
    mpo = Image.open(mpo_path)
    frames = [frame.copy() for frame in ImageSequence.Iterator(mpo)]
    if len(frames) < 2:
        raise ValueError("MPO file must contain at least two frames.")

    width, height = frames[0].size
    left_start = -overlap
    right_start = overlap

    left_box = (left_start, 0, width + left_start, height)
    right_box = (right_start, 0, width + right_start, height)

    left_image = frames[0].crop(left_box)
    right_image = frames[1].crop(right_box)

    crop_l, crop_t, crop_r, crop_b = crop["l"], crop["t"], crop["r"], crop["b"]
    new_width = left_image.width - crop_l - crop_r
    new_height = left_image.height - crop_t - crop_b

    left_image = left_image.crop((crop_l, crop_t, crop_l + new_width, crop_t + new_height))
    right_image = right_image.crop((crop_l, crop_t, crop_l + new_width, crop_t + new_height))

    return left_image, right_image

# === GIF CREATION ===
def create_gif(images, output_path, duration):
    images[0].save(
        output_path,
        save_all=True,
        append_images=images[1:],
        duration=duration,
        loop=0
    )
    print(f"🎞️ GIF saved to: {output_path}")

# === PREVIEW WINDOW ===
def show_preview(mpo_path):
    global left_img, right_img, toggle, stop_preview

    left_img, right_img = process_images(mpo_path, overlap)
    stop_preview = False
    toggle = True

    window = tk.Tk()
    window.title(f"Previewing: {os.path.basename(mpo_path)}")
    canvas = tk.Canvas(window, width=left_img.width, height=left_img.height)
    canvas.pack()

    photo = ImageTk.PhotoImage(left_img)
    canvas.image = photo
    image_container = canvas.create_image(0, 0, anchor=tk.NW, image=photo)

    def update():
        global toggle
        if stop_preview:
            window.destroy()
            return
        img = left_img if toggle else right_img
        photo = ImageTk.PhotoImage(img)
        canvas.image = photo
        canvas.itemconfig(image_container, image=photo)
        toggle = not toggle
        window.after(int(preview_interval * 1000), update)

    window.after(int(preview_interval * 1000), update)
    window.mainloop()

# === TERMINAL INPUT ===
def handle_input(mpo_path):
    global overlap, frame_duration, preview_interval, crop
    global left_img, right_img, stop_preview, skip_file, exit_script, base_filename

    while True:
        cmd = input("Enter command ('o<number>', 'f<number>', 'c <side><number>', 'e', 's', or 'exit'): ").strip()

        if cmd.lower() == "exit":
            stop_preview = True
            exit_script = True
            print("🛑 Exiting script...")
            break

        elif cmd.lower() == "s":
            stop_preview = True
            skip_file = True
            print("⏭️ Skipping current MPO...")
            break

        elif cmd.lower() == "e":
            stop_preview = True
            if not os.path.exists(output_folder):
                os.makedirs(output_folder)
            left_img.save(os.path.join(output_folder, f"{base_filename}_left.jpg"))
            right_img.save(os.path.join(output_folder, f"{base_filename}_right.jpg"))
            gif_path = os.path.join(output_folder, f"{base_filename}.gif")
            create_gif([left_img, right_img], gif_path, frame_duration)
            print(f"✅ Exported {base_filename}. Moving to next MPO...\n")
            break

        elif cmd.lower().startswith("o"):
            try:
                overlap = int(cmd[1:])
                left_img, right_img = process_images(mpo_path, overlap)
                print(f"🔁 Updated overlap to {overlap}")
            except:
                print("⚠️ Invalid overlap. Use format: o<number>")

        elif cmd.lower().startswith("f"):
            try:
                frame_duration = int(cmd[1:])
                preview_interval = frame_duration / 1000.0
                print(f"⏱️ Updated frame duration to {frame_duration}ms")
            except:
                print("⚠️ Invalid frame duration. Use format: f<number>")

        elif cmd.lower().startswith("c"):
            try:
                parts = cmd.split()
                side = parts[1][0]
                value = int(parts[1][1:])
                if side in crop:
                    crop[side] = value
                    left_img, right_img = process_images(mpo_path, overlap)
                    print(f"✂️ Cropped {side.upper()} side by {value}px")
                else:
                    raise ValueError
            except:
                print("⚠️ Invalid crop. Use format: c l<number>, c t<number>, etc.")

        else:
            print("⚠️ Unknown command.")

# === MAIN LOOP ===
if __name__ == "__main__":
    mpo_files = sorted([f for f in os.listdir(input_folder) if f.lower().endswith(".mpo")])
    print(f"📂 Found {len(mpo_files)} MPO files.")

    counter = 1

    for mpo_file in mpo_files:
        if exit_script:
            break

        skip_file = False
        mpo_path = os.path.join(input_folder, mpo_file)

        # Get file creation time and format it
        timestamp = datetime.fromtimestamp(os.path.getmtime(mpo_path)).strftime("%Y%m%d_%H%M%S")
        base_filename = f"3DS_{counter:04d}_{timestamp}"

        print(f"\n🔍 Editing: {mpo_file} → Saving as {base_filename}")

        # Reset settings
        overlap = 0
        frame_duration = 175
        preview_interval = 0.05
        crop = {"l": 0, "t": 0, "r": 0, "b": 0}

        import threading
        input_thread = threading.Thread(target=handle_input, args=(mpo_path,), daemon=True)
        input_thread.start()
        show_preview(mpo_path)

        counter += 1
