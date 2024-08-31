from PIL import Image
import numpy as np

class ImageLoader:
    @staticmethod
    def load_image(file_path):
        try:
            with Image.open(file_path) as img:
                img = img.convert('RGB')
                image_array = np.array(img, dtype=np.float32) / 255.0
            return image_array
        except Exception as e:
            print(f"Error loading image: {e}")
            # Si hay un error, devuelve una imagen de fallback
            hdri_width, hdri_height = 512, 256
            image_array = np.zeros((hdri_height, hdri_width, 3), dtype=np.float32)
            for y in range(hdri_height):
                for x in range(hdri_width):
                    image_array[y, x] = (x / hdri_width, y / hdri_height, 0.5)
            return image_array
