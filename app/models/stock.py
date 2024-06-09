from pydantic import BaseModel

class DownloadRequest(BaseModel):
    folder_name: str
