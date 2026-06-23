"""S3 client — async через aiobotocore. Endpoint совместим с MinIO/Twcstorage."""

from contextlib import asynccontextmanager
from typing import AsyncIterator

from aiobotocore.session import get_session

from src.config import get_settings


@asynccontextmanager
async def s3_client() -> AsyncIterator:
    s = get_settings()
    session = get_session()
    async with session.create_client(
        "s3",
        endpoint_url=s.s3_endpoint_url,
        aws_access_key_id=s.s3_access_key_id,
        aws_secret_access_key=s.s3_secret_access_key,
        region_name=s.s3_region,
    ) as client:
        yield client


async def upload_bytes(*, key: str, data: bytes, content_type: str | None = None) -> None:
    s = get_settings()
    async with s3_client() as client:
        kwargs: dict = {"Bucket": s.s3_bucket_name, "Key": key, "Body": data}
        if content_type:
            kwargs["ContentType"] = content_type
        await client.put_object(**kwargs)


async def download_bytes(key: str) -> bytes:
    s = get_settings()
    async with s3_client() as client:
        resp = await client.get_object(Bucket=s.s3_bucket_name, Key=key)
        async with resp["Body"] as body:
            return await body.read()


async def presigned_get_url(key: str, expires_in: int = 3600) -> str:
    s = get_settings()
    async with s3_client() as client:
        return await client.generate_presigned_url(
            "get_object",
            Params={"Bucket": s.s3_bucket_name, "Key": key},
            ExpiresIn=expires_in,
        )


async def delete_object(key: str) -> None:
    s = get_settings()
    async with s3_client() as client:
        await client.delete_object(Bucket=s.s3_bucket_name, Key=key)
