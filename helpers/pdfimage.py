from io import BytesIO

import cv2
import numpy as np
import pdf2image
import streamlit as st
from pdf2image.exceptions import PDFInfoNotInstalledError
from pdf2image.exceptions import PDFPageCountError
from pdf2image.exceptions import PDFPopplerTimeoutError
from pdf2image.exceptions import PDFSyntaxError


@st.cache_data(show_spinner=False)
def pdftoimage(pdf_file: BytesIO, page: int = 1) -> tuple[np.ndarray, str]:
    image, error = None, None
    try:
        image = convert(pdf_file=pdf_file, page=page)
        if image is not None:
            image = np.array(image)  # convert image to numpy array
            image = img2opencv2(image)
        else:
            error = "Invalid PDF page selected."
    except PDFInfoNotInstalledError:
        error = "PDFInfoNotInstalledError: PDFInfo is not installed?"
    except PDFPageCountError:
        error = "PDFPageCountError: Could not determine number of pages in PDF."
    except PDFSyntaxError:
        error = "PDFSyntaxError: PDF is damaged/corrupted?"
    except PDFPopplerTimeoutError:
        error = "PDFPopplerTimeoutError: PDF conversion timed out."
    except Exception as e:
        error = str(e)
    return (image, error)


@st.cache_data(show_spinner=False)
def convert(pdf_file: BytesIO, page: int = 1) -> np.ndarray:
    images = pdf2image.convert_from_bytes(
        pdf_file=pdf_file.read(),
        dpi=300,
        single_file=True,
        output_file=None,
        output_folder=None,
        timeout=20,
        first_page=page,
    )
    return images[0] if images else None


# convert image to opencv image
@st.cache_data(show_spinner=False)
def img2opencv2(pil_image: np.ndarray) -> np.ndarray:
    return cv2.cvtColor(pil_image, cv2.COLOR_RGB2BGR)


# opencv preprocessing grayscale
@st.cache_data(show_spinner=False)
def grayscale(img: np.ndarray) -> np.ndarray:
    return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)


if __name__ == "__main__":
    """Just to test the functions in this file"""
    st.title("pdf2image 📝")
    uploaded_file = st.file_uploader("Upload PDF", type=["pdf"])
    if uploaded_file is not None:
        # streamlit number input
        page = st.number_input("Page", min_value=1, max_value=100, value=1, step=1)
        cv2image = pdftoimage(uploaded_file, page=page)
        if cv2image is not None:
            cv2image = np.array(cv2image)  # convert image to numpy array
            cv2image = img2opencv2(cv2image)
            # rotate image with streamlit slider and opencv
            angle90 = st.slider(
                "Rotate rectangular [Degree]",
                min_value=0,
                max_value=270,
                value=0,
                step=90,
            )
            # cv2image = cv2.rotate(cv2image, angle90)
            angle = st.slider(
                "Rotate freely [Degree]", min_value=-180, max_value=180, value=0, step=1
            )
            height, width = cv2image.shape[:2]
            center = (width / 2, height / 2)
            rotate_matrix = cv2.getRotationMatrix2D(center=center, angle=angle, scale=1)
            cv2image = cv2.warpAffine(
                src=cv2image,
                M=rotate_matrix,
                dsize=(width, height),
                borderMode=cv2.BORDER_CONSTANT,
                borderValue=(255, 255, 255),
            )
            height, width = cv2image.shape[:2]
            cropleft = st.slider(
                "Crop from Left [Pixel]",
                min_value=0,
                max_value=width - 1,
                value=0,
                step=1,
            )
            cropright = st.slider(
                "Crop from Right [Pixel]",
                min_value=0,
                max_value=width - 1,
                value=0,
                step=1,
            )
            cropright = width - cropright
            croptop = st.slider(
                "Crop from Top [Pixel]",
                min_value=0,
                max_value=height - 1,
                value=0,
                step=1,
            )
            cropbottom = st.slider(
                "Crop from Bottom [Pixel]",
                min_value=0,
                max_value=height - 1,
                value=0,
                step=1,
            )
            cropbottom = height - cropbottom
            # check for invalid crop values
            if cropleft >= cropright or croptop >= cropbottom:
                st.warning("Invalid crop values")
                st.stop()
            else:
                cv2image = cv2image[croptop:cropbottom, cropleft:cropright]
                cv2image = grayscale(cv2image)
                st.image(cv2image, width=600)
