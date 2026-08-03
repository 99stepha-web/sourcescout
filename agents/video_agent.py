"""
SourceScout Video Agent
"""

from sqlalchemy.orm import Session


class VideoAgent:

    def __init__(
        self,
        db: Session,
    ):
        self.db = db

    def discover(
        self,
        product,
    ):

        print(
            f"Searching review videos for {product.title}"
        )

        return []
