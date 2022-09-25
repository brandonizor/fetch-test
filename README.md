# Fetch Notes

*For this exercise, I'll be using a Postgres database as the data store, as well as Python/Pandas/Psycopg2 to import JSON data, do basic data transformations to adhere to the data model, and import data to the DB.*

## Running Instructions

1. Create db with `docker-compose up -d` 
2. Import data with `python3 import_data.py`
3. Data will be populated in the database named `fetch_test`

---

## Initial observations

- data is not always denormalized (which might be ideal for performance, but that should be a later optimization if it's truly necessary)

  - `brands` contains the category, which could likely be provided by categoryCode referencing a `categories` table
  - some of the data within `rewardsReceiptItems` should also exist within a separate table that represents store-agnostic and receipt-agnostic product data.

- There are three clear tables required from the outset: `receipts`, `users`, and `brandBarcodes`. 

  1. receipts: populated from `receipts.json`; every receipt scanned with receipt-level information
  2. users: populated from `users.json`; information for each user that scans a receipt
  3. brandBarcodes: populated from `brands.json`; information for a product sold by a brand. This table has been renamed to better reflect the data held within, since each record reflects a single barcode within a brand

- We also need a table to store the individual records within `receipts.rewardsReceiptItemList`, so we'll create the table `rewardsReceiptItems` as well, to represent each line item of a receipt. 

  - Ideally each record within `rewardsReceiptItems` will be given a unique ID as its primary key, but it's not necessary for this exercise
  - To help normalize the data a bit, we can remove the `rewardsReceiptItemList` array and rely on the foreign key reference within `rewardsReceiptItems.receiptId` to associate specific line items with their corresponding receipt

- While we don't have exact schemas in the provided data, we can infer the some other tables, with a loose understanding of their contents:

  - categories: contains category-level information
  - cpgs: contains CPG/CPG collection information
  - brands: contains brand-level information
  - rewardsProductPartners: contents not clear, but it's referenced


  ## Stakeholder Question

  - Which brand has the most *spend* among users who were created within the past 6 months?

    ```sql
    select
    	b.name,
    	sum(rri.finalPrice)
    from rewardsReceiptItems rri
    join brandBarcodes b on b.brandCode = rri.brandCode
    join receipts r on r.id = rri.receiptId
    join users u on u.id = r.userId
    	and u.createddate between now() - interval '6 months' and now()
    group by 1
    order by 2 desc;
    ```


  ## Data Quality

  - Duplicate users in users.json
  - Some barcodes can belong to multiple rewards groups (`075925306254` and `021000045129` for example)
  - There are numerous receipts where the same barcode had duplicate entries rather than having multiple of the same product combined within the `quantitypurchased` field. As a result of this duplication, the receipt records can be unnecessarily bloated.

  ```sql
  select receiptid, barcode, count(*) from rewardsreceiptitems
  where quantitypurchased = 1
  and barcode is not null
  group by 1,2
  having count(*) > 1
  order by 3 desc;
  ```

  ## Stakeholder Communication

  @Stakeholders Hello! I've reviewed receipt, brand, and user data and would like to discuss the overall state of the data ingestion as well as a few questions that emerged as I was doing an initial pass through it.

  ### Questions

  1. What exactly is the need for `rewardsReceiptItems.partnerItemId`? If this is a serial id that references a particular line item of a receipt, it may make sense to leverage this value plus `receipts.id` to generate a unique UUID to use as a primary key within `rewardsReceiptItems` for each record.
  2. What is the difference between `rewardsReceiptItems.pointsPayerId` and `rewardsReceiptItems.rewardsProductPartnerId`? They appear to be duplicate fields for most receipt items.

  ### Data Quality Issues

  1. The `users.json` file has numerous duplicate records. The file has 495 entries, but only 212 distinct users. Is this data supposed to be deduplicated, or are duplicates to be expected?
  2. There are numerous receipts where the same barcode had duplicate entries rather than having multiple of the same product combined within the `quantitypurchased` field. As a result of this duplication, the receipt records can be unnecessarily bloated. 
  3. I noticed that some barcodes can belong to multiple rewards groups. For instance,`075925306254` can either correspond to `KRAFT NATURAL CHEESE - SHREDDED` or `SARGENTO NATURAL SHREDDED CHEESE 6OZ OR LARGER` depending on the receipt in question. Checking the brand barcode data, these correspond to two different CPGs. Are we able to determine the correct reward group for these barcodes so they can be associated with the correct CPGs?

  ### Resolving Data Quality Issues

  1. We need to understand what assumptions we should be able to make about incoming data. For example, should we be able to assume user data/receipt line itmes are deduplicated, or is that something that we will need to own resolving prior to importing this data?
  2. Regarding point 3 from above, do we need to audit our associations between brands and barcodes? Ideally, we'd be able to ensure uniqueness of barcodes on that table.

  ### Optimizing Data Assets

  I've loaded every field that was included in each of the provided files, but some of them may be extraneous. What specific use cases do we need to address from this data? Is there an list of fields that analysts already need for reporting so we can reduce clutter within the output tables? On a related note, are there any indexes we could create to improve query performance for commonly utilized fields/operations?

  ### Performance/Scaling Concerns

  Pandas stores data in memory rather than on disk, which means it can run into problems with large datasets. There are ways to optimize for memory utilization, such as by breaking apart input data into chunks, but if the scale of data continues to grow, other solutions like Spark might be more appropriate. Further, the data store used here is Postgres, which should work fine for most use cases, but does not scale horizontally if that is a potential use case. 

  