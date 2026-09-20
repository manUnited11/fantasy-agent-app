import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")

os.makedirs(DATA_DIR, exist_ok=True)

DOC_IDS = {
    "snapshot": "19dzRV44VHm5nVaj5ge8FEXaCGeqRZv7cw60CVKUq9iE",
    "hathat": "103a7PjQr5976ByVOOn3yR4aeoNI3mqABP4XtOTr5T2k",
    "bush": "10Q3y_nmdivTz0T1NECdhN8rFgoNDucGvO5zCITt-Ar4"
}

DOC_EXPORT_URL = "https://docs.google.com/document/d/{doc_id}/export?format=txt"
