# Auction Website Database Schema (Draft)

## Objective
Model an online auction site in MySQL, normalized to Third Normal Form (3NF).
- Core features: Users can register, list items, start auctions and place bids.

___

## Entities (Table Fields)
- User_Table
- Item_Table
- Auction_Table
- Bids_Table
- TBD?
___

## Attributes
- User_Table
  - User_ID
  - User_Name
  - User_Auctions
  - User_Bids

- Item_Table
  - Item_ID
  - Item_Name
  - Item_Owner -> User_ID
  - Item_Status
  - Item_Description
  -

___

## Open Questions & Next Steps

- How do we track all these categories?
- Finalize Entities and Attributes
- Create diagram (Excalidraw or Mermaid)
- Write the schema.sql
