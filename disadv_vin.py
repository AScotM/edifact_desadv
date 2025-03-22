import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

def validate_data(data):
    """Validate required fields in DISADV data."""
    required_fields = ["message_ref", "shipment_number", "parties", "items"]
    for field in required_fields:
        if field not in data or not data[field]:
            raise ValueError(f"Missing required field: {field}")
    if not isinstance(data["items"], list) or len(data["items"]) == 0:
        raise ValueError("DISADV must contain at least one item.")
    logging.info("Data validation passed.")

def generate_disadv(data, filename="disadv.edi"):
    """Generate an EDIFACT DISADV message and save to a file."""
    try:
        validate_data(data)
    except ValueError as e:
        logging.error(e)
        return ""

    logging.info("Generating DISADV message...")
    
    edifact = [
        "UNA:+.? '",  # Service string advice
        f"UNH+{data['message_ref']}+DISADV:D:96A:UN'"
    ]
    
    edifact.append(f"BGM+351+{data['shipment_number']}+9'")  # 351 = Dispatch Advice
    current_date = datetime.datetime.now().strftime('%Y%m%d')
    edifact.append(f"DTM+137:{current_date}:102'")
    
    for party in data['parties']:
        if "qualifier" not in party or "id" not in party:
            logging.warning("Skipping invalid NAD entry: %s", party)
            continue
        edifact.append(f"NAD+{party['qualifier']}+{party['id']}::91'")
    
    if "transport" in data:
        transport = data["transport"]
        if "mode" in transport and "carrier" in transport:
            edifact.append(f"TDT+20+{transport['carrier']}+{transport['mode']}'")
    
    total_weight = 0.0
    for index, item in enumerate(data['items'], start=1):
        if "product_code" not in item or "description" not in item or "quantity" not in item:
            logging.warning("Skipping item due to missing fields: %s", item)
            continue
        edifact.append(f"LIN+{index}++{item['product_code']}:EN'")
        edifact.append(f"IMD+F++:::{item['description']}'")
        edifact.append(f"QTY+12:{item['quantity']}:EA'")
        if "weight" in item:
            edifact.append(f"MEA+WT+AAA:{item['weight']}:KG'")
            total_weight += float(item["weight"]) * int(item["quantity"])
        if "vin" in item:
            edifact.append(f"GIN+BJ+{item['vin']}'")
    
    edifact.append(f"MEA+WT+AAA:{total_weight:.2f}:KG'")
    
    segment_count = len(edifact) - 1
    edifact.append(f"UNT+{segment_count}+{data['message_ref']}'")
    
    edifact_message = "\n".join(edifact)
    with open(filename, "w", encoding="utf-8") as f:
        f.write(edifact_message)
    
    logging.info("DISADV message generated and saved to %s", filename)
    return edifact_message

# Example data
disadv_data = {
    "message_ref": "654321",
    "shipment_number": "SHIP001",
    "parties": [
        {"qualifier": "BY", "id": "123456789"},
        {"qualifier": "SU", "id": "987654321"},
        {"qualifier": "CA", "id": "555555555"}  # Carrier
    ],
    "transport": {"mode": "30", "carrier": "DHL"},
    "items": [
        {"product_code": "ABC123", "description": "Product A", "quantity": "10", "weight": "2.5", "vin": "1HGCM82633A123456"},
        {"product_code": "XYZ456", "description": "Product B", "quantity": "5", "weight": "3.0", "vin": "1HGCM82633A654321"}
    ]
}

# Generate and save DISADV
disadv_message = generate_disadv(disadv_data)
if disadv_message:
    print("\nGenerated DISADV Message:\n")
    print(disadv_message)

