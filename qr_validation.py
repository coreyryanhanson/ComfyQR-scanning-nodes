import numpy as np
from PIL import Image
from pyzbar.pyzbar import decode


class QRReader:
    def __init__(self):
        pass

    FUNCTION = "read_qr"
    CATEGORY = "Comfy-QR"
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("EXTRACTED_TEXT",)

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "library": (["pyzbar",], {"default": "pyzbar"}),
            },
        }
    
    def _pyzbar_read(self, img):
        try:
            decoded_objects = decode(img)
            if decoded_objects:
                return decoded_objects[0].data.decode('utf-8')
            return ""
        except OSError:
            raise OSError("The pyzbar package requires the zbar libraries to be installed to your system. Instructions depending on your OS and can be found here: https://github.com/NaturalHistoryMuseum/pyzbar/")
    
    def _tensor_to_img(self, tensor):
        i = 255. * tensor.cpu().numpy()[0]
        return Image.fromarray(np.clip(i, 0, 255).astype(np.uint8))

    def read_qr(self, image, library):
        img = self._tensor_to_img(image)
        if library == "pyzbar":
            text = self._pyzbar_read(img)
        else:
            raise ValueError("This plugin currently only supports pyzbar.")
        return (text, )

    
class QRValidator:
    def __init__(self):
        self.text = ""

    FUNCTION = "validate_qr"
    CATEGORY = "Comfy-QR"
    RETURN_TYPES = ("IMAGE", "INT",)
    RETURN_NAMES = ("IMAGE", "VALIDATION_CODE",)

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "extracted_text": ("STRING",{"multiline": True, "forceInput":True}),
                "protocol": (["Http", "Https", "None"], {"default": "Https"}),
                "text": ("STRING", {"multiline": True}),
                "passthrough": (["False", "True",], {"default": "False"}),
            },
        }
    
    def update_text(self, protocol, text):
        """This function takes input from a text box and a chosen internet
        protocol and stores a full address within an instance variable.
        Backslashes will invalidate text box input and this acts as a
        workaround to be able to use them when required in QR strings.

        Args:
            protocol: A categorical variable of one of the available internet
                protocols.
            text: The input from the text box.
        """
        if protocol == "Https":
            prefix = "https://"
        elif protocol == "Http":
            prefix = "http://"
        elif protocol == "None":
            prefix = ""
        self.text = prefix + text

    def _create_qr_validation_code(self, extracted_text):
        if not extracted_text:
            return 1
        if extracted_text != self.text:
            return 2
        return 0
    
    def _exception_from_qr_validation_code(self, validation_code, extracted_text):
        if not validation_code:
            return
        if validation_code == 1:
            raise RuntimeError("There is no extracted_text to check.")
        raise RuntimeError(f"extracted_text of {extracted_text} does not match input text of {self.text}")
    
    def validate_qr(self, image, extracted_text, protocol, text, passthrough):
        self.update_text(protocol, text)
        validation_code = self._create_qr_validation_code(extracted_text)
        if passthrough == "False":
            self._exception_from_qr_validation_code(validation_code, extracted_text)
        return (image, validation_code)

    
NODE_CLASS_MAPPINGS = {
                       "comfy-qr-read": QRReader,
                       "comfy-qr-validate": QRValidator,
                       }


NODE_DISPLAY_NAME_MAPPINGS = {
                              "comfy-qr-read": "Read QR Code",
                              "comfy-qr-validate": "Validate QR Code",
                              }
