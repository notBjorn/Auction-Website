# Auction Website Database Schema (Draft)

## Objective
Model an online auction site in MySQL, normalized to Third Normal Form (3NF).
- Core features: Users can register, list items, start auctions and place bids.

___

## Minimum Requirements

- Users can login/register and manage their profile
- Users (seller) can list an item for sale
- An item is sold via auction transaction with start/end times and a starting price
- Users (buyers) can place bids
  - Highest bid before end of time wins the auction
- All items have a category
  - Do we consider nested categories?
- The site lists auction with current price and the highest bid placed


___

## Entities (Table Fields)
- Users - The buyers/sellers
- Items - The item being sold
- Auctions - The process of buying/selling an item
- Bids - Shows a history of offers on the item
- Categories (optional?) - A classification tree for items
___

## Definitions (Primary and Foreign Key)

**Primary Key (PK) definition**

- A primary key is one (or more) columns in a table that uniquely identify each row.
- Every table in a relational database should have a PK.


**Rules for PKs:** 
- No duplicates (every value must be unique).
- No nulls (every row must have a value).

**Foreign Key (FK) definition**
- A foreign key is a column (or set of columns) in one table that references the primary key of another table.

## Attributes
- Users
  - **(PK)** : User_ID
  - User_Name (UNIQUE)
  - Email_Id (UNIQUE)
  - Password_hash (SECURE VERSION OF PASSWORD)
  - Created_Date (TIMESTAMP)

- Items
  - **(PK)** : Item_ID
  - **(FK)** : Seller_Id (Users.User_ID)
  - (optional) **(FK)** Category_ID (Categories.Category_ID)
  - Item_Name (TITLE)
  - Item_Description
  - Item_Status
  - Created_Data (TIMESTAMP)

- Auctions
  - **(PK)** : Auction_ID
  - **(FK)** : Item_Id (Items.Item_ID)
  - Start_Price
  - Start_Time
  - End_Time
  - Item_Status (Active/Inactive) ?
  - Current_Highest_Bid = MAX(Bids Amount)

- Bids
  - **(PK)** : Bids_ID
  - **(FK)** : Auction_ID (Auctions.Auctions_ID)
  - **(FK)** : Buyer_ID (Users.User_ID)
  - Bid_Amount
  - Bid_Time

- Categories
  - **(PK)** : Category_ID
  - **(FK)** : Parent_Category_ID (points back to self)
  - Category_Name

___

## Open Questions & Next Steps

- How do we track auction status? 
- Do we include Categories? Any other optional functionality?
- Team agreement on final list
- Create diagram (dbdiagram.io) - Link with Git (Rishav has master)
- Write the schema.sql with tables and variable types indicated
- Create test database
