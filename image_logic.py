import io
import pickle
import os, json
import numpy as np
from collections import defaultdict
from PIL import Image
import pytesseract
import cv2
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build


# Tesseract path
# pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


# Load Google credentials
# with open('token.pickle', 'rb') as f:
#     creds = pickle.load(f)
# drive_service = build('drive', 'v3', credentials=creds)

creds_info = json.loads(os.environ['GOOGLE_CREDS_JSON'])
creds = Credentials.from_service_account_info(creds_info)

drive_service = build('drive', 'v3', credentials=creds)

def list_image_files(folder_id):
    q = f"'{folder_id}' in parents and mimeType contains 'image/' and trashed = false"
    res = drive_service.files().list(q=q, fields="files(id,name)").execute()
    return res.get('files', [])

def download_image_bytes(file_id):
    try:
        req = drive_service.files().get_media(fileId=file_id)
        buf = io.BytesIO()
        downloader = MediaIoBaseDownload(buf, req)
        done = False
        while not done:
            _, done = downloader.next_chunk()
        return buf.getvalue()
    except Exception as e:
        print("Download failed:", e)
        return None

def crop_with_polygon(image_bytes, quad):
    try:
        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        arr = np.array(img)
        pts = np.array(quad, dtype=np.float32)
        # order and transform
        rect = np.zeros((4,2), dtype="float32")
        s = pts.sum(axis=1)
        rect[0], rect[2] = pts[np.argmin(s)], pts[np.argmax(s)]
        d = np.diff(pts, axis=1)
        rect[1], rect[3] = pts[np.argmin(d)], pts[np.argmax(d)]
        (tl, tr, br, bl) = rect
        wA = np.linalg.norm(br - bl)
        wB = np.linalg.norm(tr - tl)
        hA = np.linalg.norm(tr - br)
        hB = np.linalg.norm(tl - bl)
        maxW, maxH = int(max(wA,wB)), int(max(hA,hB))
        dst = np.array([[0,0],[maxW-1,0],[maxW-1,maxH-1],[0,maxH-1]], dtype="float32")
        M = cv2.getPerspectiveTransform(rect, dst)
        warp = cv2.warpPerspective(arr, M, (maxW, maxH))
        return Image.fromarray(warp)
    except Exception as e:
        print("Crop failed:", e)
        return None

def extract_text(img):
    try:
        return pytesseract.image_to_string(img).strip()
    except:
        return ""

def extract_unique_part(text):
    if "to" in text:
        return text.split("to")[-1].strip()
    return None

def find_duplicates_by_message_part(folder_id, coords):
    files = list_image_files(folder_id)
    dups = defaultdict(list)

    for idx, f in enumerate(files):
        data = download_image_bytes(f['id'])
        if not data: continue
        cropped = crop_with_polygon(data, coords)
        if not cropped: continue

        # For debugging, save only the first crop
        # if idx == 0:
        #     os.makedirs("cropped_output", exist_ok=True)
        #     cropped.save(os.path.join("cropped_output", "preview_"+f['name']))
        txt = extract_text(cropped)
        part = extract_unique_part(txt)
        if part:
            dups[part].append(f['name'])

    return {k:v for k,v in dups.items() if len(v)>1}
