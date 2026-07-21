"""Abstract marketplace product adapter for HYDRA.

A marketplace adapter converts a product URL into a HYDRA Product Intelligence
Record (see ``data/schemas/product_intelligence.schema.json``). Concrete
adapters — Coupang today, and AliExpress, Amazon, Rakuten, Temu in the future —
implement the four steps defined here, so new marketplaces can be added without
changing the core pipeline.

The record produced by :meth:`ProductAdapter.to_product_intelligence` is the
single contract every downstream engine consumes; adapters never redefine it.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class ProductAdapter(ABC):
    """Base interface for all marketplace adapters.

    Every marketplace adapter must implement :meth:`validate`, :meth:`load`,
    :meth:`extract`, and :meth:`to_product_intelligence`. The :meth:`analyze`
    template method runs them in order and returns a Product Intelligence
    Record.
    """

    #: Human-readable marketplace name; concrete adapters set this.
    marketplace: str = ""

    @abstractmethod
    def validate(self, url: str) -> bool:
        """Return ``True`` if ``url`` is a valid product URL for this marketplace."""
        raise NotImplementedError

    @abstractmethod
    def load(self, url: str) -> Any:
        """Load the raw product source for ``url`` and return it.

        Concrete adapters may cache the loaded source on the instance so that
        :meth:`extract` can read it.
        """
        raise NotImplementedError

    @abstractmethod
    def extract(self) -> dict:
        """Extract structured fields from the loaded source and return them."""
        raise NotImplementedError

    @abstractmethod
    def to_product_intelligence(self) -> dict:
        """Map the extracted fields to a Product Intelligence Record dict.

        The returned dict must validate against
        ``data/schemas/product_intelligence.schema.json``.
        """
        raise NotImplementedError

    def analyze(self, url: str) -> dict:
        """Run the adapter end to end for ``url``.

        Orchestrates ``validate -> load -> extract -> to_product_intelligence``.
        Raises :class:`ValueError` if ``url`` is not valid for this marketplace.
        """
        if not self.validate(url):
            raise ValueError(f"Invalid {self.marketplace or 'product'} URL: {url}")
        self.load(url)
        self.extract()
        return self.to_product_intelligence()
