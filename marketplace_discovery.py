from marketplace_connectors.alibaba import discover_alibaba_products


# --------------------------------------------------
# Available marketplaces
# --------------------------------------------------

SUPPORTED_MARKETPLACES = [
    "Alibaba",
]


# --------------------------------------------------
# Discover products
# --------------------------------------------------

def discover_products(
    marketplace,
    keyword,
    limit=20,
):

    marketplace = str(
        marketplace or ""
    ).strip()

    keyword = str(
        keyword or ""
    ).strip()


    if not keyword:

        raise ValueError(
            "Enter a product keyword."
        )


    if marketplace not in SUPPORTED_MARKETPLACES:

        raise ValueError(
            f"Marketplace connector not available: "
            f"{marketplace}"
        )


    # --------------------------------------------------
    # Alibaba live discovery
    # --------------------------------------------------

    if marketplace == "Alibaba":

        return discover_alibaba_products(
            keyword=keyword,
            max_results=limit,
        )


    return []
