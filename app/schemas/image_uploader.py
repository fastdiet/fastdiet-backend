from pydantic import BaseModel


class UploadURLRequest(BaseModel):
    file_name: str

class UploadURLResponse(BaseModel):
    signed_url: str
    public_url: str
    content_type: str