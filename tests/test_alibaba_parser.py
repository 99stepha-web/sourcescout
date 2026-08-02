from connectors.alibaba_parser import AlibabaParser


def test_parse_basic_html():
    html = """
    <html>
      <head>
        <title>Premium Bluetooth Speaker</title>
      </head>
      <body></body>
    </html>
    """

    parser = AlibabaParser()
    product = parser.parse(html)

    assert product.marketplace == "alibaba"
    assert product.raw_data["product_title"] == "Premium Bluetooth Speaker"
    assert product.raw_data["product_id"] == ""
    assert product.raw_data["price"] == 0.0
    assert product.raw_data["currency"] == "USD"
    assert product.raw_data["country"] == "China"
