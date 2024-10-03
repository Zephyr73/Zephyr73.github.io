import os
import re
from PIL import Image
from datetime import datetime


def get_image_exif_date(image_path):
    try:
        image = Image.open(image_path)
        exif_data = image._getexif()
        if exif_data is not None:
            date_str = exif_data.get(36867)  # DateTimeOriginal
            if date_str:
                return datetime.strptime(date_str, '%Y:%m:%d %H:%M:%S')
    except Exception as e:
        print(f"Error reading EXIF data from {image_path}: {e}")
    return None


def sort_images_by_date(folder_path):
    images_with_dates = []
    for filename in os.listdir(folder_path):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
            image_path = os.path.join(folder_path, filename)
            date = get_image_exif_date(image_path)
            if date:
                images_with_dates.append((image_path, date))
    images_with_dates.sort(key=lambda x: x[1], reverse=True)
    return [image[0] for image in images_with_dates]


def sort_images_by_modification_date(folder_path):
    images_with_dates = []
    for filename in os.listdir(folder_path):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
            image_path = os.path.join(folder_path, filename)
            modification_time = os.path.getmtime(image_path)
            images_with_dates.append((image_path, datetime.fromtimestamp(modification_time)))
    images_with_dates.sort(key=lambda x: x[1], reverse=True)
    return [image[0] for image in images_with_dates]


def rename_images(images):
    new_image_names = []
    for index, image_path in enumerate(images):
        temp_new_name = f"temp_{index + 1}.jpg"
        temp_new_path = os.path.join(os.path.dirname(image_path), temp_new_name)
        try:
            os.rename(image_path, temp_new_path)
            print(f"Temporarily renamed {image_path} to {temp_new_path}")
            new_image_names.append(temp_new_path)  # Keep track of the new names
        except FileNotFoundError:
            print(f"File not found: {image_path}. It may not exist.")
            continue

    for index in range(len(images)):
        temp_new_name = f"temp_{index + 1}.jpg"
        final_new_name = f"{index + 1}.jpg"
        temp_new_path = os.path.join(os.path.dirname(images[index]), temp_new_name)
        final_new_path = os.path.join(os.path.dirname(images[index]), final_new_name)
        try:
            os.rename(temp_new_path, final_new_path)
            print(f"Renamed {temp_new_path} to {final_new_path}")
            new_image_names[index] = final_new_path  # Update to final new name
        except FileNotFoundError:
            print(f"File not found: {temp_new_path}. It may not exist.")
            continue
            
    return new_image_names  # Return the list of new names


def generate_new_columns_html(images, is_ai=False, is_forza=False):
    total_images = len(images)
    columns = 3
    base_images_per_column = total_images // columns
    extra_images = total_images % columns
    new_html = []

    start_index = 0
    for col in range(columns):
        if col == 0:
            new_html.append('<div class="column">')  # No indentation for the first column
        else:
            new_html.append('      <div class="column">')  # 6 spaces indentation for other columns

        if col < extra_images:
            images_in_this_column = base_images_per_column + 1
        else:
            images_in_this_column = base_images_per_column

        images_to_display = images[start_index:start_index + images_in_this_column]
        start_index += images_in_this_column

        for img_path in images_to_display:
            if is_ai:
                new_html.append(
                    f'        <img src="/img/gallery/ai/{os.path.basename(img_path)}" '
                    f'alt="image {os.path.basename(img_path)[:-4]}">'
                )  # AI images source path
            elif is_forza:
                new_html.append(
                    f'        <img src="/img/gallery/forza/{os.path.basename(img_path)}" '
                    f'alt="image {os.path.basename(img_path)[:-4]}">'
                )  # Forza images source path
            else:
                new_html.append(
                    f'        <img src="/img/gallery/photography/{os.path.basename(img_path)}" '
                    f'alt="image {os.path.basename(img_path)[:-4]}">'
                )  # Photography images source path

        new_html.append('      </div>')  # 6 spaces indentation for closing divs

    return '\n'.join(new_html)


def replace_gallery_columns(html_path, new_columns_html, container_class):
    try:
        with open(html_path, 'r', encoding='utf-8') as file:
            content = file.read()

        # Check if the container is for photography or for AI/Forza
        if container_class == "photography-container":
            # Regex for photography container
            updated_content = re.sub(
                rf'(<div class="{container_class}">\s*)(<div class="column">.*?</div>\s*'
                r'<div class="column">.*?</div>\s*<div class="column">.*?</div>\s*)(</div>)',
                rf'\1{new_columns_html}\n    \3',
                content,
                flags=re.DOTALL
            )
        else:
            # Regex for AI/Forza containers (with display:none)
            updated_content = re.sub(
                rf'(<div class="{container_class}" style="display: none;">\s*)(<div class="column">.*?</div>\s*'
                r'<div class="column">.*?</div>\s*<div class="column">.*?</div>\s*)(</div>)',
                rf'\1{new_columns_html}\n    \3',
                content,
                flags=re.DOTALL
            )

        with open(html_path, 'w', encoding='utf-8') as file:
            file.write(updated_content)

        print(f"Updated HTML file at {html_path} with new images in {container_class}.")
    except Exception as e:
        print(f"Error updating HTML file: {e}")



def main(folder_photography, folder_ai, folder_forza, html_path):
    # Process photography images
    photography_images = sort_images_by_date(folder_photography)
    new_photography_images = rename_images(photography_images)  # Get the new image names after renaming
    new_photography_columns_html = generate_new_columns_html(new_photography_images, is_ai=False)
    replace_gallery_columns(html_path, new_photography_columns_html, "photography-container")

    # Process AI images
    ai_images = sort_images_by_modification_date(folder_ai)
    new_ai_images = rename_images(ai_images)  # Get the new image names after renaming
    new_ai_columns_html = generate_new_columns_html(new_ai_images, is_ai=True)  # Pass is_ai=True for AI images
    replace_gallery_columns(html_path, new_ai_columns_html, "ai-container")

    # Process Forza images
    forza_images = sort_images_by_modification_date(folder_forza)
    new_forza_images = rename_images(forza_images)  # Get the new image names after renaming
    new_forza_columns_html = generate_new_columns_html(new_forza_images, is_forza=True)  # Pass is_forza=True for Forza images
    replace_gallery_columns(html_path, new_forza_columns_html, "forza-container")


if __name__ == "__main__":
    folder_photography = r'img\gallery\photography'  # Change this to your photography folder path
    folder_ai = r'img\gallery\ai'  # Change this to your AI folder path
    folder_forza = r'img\gallery\forza'  # Change this to your Forza folder path
    html_path = r'gallery\index.html'  # Change this to your HTML file path
    main(folder_photography, folder_ai, folder_forza, html_path)
