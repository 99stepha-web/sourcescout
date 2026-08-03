"""
SourceScout Research Agent

Pipeline

Alimama
    ↓
Playwright
    ↓
Parser
    ↓
SQLite
    ↓
Claude AI
    ↓
Content
    ↓
Video
    ↓
Publisher
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from affiliate.alimama.search import AlimamaSearch
from affiliate.alimama.parser import AlimamaParser

from analysis_service import analyze_and_save_product
from content_service import generate_and_save_content
from agents.video_agent import VideoAgent


class ResearchAgent:

    def __init__(self, db: Session):

        self.db = db

        self.search = AlimamaSearch()

        self.parser = AlimamaParser()

        self.video = VideoAgent(db)

    def research(self, keyword: str):

        print(f"\nSearching: {keyword}")

        # Open Alimama and return the Playwright page
        page = self.search.search(keyword)

        # Extract products directly from the page
        products = self.parser.parse(page)

        print(f"\nParsed {len(products)} products")

        if not products:
            print("No products parsed.")
            return []

        # --------------------------------------------------
        # Temporary stop point
        #
        # We have not yet connected:
        #   parser -> Product model
        #   Product model -> SQLite
        #
        # The next step is to return parsed products and
        # verify extraction before database integration.
        # --------------------------------------------------

        return products

        # ==================================================
        # Phase 2 (Enable after parser returns Product objects)
        # ==================================================

        for product in products:

            self.db.add(product)

        self.db.commit()

        for product in products:

            analyze_and_save_product(
                self.db,
                product,
            )

            generate_and_save_content(
                self.db,
                product,
            )

            self.video.find_review_video(product)

        return products
