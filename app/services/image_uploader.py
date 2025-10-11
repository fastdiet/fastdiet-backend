import mimetypes
from uuid import uuid4
from urllib.parse import urlparse
from datetime import timedelta
import logging

import google.auth
from google.auth.transport.requests import Request
from google.api_core import exceptions as gcs_exceptions
from google.cloud import storage
from app.core.config import Settings

logger = logging.getLogger(__name__)


class ImageUploaderService:
    def __init__(self, settings: Settings):
        try:
            if getattr(settings, "google_image_uploader_credentials", None):
                self.storage_client = storage.Client.from_service_account_json(
                    settings.google_image_uploader_credentials
                )
            else:
                self.storage_client = storage.Client()
                
            self.service_account_email = f"image-uploader@{settings.gcp_project_id}.iam.gserviceaccount.com"
            self.bucket_name = settings.gcs_bucket_name
            self.bucket = self.storage_client.bucket(self.bucket_name)
            
        except Exception as e:
            logger.critical(f"Failed to initialize Google Cloud Storage client: {e}")
            raise RuntimeError("Could not connect to GCS. Please check credentials.")

    def generate_upload_url(self, file_name: str, user_id: int) -> dict | None:
        """ Generates a v4 signed URL for uploading a file. """
        try:
            try:
                file_extension = file_name.split('.')[-1]
            except IndexError:
                logger.warning(f"Invalid file name for user {user_id}: No extension found.")
                return None

            content_type, _ = mimetypes.guess_type(file_name)
            if not content_type:
                content_type = 'application/octet-stream'

            unique_object_name = f"user_{user_id}/recipes/{uuid4()}.{file_extension}"
            blob = self.bucket.blob(unique_object_name)

            credentials, project = google.auth.default()
            request = Request()
            try:
                credentials.refresh(request)
            except Exception:
                logger.exception("Failed to refresh ADC credentials (cannot obtain access token).")
                return None

            access_token = getattr(credentials, "token", None)
            if not access_token:
                logger.error("No access token obtained after credentials.refresh(); cannot sign URL.")
                return None

            signed_url = blob.generate_signed_url(
                version="v4",
                expiration=timedelta(minutes=15),
                method="PUT",
                content_type=content_type,
                service_account_email=self.service_account_email,
                access_token=access_token,
            )
            

            return {
                "signed_url": signed_url,
                "public_url": blob.public_url,
                "content_type": content_type,
            }
        except gcs_exceptions.GoogleAPICallError as e:
            logger.error(f"GCS API Error during upload URL generation for user {user_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error generating upload URL for user {user_id}: {e}", exc_info=True)
            return None
        
    def delete_image(self, public_url: str) -> bool:
        """Deletes an image from GCS using its public URL."""
        if not public_url:
            return False

        try:
            path = urlparse(public_url).path
            object_name = path.replace(f"/{self.bucket_name}/", "", 1)
            blob = self.bucket.blob(object_name)
            blob.delete()
            logger.info(f"Deleted image {object_name} from GCS successfully.")
            return True
        except gcs_exceptions.NotFound:
            logger.warning(f"Tried to delete non-existent image in GCS: {public_url}")
            return False
        except Exception as e:
            logger.error(f"Failed to delete image {public_url} from GCS: {e}")
            return False
