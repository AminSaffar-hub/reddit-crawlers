import abc

from models.data_models import Author, Media, Post


class BaseStorageHandler(abc.ABC):

    @abc.abstractmethod
    def setup_bucket(self) -> None:
        """Setup the bucket for the storage"""
        raise NotImplementedError("Method not implemented")

    @abc.abstractmethod
    def store_author(self, author: Author) -> None:
        """Store the author in the bucket"""
        raise NotImplementedError("Method not implemented")

    @abc.abstractmethod
    def store_post(self, post: Post) -> None:
        """Store the post in the bucket"""
        raise NotImplementedError("Method not implemented")

    @abc.abstractmethod
    def store_media(self, media: Media) -> None:
        """Store the media in the bucket"""
        raise NotImplementedError("Method not implemented")
